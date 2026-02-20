# Cluster 22

def get_currency_pair_name_by_exchange_id(pair_id, exchange_id):
    return {EXCHANGE.BITTREX: get_currency_pair_to_bittrex(pair_id), EXCHANGE.KRAKEN: get_currency_pair_to_kraken(pair_id), EXCHANGE.POLONIEX: get_currency_pair_to_poloniex(pair_id), EXCHANGE.BINANCE: get_currency_pair_to_binance(pair_id), EXCHANGE.HUOBI: get_currency_pair_to_huobi(pair_id)}[exchange_id]

# Node: get_currency_pair_to_bittrex
# Node: get_currency_pair_to_kraken
# Node: get_currency_pair_to_poloniex
# Node: get_currency_pair_to_binance
# Node: get_currency_pair_to_huobi
# Node: truncate_float
class SubscriptionPoloniex:

    def __init__(self, pair_id, on_update=default_on_public, base_url=POLONIEX_WEBSCOKET_URL):
        """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
        self.url = base_url
        self.pair_id = pair_id
        self.pair_name = get_currency_pair_to_poloniex(self.pair_id)
        self.on_update = on_update
        self.order_book_is_received = False
        self.should_run = False
        self.last_heartbeat_ts = None
        self.ws = None
        self.subscribe_string = json.dumps({'command': 'subscribe', 'channel': self.pair_name})
        self.subscribe_heartbeat = json.dumps({'command': 'subscribe', 'channel': WEBSOCKET_SUBSCRIBE_HEARTBEAT})

    def on_open(self):

        def run():
            log_subscribe_to_exchange_heartbeat('Poloniex')
            self.ws.send(self.subscribe_string)
            try:
                while self.should_run:
                    self.ws.send(self.subscribe_heartbeat)
                    sleep_for(1)
            except Exception as e:
                log_send_heart_beat_failed('Poloniex', e)
            log_unsubscribe_to_exchange_heartbeat('Poloniex')
        thread.start_new_thread(run, ())

    def on_public(self, compressed_data):
        msg = process_message(compressed_data)
        if not self.order_book_is_received and 'orderBook' in compressed_data:
            self.order_book_is_received = True
            order_book_delta = parse_socket_order_book_poloniex(msg, self.pair_id)
        else:
            order_book_delta = parse_socket_update_poloniex(msg)
        if order_book_delta is None:
            str_msg = str(msg)
            if '1010' in str_msg:
                self.last_heartbeat_ts = get_now_seconds_utc()
            else:
                err_msg = 'Poloniex - cant parse update from message: {msg}'.format(msg=str_msg)
                log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        else:
            self.last_heartbeat_ts = get_now_seconds_utc()
            self.on_update(EXCHANGE.POLONIEX, order_book_delta)

    def subscribe(self):
        if self.should_run:
            die_hard('Poloniex - another subcription thread running?')
        if get_logging_level() == LOG_ALL_TRACE:
            msg = 'Poloniex - call subscribe!'
            log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
            print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        self.should_run = True
        if get_logging_level() == LOG_ALL_TRACE:
            websocket.enableTrace(True)
        try:
            self.ws = create_connection(POLONIEX_WEBSCOKET_URL, enable_multithread=True)
            self.ws.settimeout(15)
        except Exception as e:
            msg = 'Poloniex - connect ws error - {}, retry...'.format(str(e))
            print_to_console(msg, LOG_ALL_ERRORS)
            self.disconnect()
            return
        self.ws.send(self.subscribe_string)
        log_conect_to_websocket('Poloniex')
        while self.should_run:
            try:
                compressed_data = self.ws.recv()
                self.on_public(compressed_data)
            except Exception as e:
                log_error_on_receive_from_socket('Poloniex', e)
                break
            if self.last_heartbeat_ts:
                ts_now = get_now_seconds_utc()
                if ts_now - self.last_heartbeat_ts > POLONIEX_WEBSOCKET_TIMEOUT:
                    log_heartbeat_is_missing('Poloniex', POLONIEX_WEBSOCKET_TIMEOUT, self.last_heartbeat_ts, ts_now)
                    break
        log_subscription_cancelled('Poloniex')
        self.disconnect()

    def disconnect(self):
        self.should_run = False
        self.order_book_is_received = False
        self.last_heartbeat_ts = None
        try:
            self.ws.close()
        except Exception as e:
            log_websocket_disconnect('Poloniex', e)

    def is_running(self):
        return self.should_run

def __init__(self, pair_id, on_update=default_on_public, base_url=POLONIEX_WEBSCOKET_URL):
    """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
    self.url = base_url
    self.pair_id = pair_id
    self.pair_name = get_currency_pair_to_poloniex(self.pair_id)
    self.on_update = on_update
    self.order_book_is_received = False
    self.should_run = False
    self.last_heartbeat_ts = None
    self.ws = None
    self.subscribe_string = json.dumps({'command': 'subscribe', 'channel': self.pair_name})
    self.subscribe_heartbeat = json.dumps({'command': 'subscribe', 'channel': WEBSOCKET_SUBSCRIBE_HEARTBEAT})

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

