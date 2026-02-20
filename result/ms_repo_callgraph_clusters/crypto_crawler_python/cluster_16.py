# Cluster 16

# Node: get_cache
# Node: get_balance
def log_last_balances(exchanges_ids, cache, msg_queue):
    timest = get_now_seconds_utc()
    ttl = 'At ts={ts} what we have at cache'.format(ts=timest)
    print_to_console(ttl, LOG_ALL_ERRORS)
    log_to_file(ttl, 'balance.log')
    for idx in exchanges_ids:
        some_balance = cache.get_balance(idx)
        if some_balance is None or timest - some_balance.last_update > BALANCE_EXPIRE_TIMEOUT:
            log_warn_balance_not_updating(some_balance, msg_queue)
        else:
            log_balance_updated(idx, some_balance)

# Node: log_warn_balance_not_updating
# Node: log_balance_updated
def generate_nonce():
    cache = get_cache()
    return cache.get_counter()

# Node: get_counter
def get_next_arbitrage_id():
    cache = get_cache()
    return cache.get_arbitrage_id()

# Node: get_arbitrage_id
def get_updated_balance_arbitrage(cfg, balance_state, local_cache):
    """
    Method is frequently called from numerous thread so in order to decrease load and number of request to exchanges,
    to avoid banning, we use cached version of balance from memory cache.

    :param cfg: type: ArbitrageConfig
    :param balance_state:
    :param local_cache:
    :return: updated balance_state for request exchanges id
    """
    for exchange_id in [cfg.sell_exchange_id, cfg.buy_exchange_id]:
        balance = local_cache.get_balance(exchange_id)
        if balance is not None:
            balance_state.balance_per_exchange[exchange_id] = balance
    return balance_state

# Node: update_balance_by_exchange
def init_balances(exchanges_ids, cache=get_cache()):
    for exchange_id in exchanges_ids:
        update_balance_by_exchange(exchange_id, cache)

def get_huobi_account(key, cache=get_cache()):
    if cache.get_value(HUOBI_ACOUNT_ID) is None:
        huobi_account_id = get_huobi_account_impl(key)
        if huobi_account_id is not None:
            cache.set_value(HUOBI_ACOUNT_ID, huobi_account_id)
        else:
            assert huobi_account_id is not None
    return cache.get_value(HUOBI_ACOUNT_ID)

# Node: get_value
# Node: get_huobi_account_impl
# Node: set_value
def process_expired_order(expired_order, msg_queue, priority_queue, local_cache):
    """
            In order to speedup and simplify expired deal processing following approach implemented.

            Every successfully placed order go into priority queue sorted by time. Earliest - first.
            When time come - it will appear in this method.
            We retrieve open orders and try to find that order there.
            If it still there:
                adjust executed volume
                cancel active order
                retrieve order book and adjust price
                place new order with new volume and price

            FIXME NOTE: poloniex(? other ?) executed volume = 0 and volume != original ?

    :param expired_order:  order retrieved from redis cache
    :param msg_queue: saving to postgres and re-process failed orders
    :param priority_queue: watch queue for expired orders
    :param local_cache: to retrieve balance
    :return:
    """
    err_code, open_orders = get_open_orders_by_exchange(expired_order.exchange_id, expired_order.pair_id)
    if err_code == STATUS.FAILURE:
        log_open_orders_by_exchange_bad_result(expired_order)
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        return
    if not open_orders:
        log_open_orders_is_empty(expired_order)
        return
    log_trace_all_open_orders(open_orders)
    if not executed_volume_updated(open_orders, expired_order):
        log_to_file("Can't update volume for ", EXPIRED_ORDER_PROCESSING_FILE_NAME)
    err_code, response = cancel_by_exchange(expired_order)
    log_trace_cancel_request_result(expired_order, err_code, response)
    if err_code == STATUS.FAILURE:
        log_cant_cancel_deal(expired_order, msg_queue)
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        return
    sleep_for(2)
    ticker = get_ticker(expired_order.exchange_id, expired_order.pair_id)
    if ticker is None:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        log_cant_retrieve_ticker(expired_order, msg_queue)
        return
    min_volume = compute_min_cap_from_ticker(expired_order.pair_id, ticker)
    order_book = get_order_book(expired_order.exchange_id, expired_order.pair_id)
    if order_book is None:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        log_cant_retrieve_order_book(expired_order, msg_queue)
        return
    if is_order_book_expired(EXPIRED_ORDER_PROCESSING_FILE_NAME, order_book, local_cache, msg_queue):
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        return
    orders = order_book.bid if expired_order.trade_type == DEAL_TYPE.SELL else order_book.ask
    expired_order.price = adjust_price_by_order_book(orders, expired_order.volume)
    update_balance_by_exchange(expired_order.exchange_id)
    balance = local_cache.get_balance(expired_order.exchange_id)
    if balance.expired(BALANCE_EXPIRED_THRESHOLD):
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        log_balance_expired(expired_order.exchange_id, BALANCE_EXPIRED_THRESHOLD, balance, msg_queue)
        assert False
    place_order_by_market_rate(expired_order, msg_queue, priority_queue, min_volume, balance, order_book, EXPIRED_ORDER_PROCESSING_FILE_NAME)