# Node: range
# Node: min
def round_volume_by_huobi_rules(volume, pair_id):
    pair_name = get_currency_pair_to_huobi(pair_id)
    base_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    if pair_name in PRECISION_NUMBER[base_currency_id]:
        return truncate_float(volume, PRECISION_NUMBER[base_currency_id][pair_name])
    return volume

# Node: split_currency_pairs
class SubscriptionHuobi(object):

    def __init__(self, pair_id, on_update=default_on_public, base_url=HUOBI_WEBSOCKET_URL):
        """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
        self.url = base_url
        self.pair_id = pair_id
        self.pair_name = get_currency_pair_to_huobi(self.pair_id)
        self.subscription_url = HUOBI_SUBSCRIPTION_STRING.format(pair_name=self.pair_name, uuid_id=uuid.uuid4())
        self.on_update = on_update
        self.should_run = False

    def on_public(self, args):
        msg = process_message(args)
        updated_order_book = parse_socket_update_huobi(msg, self.pair_id)
        if updated_order_book is None:
            if 'ping' in msg or 'pong' in msg or ('status' in msg and 'ok' == msg['status']):
                return
            err_msg = 'Huobi - cant parse update from message: {msg}'.format(msg=msg)
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        else:
            self.on_update(EXCHANGE.HUOBI, updated_order_book)

    def on_open(self):

        def run():
            log_subscribe_to_exchange_heartbeat('Huobi')
            self.ws.send(self.subscription_url)
            try:
                while self.should_run:
                    self.ws.send(json.dumps({'ping': 18212558000}))
                    sleep_for(1)
                self.ws.close()
            except Exception as e:
                log_send_heart_beat_failed('Huobi', e)
            log_unsubscribe_to_exchange_heartbeat('Huobi')
        thread.start_new_thread(run, ())

    def subscribe(self):
        if self.should_run:
            die_hard('Huobi - another subcription thread running?')
        self.should_run = True
        if get_logging_level() == LOG_ALL_TRACE:
            websocket.enableTrace(True)
        try:
            self.ws = create_connection(HUOBI_WEBSOCKET_URL, enable_multithread=True, sslopt={'cert_reqs': ssl.CERT_NONE})
            self.ws.settimeout(15)
        except Exception as e:
            print('Huobi - connect ws error - {}, retry...'.format(str(e)))
            self.disconnect()
            return
        self.on_open()
        log_conect_to_websocket('Huobi')
        while self.should_run:
            try:
                compress_data = self.ws.recv()
                if compress_data:
                    self.on_public(compress_data)
            except Exception as e:
                log_error_on_receive_from_socket('Huobi', e)
                break
        log_subscription_cancelled('Huobi')
        self.disconnect()

    def disconnect(self):
        self.should_run = False
        try:
            self.ws.close()
        except Exception as e:
            log_websocket_disconnect('Huobi', e)

    def is_running(self):
        return self.should_run

def __init__(self, pair_id, on_update=default_on_public, base_url=HUOBI_WEBSOCKET_URL):
    """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
    self.url = base_url
    self.pair_id = pair_id
    self.pair_name = get_currency_pair_to_huobi(self.pair_id)
    self.subscription_url = HUOBI_SUBSCRIPTION_STRING.format(pair_name=self.pair_name, uuid_id=uuid.uuid4())
    self.on_update = on_update
    self.should_run = False

# Node: uuid4
def round_volume_by_binance_rules(volume, pair_id):
    pair_name = get_currency_pair_to_binance(pair_id)
    base_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    if pair_name in PRECISION_NUMBER[base_currency_id]:
        return truncate_float(volume, PRECISION_NUMBER[base_currency_id][pair_name])
    return volume

# Node: do_we_have_enough
# Node: search_for_arbitrage
def determine_minimum_volume(first_order_book, second_order_book, balance_state):
    """
        we are going to SELL something at first exchange
        we are going to BUY something at second exchange using BASE_CURRENCY

        This method determine maximum available volume of DST_CURRENCY on 1ST exchanges
        This method determine maximum available volume according to amount of available BASE_CURRENCY on 2ND exchanges

    :param first_order_book:
    :param second_order_book:
    :param balance_state:
    :return:    Decimal object representing exact number
    """
    min_volume = min(first_order_book.bid[FIRST].volume, second_order_book.ask[LAST].volume)
    if min_volume <= 0:
        msg = 'determine_minimum_volume - something severely wrong - NEGATIVE min price: {pr}'.format(pr=min_volume)
        print_to_console(msg, LOG_ALL_ERRORS)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        assert min_volume <= 0
    base_currency_id, dst_currency_id = split_currency_pairs(first_order_book.pair_id)
    if not balance_state.do_we_have_enough(dst_currency_id, first_order_book.exchange_id, min_volume):
        min_volume = balance_state.get_available_volume_by_currency(dst_currency_id, first_order_book.exchange_id)
    if not balance_state.do_we_have_enough_by_pair(first_order_book.pair_id, second_order_book.exchange_id, min_volume, second_order_book.ask[LAST].price):
        min_volume = MAX_VOLUME_COEFFICIENT * balance_state.get_available_volume_by_currency(base_currency_id, second_order_book.exchange_id) / second_order_book.ask[LAST].price
    return min_volume