# Node: get_open_orders_by_exchange
# Node: log_open_orders_by_exchange_bad_result
# Node: add_order_to_watch_queue
# Node: log_open_orders_is_empty
# Node: log_trace_all_open_orders
# Node: executed_volume_updated
# Node: cancel_by_exchange
# Node: log_trace_cancel_request_result
# Node: log_cant_cancel_deal
# Node: get_ticker
# Node: log_cant_retrieve_ticker
# Node: compute_min_cap_from_ticker
# Node: log_cant_retrieve_order_book
# Node: is_order_book_expired
# Node: adjust_price_by_order_book
# Node: log_balance_expired
# Node: place_order_by_market_rate
def add_orders_to_watch_list(orders_pair, priority_queue):
    if orders_pair is None:
        return
    msg = 'Add order to watch list - {pair}'.format(pair=str(orders_pair))
    log_to_file(msg, 'expire_deal.log')
    if orders_pair.deal_1:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, orders_pair.deal_1)
    if orders_pair.deal_2:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, orders_pair.deal_2)

def search_for_arbitrage(sell_order_book, buy_order_book, threshold, balance_threshold, action_to_perform, balance_state, deal_cap, type_of_deal, worker_pool, msg_queue):
    """
    :param sell_order_book:         order_book from exchange where we are going to SELL
    :param buy_order_book:          order_book from exchange where we are going to BUY
    :param threshold:               difference in price in percent that MAY trigger MUTUAL deal placement
    :param balance_threshold:       for interface compatibility with balance_adjustment method
    :param action_to_perform:       method that will be called in case threshold condition are met
    :param balance_state:           balance across all active exchange for all supported currencies
    :param deal_cap:                dynamically updated minimum volume per currency
    :param type_of_deal:            ARBITRAGE or REVERSE. EXPIRED or FAILED will not be processed here
    :param worker_pool:             gevent based connection pool for speedy deal placement
    :param msg_queue:               redis backed msq queue with notification for Telegram
    :return:
    """
    deal_status = (STATUS.FAILURE, None)
    if not sell_order_book.bid or not buy_order_book.ask:
        return deal_status
    difference = get_change(sell_order_book.bid[FIRST].price, buy_order_book.ask[LAST].price, provide_abs=False)
    if should_print_debug():
        log_arbitrage_heart_beat(sell_order_book, buy_order_book, difference)
    if difference >= threshold:
        min_volume = determine_minimum_volume(sell_order_book, buy_order_book, balance_state)
        min_volume = adjust_minimum_volume_by_trading_cap(deal_cap, min_volume)
        min_volume = adjust_maximum_volume_by_trading_cap(deal_cap, min_volume)
        min_volume = round_volume_by_exchange_rules(sell_order_book.exchange_id, buy_order_book.exchange_id, min_volume, sell_order_book.pair_id)
        if min_volume <= 0:
            log_arbitrage_determined_volume_not_enough(sell_order_book, buy_order_book, msg_queue)
            return deal_status
        sell_price = adjust_price_by_order_book(sell_order_book.bid, min_volume)
        arbitrage_id = get_next_arbitrage_id()
        create_time = get_now_seconds_utc()
        trade_at_first_exchange = Trade(DEAL_TYPE.SELL, sell_order_book.exchange_id, sell_order_book.pair_id, sell_price, min_volume, sell_order_book.timest, create_time, arbitrage_id=arbitrage_id)
        buy_price = adjust_price_by_order_book(buy_order_book.ask, min_volume)
        trade_at_second_exchange = Trade(DEAL_TYPE.BUY, buy_order_book.exchange_id, buy_order_book.pair_id, buy_price, min_volume, buy_order_book.timest, create_time, arbitrage_id=arbitrage_id)
        final_difference = get_change(sell_price, buy_price, provide_abs=False)
        if final_difference <= 0.2:
            log_arbitrage_determined_price_not_enough(sell_price, sell_order_book.bid[FIRST].price, buy_price, buy_order_book.ask[LAST].price, difference, final_difference, sell_order_book.pair_id, msg_queue)
            return deal_status
        trade_pair = TradePair(trade_at_first_exchange, trade_at_second_exchange, sell_order_book.timest, buy_order_book.timest, type_of_deal)
        placement_status = action_to_perform(trade_pair, final_difference, 'history_trades.log', worker_pool, msg_queue)
    return deal_status

# Node: log_arbitrage_heart_beat
# Node: determine_minimum_volume
# Node: adjust_minimum_volume_by_trading_cap
# Node: adjust_maximum_volume_by_trading_cap
# Node: round_volume_by_exchange_rules
# Node: log_arbitrage_determined_volume_not_enough
# Node: get_next_arbitrage_id
# Node: log_arbitrage_determined_price_not_enough
# Node: TradePair
# Node: action_to_perform
def place_order_by_market_rate(expired_order, msg_queue, priority_queue, min_volume, balance, order_book, log_file_name):
    max_volume = determine_maximum_volume_by_balance(expired_order.pair_id, expired_order.trade_type, expired_order.volume, expired_order.price, balance)
    max_volume = round_volume(expired_order.exchange_id, max_volume, expired_order.pair_id)
    if max_volume < min_volume:
        log_too_small_volume(expired_order, max_volume, min_volume, msg_queue)
        return
    expired_order.volume = max_volume
    expired_order.create_time = get_now_seconds_utc()
    msg = 'Replace EXPIRED order with new one - {tt}'.format(tt=expired_order)
    err_code, json_document = init_deal(expired_order, msg)
    log_expired_order_replacement_result(expired_order, json_document, msg_queue)
    if err_code == STATUS.SUCCESS:
        expired_order.execute_time = get_now_seconds_utc()
        expired_order.order_book_time = long(order_book.timest)
        expired_order.order_id = parse_order_id(expired_order.exchange_id, json_document)
        msg_queue.add_order(ORDERS_MSG, expired_order)
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, expired_order)
        log_placing_new_deal(expired_order, msg_queue, log_file_name)
    else:
        log_cant_placing_new_deal(expired_order, msg_queue)
        msg_queue.add_order(FAILED_ORDERS_MSG, expired_order, log_file_name)

# Node: determine_maximum_volume_by_balance
# Node: round_volume
# Node: log_too_small_volume
# Node: init_deal
# Node: log_expired_order_replacement_result
# Node: parse_order_id
# Node: add_order
# Node: log_placing_new_deal
# Node: log_cant_placing_new_deal