# Node: get_available_volume_by_currency
# Node: do_we_have_enough_by_pair
def determine_maximum_volume_by_balance(pair_id, deal_type, volume, price, balance):
    """
    :param pair_id:
    :param deal_type:
    :param volume:
    :param price:
    :param balance:
    :return: Decimal object representing exact volume
    """
    base_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    if deal_type == DEAL_TYPE.SELL:
        if not balance.do_we_have_enough(dst_currency_id, volume):
            volume = balance.available_balance[dst_currency_id]
    elif deal_type == DEAL_TYPE.BUY:
        if not balance.do_we_have_enough(base_currency_id, volume * price):
            volume = MAX_VOLUME_COEFFICIENT * balance.available_balance[base_currency_id] / price
    else:
        assert deal_type not in [DEAL_TYPE.BUY, DEAL_TYPE.SELL]
    return volume

def round_volume_by_exchange_rules(sell_exchange_id, buy_exchange_id, min_volume, pair_id):
    if EXCHANGE.BINANCE in {sell_exchange_id, buy_exchange_id}:
        return round_volume_by_binance_rules(volume=min_volume, pair_id=pair_id)
    elif EXCHANGE.HUOBI in {sell_exchange_id, buy_exchange_id}:
        return round_volume_by_huobi_rules(volume=min_volume, pair_id=pair_id)
    return truncate_float(min_volume, 8)

# Node: round_volume_by_binance_rules
# Node: round_volume_by_huobi_rules
def round_volume(exchange_id, min_volume, pair_id):
    if exchange_id == EXCHANGE.BINANCE:
        return round_volume_by_binance_rules(volume=min_volume, pair_id=pair_id)
    elif exchange_id == EXCHANGE.HUOBI:
        return round_volume_by_huobi_rules(volume=min_volume, pair_id=pair_id)
    return truncate_float(min_volume, 8)

def adjust_currency_balance(first_order_book, second_order_book, threshold, balance_threshold, action_to_perform, balance_state, deal_cap, type_of_deal, worker_pool, msg_queue):
    deal_status = (STATUS.FAILURE, None)
    pair_id = first_order_book.pair_id
    src_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    src_exchange_id = first_order_book.exchange_id
    dst_exchange_id = second_order_book.exchange_id
    if balance_state.is_there_disbalance(dst_currency_id, src_exchange_id, dst_exchange_id, balance_threshold) and is_no_pending_order(pair_id, src_exchange_id, dst_exchange_id):
        max_volume = Decimal(0.5) * abs(balance_state.get_available_volume_by_currency(dst_currency_id, dst_exchange_id) - balance_state.get_available_volume_by_currency(dst_currency_id, src_exchange_id))
        deal_cap.update_max_volume_cap(max_volume)
        log_currency_disbalance_present(src_exchange_id, dst_exchange_id, pair_id, dst_currency_id, balance_threshold, max_volume, threshold)
        deal_status = search_for_arbitrage(first_order_book, second_order_book, threshold, balance_threshold, action_to_perform, balance_state, deal_cap, type_of_deal, worker_pool, msg_queue)
    else:
        log_currency_disbalance_heart_beat(src_exchange_id, dst_exchange_id, dst_currency_id, balance_threshold)
    return deal_status

# Node: is_there_disbalance
# Node: is_no_pending_order
# Node: log_currency_disbalance_present
# Node: log_currency_disbalance_heart_beat
def compute_new_min_cap_from_tickers(pair_id, tickers):
    min_price = DECIMAL_ZERO
    for ticker in tickers:
        if ticker is not None:
            try:
                min_price = max(min_price, ticker.ask)
            except:
                msg = 'Msg bad ticker value = {}!'.format(ticker)
                log_to_file(msg, ERROR_LOG_FILE_NAME)
    base_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    if min_price != DECIMAL_ZERO:
        return MIN_VOLUME_COEFFICIENT[base_currency_id] / min_price
    return DECIMAL_ZERO

# Node: max
def compute_min_cap_from_ticker(pair_id, ticker):
    min_price = DECIMAL_ZERO
    if ticker is not None:
        min_price = max(min_price, ticker.ask)
    base_currency_id, dst_currency_id = split_currency_pairs(pair_id)
    if min_price != DECIMAL_ZERO:
        return MIN_VOLUME_COEFFICIENT[base_currency_id] / min_price
    return DECIMAL_ZERO

