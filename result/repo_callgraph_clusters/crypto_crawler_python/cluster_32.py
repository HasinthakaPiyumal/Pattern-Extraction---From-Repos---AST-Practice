# Cluster 32

def load_keys(path):
    """
    :param path: full path to folder with public keys, each key should be named as corresponding exchange
    :return:
    """
    global access_keys
    for exchange_id in EXCHANGE.values():
        exchange_name = get_exchange_name_by_id(exchange_id)
        key = ExchangeKey.from_file(path, exchange_name)
        access_keys[exchange_id] = key

# Node: values
# Node: from_file
def load_key_by_exchange(path, exchange_id):
    global access_keys
    exchange_name = get_exchange_name_by_id(exchange_id)
    key = ExchangeKey.from_file(path, exchange_name)
    access_keys[exchange_id] = key

# Node: set_logging_level
class OrderBook(BaseData):
    insert_query = ORDER_BOOK_INSERT_QUERY
    type = ORDER_BOOK_TYPE_NAME
    table_name = ORDER_BOOK_TABLE_NAME
    columns = ORDER_BOOK_COLUMNS

    def __init__(self, pair_id, timest, sell_bids, buy_bids, exchange_id, sequence_id=None):
        self.pair_id = int(pair_id)
        self.pair_name = get_pair_name_by_id(self.pair_id)
        self.timest = timest
        self.ask = sell_bids
        self.bid = buy_bids
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)
        self.sequence_id = sequence_id

    def is_valid(self):
        return self.ask and self.bid

    def sort_by_price(self):
        self.bid = sorted(self.bid, key=lambda x: x.price, reverse=True)
        self.ask = sorted(self.ask, key=lambda x: x.price, reverse=False)

    def get_pg_arg_list(self):
        return (self.pair_id, self.exchange_id, self.timest, get_date_time_from_epoch(self.timest))

    def __str__(self):
        attr_list = [a for a in dir(self) if not a.startswith('__') and (not a.startswith('ask')) and (not a.startswith('bid')) and (not a.startswith('insert')) and (not callable(getattr(self, a)))]
        str_repr = '['
        for every_attr in attr_list:
            str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
        str_repr += 'bids - [' + '\n'.join(map(str, self.bid)) + '] '
        str_repr += 'asks - [' + '\n'.join(map(str, self.ask)) + ']]'
        return str_repr

    @classmethod
    def from_poloniex(cls, json_document, currency, timest):
        """
        {"asks":[["0.00006604",11590.35669799],["0.00006606",25756.70896058]],
        "bids":[["0.00006600",46771.47390146],["0.00006591",25268.665],],
        "isFrozen":"0","seq":41049600}
        """
        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document['asks']]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document['bids']]
        pair_id = get_currency_pair_from_poloniex(currency)
        sequence_id = long(json_document['seq'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.POLONIEX, sequence_id)

    @classmethod
    def from_kraken(cls, json_document, currency, timest):
        """
        {"error":[],"result":{"XETHXXBT":{"asks":[["0.081451","0.200",1501690777],["0.081496","163.150",1501691124]
        "bids":[["0.080928","0.100",1501691107],["0.080926","0.255",1501691110]
        """
        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document['asks']]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document['bids']]
        pair_id = get_currency_pair_from_kraken(currency)
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, json_document, currency, timest):
        """
        {"success":true,"message":"","result":{"buy":[{"Quantity":12.76073322,"Rate":0.01557999},{"Quantity":12.01802925,"Rate":0.01557998}
        "sell":[{"Quantity":0.38767680,"Rate":0.01560999},{"Quantity":2.24182363,"Rate":0.01561999}
        """
        sell_bids = []
        if 'sell' in json_document and json_document['sell'] is not None:
            for b in json_document['sell']:
                sell_bids.append(Deal(b['Rate'], b['Quantity']))
        buy_bids = []
        if 'buy' in json_document and json_document['buy'] is not None:
            for b in json_document['buy']:
                buy_bids.append(Deal(b['Rate'], b['Quantity']))
        pair_id = get_currency_pair_from_bittrex(currency)
        sequence_id = get_now_seconds_utc_ms()
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BITTREX, sequence_id)

    @classmethod
    def from_binance(cls, json_document, currency, timest):
        """
        "lastUpdateId":1668114,"bids":[["0.40303000","22.00000000",[]],],"asks":[["0.41287000","1.00000000",[]]
        """
        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('asks', [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('bids', [])]
        pair_id = get_currency_pair_from_binance(currency)
        sequence_id = long(json_document['lastUpdateId'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BINANCE, sequence_id)

    @classmethod
    def from_huobi(cls, json_document, pair_name, timest):
        """
        "tick": {
            "id": 1489464585407,
            "ts": 1489464585407,
            "bids": [
              [7964, 0.0678], // [price, amount]
              [7963, 0.9162],
              [7961, 0.1],
            ],
            "asks": [
              [7979, 0.0736],
              [7980, 1.0292],
            ]

        :param pair_name:
        :param timest:
        :return:
        """
        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('asks', [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('bids', [])]
        pair_id = get_currency_pair_from_huobi(pair_name)
        sequence_id = long(json_document['version'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.HUOBI, sequence_id)

    @classmethod
    def from_row(cls, db_row, asks_rows, sell_rows):
        currency_pair_id = db_row[1]
        exchange_id = db_row[2]
        timest = db_row[3]
        ask_bids = [Deal(entry[2], entry[3]) for entry in asks_rows]
        sell_bids = [Deal(entry[2], entry[3]) for entry in sell_rows]
        return OrderBook(currency_pair_id, timest, ask_bids, sell_bids, exchange_id)

    def insert_new_bid_preserve_order(self, new_bid, overwrite_volume=True, err_msg=None):
        """
            Bids array are sorted in reversed order i.e. highest - first
            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!

        """
        item_insert_point = binary_search(self.bid, new_bid, cmp_method_bid)
        is_present = False
        if item_insert_point < len(self.bid):
            is_present = self.bid[item_insert_point] == new_bid
        almost_zero = new_bid.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and (not overwrite_volume)
        update_volume_error = not is_present and (not overwrite_volume)
        should_delete = almost_zero and is_present
        if should_delete:
            del self.bid[item_insert_point]
        elif is_present:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_overwrite:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_update_volume:
            self.bid[item_insert_point].volume -= new_bid.volume
            if self.bid[item_insert_point].volume < 0:
                die_hard('Negative value of bid!')
        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            self.bid.insert(item_insert_point, new_bid)

    def insert_new_ask_preserve_order(self, new_ask, overwrite_volume=True, err_msg=None):
        """
            Ask array are sorted in reversed order i.e. lowest - first

            self.ask = sorted(self.ask, key = lambda x: x.price, reverse=False)

            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!
        """
        item_insert_point = binary_search(self.ask, new_ask, cmp_method_ask)
        is_present = False
        if item_insert_point < len(self.ask):
            is_present = self.ask[item_insert_point] == new_ask
        almost_zero = new_ask.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and (not overwrite_volume)
        update_volume_error = not is_present and (not overwrite_volume)
        should_delete = almost_zero and is_present
        if should_delete:
            del self.ask[item_insert_point]
        elif should_overwrite:
            self.ask[item_insert_point].volume = new_ask.volume
        elif should_update_volume:
            self.ask[item_insert_point].volume -= new_ask.volume
            if self.ask[item_insert_point].volume < 0:
                die_hard('Negative value of ask!')
        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            self.ask.insert(item_insert_point, new_ask)

    def update_for_poloniex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """
        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)
            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                return STATUS.SUCCESS
            if self.sequence_id + 1 != order_book_update.sequence_id:
                log_sequence_id_mismatch('Poloniex', self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE
            self.sequence_id = order_book_update.sequence_id
            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)
            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)
        return STATUS.SUCCESS

    def _copy_order_book(self, other_order_book):
        self.timest = other_order_book.timest
        self.exchange_id = other_order_book.exchange_id
        self.exchange = other_order_book.exchange_id
        self.pair_id = other_order_book.pair_id
        self.pair_name = other_order_book.pair_id
        self.ask = copy.deepcopy(other_order_book.ask)
        self.bid = copy.deepcopy(other_order_book.bid)
        self.sequence_id = other_order_book.sequence_id

    def update_for_bittrex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """
        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)
            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                return STATUS.SUCCESS
            elif self.sequence_id + 1 != order_book_update.sequence_id:
                log_sequence_id_mismatch('Bittrex', self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE
            self.sequence_id = order_book_update.sequence_id
            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)
            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)
            for trade_sell in order_book_update.trades_sell:
                err_msg = 'Bittrex socket CANT FIND fill request FILL AND UPDATE - SELL??? {wtf}'.format(wtf=trade_sell)
                self.insert_new_ask_preserve_order(trade_sell, overwrite_volume=False, err_msg=err_msg)
            for trade_buy in order_book_update.trades_buy:
                err_msg = 'Bittrex socket CANT FIND fill request FILL AND UPDATE - BUY??? {wtf}'.format(wtf=trade_buy)
                self.insert_new_bid_preserve_order(trade_buy, overwrite_volume=False, err_msg=err_msg)
        return STATUS.SUCCESS

    def update_for_binance(self, order_book_update):
        """
        For binance sequence_id is a range of number.
        one number for every price level updates.

        "U": 157,           // First update ID in event
        "u": 160,           // Final update ID in event

        During update parsing we are use following logic:

        sequence_id = long(order_book_delta["U"])

        :param order_book_update:
        :return:
        """
        if self.sequence_id >= order_book_update.sequence_id:
            return STATUS.SUCCESS
        if self.sequence_id + 1 != order_book_update.sequence_id:
            log_sequence_id_mismatch('Binance', self.sequence_id, order_book_update.sequence_id)
            return STATUS.FAILURE
        self.sequence_id = order_book_update.sequence_id_end
        for ask in order_book_update.ask:
            self.insert_new_ask_preserve_order(ask)
        for bid in order_book_update.bid:
            self.insert_new_bid_preserve_order(bid)
        return STATUS.SUCCESS

    def update_for_huobi(self, order_book_update):
        """
        NOTE: always get full order book
        :param order_book_update:
        :return:
        """
        self._copy_order_book(order_book_update)
        self.sort_by_price()
        return STATUS.SUCCESS

    def update(self, exchange_id, order_book_delta):
        method = {EXCHANGE.POLONIEX: self.update_for_poloniex, EXCHANGE.BITTREX: self.update_for_bittrex, EXCHANGE.BINANCE: self.update_for_binance, EXCHANGE.HUOBI: self.update_for_huobi}[exchange_id]
        return method(order_book_delta)

def sort_by_price(self):
    self.bid = sorted(self.bid, key=lambda x: x.price, reverse=True)
    self.ask = sorted(self.ask, key=lambda x: x.price, reverse=False)

# Node: sorted
# Node: get_debug_level_name_by_id
# Node: get_currency_pair_name_by_exchange_id
# Node: get_key_by_exchange
def get_ticker_speedup(timest, processor):
    ohlc_async_requests = []
    for exchange_id in [EXCHANGE.BITTREX, EXCHANGE.KRAKEN, EXCHANGE.HUOBI]:
        for pair_id in CURRENCY_PAIR.values():
            pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
            if pair_name is None:
                continue
            method_for_url = get_ticker_url_by_exchange_id(exchange_id)
            request_url = method_for_url(pair_name)
            constructor = get_ticker_constructor_by_exchange_id(exchange_id)
            ohlc_async_requests.append(WorkUnit(request_url, constructor, pair_name, timest))
    async_results = processor.process_async_get(ohlc_async_requests, timeout=HTTP_TIMEOUT_SECONDS)
    async_results += get_tickers_poloniex(POLONIEX_CURRENCY_PAIRS, timest)
    async_results += get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
    return async_results

# Node: get_ticker_url_by_exchange_id
# Node: method_for_url
# Node: get_ticker_constructor_by_exchange_id
# Node: WorkUnit
# Node: process_async_get
def get_ticker_for_arbitrage(pair_id, timest, exchange_list, processor):
    async_requests = []
    for exchange_id in exchange_list:
        pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
        if pair_name is None:
            msg = 'get_ticker for arbitrage - wrong pair_id - {pair_id} for exchange_id = {idd}!'.format(pair_id=pair_id, idd=exchange_id)
            print_to_console(msg, LOG_ALL_ERRORS)
            assert pair_name is None
        method_for_url = get_ticker_url_by_exchange_id(exchange_id)
        request_url = method_for_url(pair_name)
        constructor = get_ticker_constructor_by_exchange_id(exchange_id)
        async_requests.append(WorkUnit(request_url, constructor, pair_name, timest))
    res = processor.process_async_get(async_requests, timeout=5)
    return res

def get_ohlc_speedup(date_start, date_end, processor):
    ohlc_async_requests = []
    for exchange_id in EXCHANGE.values():
        if exchange_id == EXCHANGE.KRAKEN:
            continue
        for pair_id in CURRENCY_PAIR.values():
            pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
            if pair_name:
                period = get_ohlc_period_by_exchange_id(exchange_id)
                method_for_url = get_ohlc_url_by_echange_id(exchange_id)
                request_url = method_for_url(pair_name, date_start, date_end, period)
                constructor = get_candle_constructor_by_exchange_id(exchange_id)
                ohlc_async_requests.append(WorkUnit(request_url, constructor, pair_name, date_start, date_end))
    return processor.process_async_get(ohlc_async_requests, HTTP_TIMEOUT_SECONDS)

# Node: get_ohlc_period_by_exchange_id
# Node: get_ohlc_url_by_echange_id
# Node: get_candle_constructor_by_exchange_id
def buy_by_exchange(trade):
    res = (STATUS.FAILURE, None)
    assert_trade_type(trade, DEAL_TYPE.BUY)
    key = get_key_by_exchange(trade.exchange_id)
    methods_by_exchange = {EXCHANGE.BITTREX: (get_currency_pair_to_bittrex, add_buy_order_bittrex), EXCHANGE.KRAKEN: (get_currency_pair_to_kraken, add_buy_order_kraken), EXCHANGE.POLONIEX: (get_currency_pair_to_poloniex, add_buy_order_poloniex), EXCHANGE.BINANCE: (get_currency_pair_to_binance, add_buy_order_binance), EXCHANGE.HUOBI: (get_currency_pair_to_huobi, add_buy_order_huobi)}
    if trade.exchange_id in methods_by_exchange:
        get_currency_pair, add_buy_order = methods_by_exchange[trade.exchange_id]
        currency = get_currency_pair(trade.pair_id)
        res = add_buy_order(key, currency, trade.price, trade.volume)
    else:
        log_error_unknown_exchange('buy_by_exchange', trade)
    return res

# Node: assert_trade_type
# Node: get_currency_pair
# Node: add_buy_order
# Node: log_error_unknown_exchange
def sell_by_exchange(trade):
    res = (STATUS.FAILURE, None)
    assert_trade_type(trade, DEAL_TYPE.SELL)
    key = get_key_by_exchange(trade.exchange_id)
    methods_by_exchange = {EXCHANGE.BITTREX: (get_currency_pair_to_bittrex, add_sell_order_bittrex), EXCHANGE.KRAKEN: (get_currency_pair_to_kraken, add_sell_order_kraken), EXCHANGE.POLONIEX: (get_currency_pair_to_poloniex, add_sell_order_poloniex), EXCHANGE.BINANCE: (get_currency_pair_to_binance, add_sell_order_binance), EXCHANGE.HUOBI: (get_currency_pair_to_huobi, add_sell_order_huobi)}
    if trade.exchange_id in methods_by_exchange:
        get_currency_pair, add_sell_order = methods_by_exchange[trade.exchange_id]
        currency = get_currency_pair(trade.pair_id)
        res = add_sell_order(key, currency, trade.price, trade.volume)
    else:
        log_error_unknown_exchange('sell_by_exchange', trade)
    return res

# Node: add_sell_order
def cancel_by_exchange(trade):
    res = (STATUS.FAILURE, None)
    key = get_key_by_exchange(trade.exchange_id)
    methods_by_exchange = {EXCHANGE.BITTREX: cancel_order_bittrex, EXCHANGE.KRAKEN: cancel_order_kraken, EXCHANGE.POLONIEX: cancel_order_poloniex, EXCHANGE.HUOBI: cancel_order_huobi}
    if trade.exchange_id in methods_by_exchange:
        res = methods_by_exchange[trade.exchange_id](key, trade.order_id)
    elif trade.exchange_id == EXCHANGE.BINANCE:
        pair_name = get_currency_pair_to_binance(trade.pair_id)
        res = cancel_order_binance(key, pair_name, trade.order_id)
    else:
        log_error_unknown_exchange('cancel_by_exchange', trade)
    return res

# Node: cancel_order_binance
def get_open_orders_by_exchange(exchange_id, pair_id):
    res = (STATUS.FAILURE, None)
    key = get_key_by_exchange(exchange_id)
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
    method_by_exchange = {EXCHANGE.BITTREX: get_open_orders_bittrix, EXCHANGE.KRAKEN: get_open_orders_kraken, EXCHANGE.POLONIEX: get_open_orders_poloniex, EXCHANGE.BINANCE: get_open_orders_binance, EXCHANGE.HUOBI: get_open_orders_huobi}
    if exchange_id in method_by_exchange:
        get_open_orders = method_by_exchange[exchange_id]
        res = get_open_orders(key, pair_name)
    else:
        msg = 'get_open_orders_by_exchange - Unknown exchange! {idx}'.format(idx=exchange_id)
        print_to_console(msg, LOG_ALL_ERRORS)
    return res

# Node: get_open_orders
def get_open_orders_for_arbitrage_pair(cfg, processor):
    open_orders = []
    for exchange_id in [cfg.sell_exchange_id, cfg.buy_exchange_id]:
        key = get_key_by_exchange(exchange_id)
        pair_name = get_currency_pair_name_by_exchange_id(cfg.pair_id, exchange_id)
        method_for_url = get_open_orders_post_details_generator(exchange_id)
        post_details = method_for_url(key, pair_name)
        constructor = get_open_orders_constructor_by_exchange_id(exchange_id)
        http_method = get_http_method_open_order_by_exchange_id(exchange_id)
        wu = WorkUnit(post_details.final_url, constructor, pair_name)
        wu.add_post_details(post_details)
        wu.add_http_method(http_method)
        open_orders.append(wu)
    return processor.process_async_custom(open_orders, HTTP_TIMEOUT_SECONDS)

# Node: get_open_orders_post_details_generator
# Node: get_open_orders_constructor_by_exchange_id
# Node: get_http_method_open_order_by_exchange_id
# Node: add_post_details
# Node: add_http_method
# Node: process_async_custom
def get_history_speedup(date_start, date_end, processor):
    history_async_requests = []
    for exchange_id in EXCHANGE.values():
        if exchange_id == EXCHANGE.KRAKEN:
            continue
        for pair_id in CURRENCY_PAIR.values():
            pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
            if pair_name:
                method_for_url = get_history_url_by_exchange_id(exchange_id)
                request_url = method_for_url(pair_name, date_start, date_end)
                constructor = get_history_constructor_by_exchange_id(exchange_id)
                history_async_requests.append(WorkUnit(request_url, constructor, pair_name, date_end))
    return processor.process_async_get(history_async_requests, HTTP_TIMEOUT_SECONDS)

# Node: get_history_url_by_exchange_id
# Node: get_history_constructor_by_exchange_id
def get_order_history_by_exchange(exchange_id, pair_id):
    res = (STATUS.FAILURE, None)
    key = get_key_by_exchange(exchange_id)
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
    method_by_exchange = {EXCHANGE.BITTREX: get_order_history_bittrex, EXCHANGE.KRAKEN: get_order_history_kraken, EXCHANGE.POLONIEX: get_order_history_poloniex, EXCHANGE.BINANCE: get_order_history_binance, EXCHANGE.HUOBI: get_order_history_huobi}
    if exchange_id in method_by_exchange:
        get_order_history = method_by_exchange[exchange_id]
        res = get_order_history(key, pair_name)
    else:
        msg = 'get_open_orders_by_exchange - Unknown exchange! {idx}'.format(idx=exchange_id)
        print_to_console(msg, LOG_ALL_ERRORS)
    return res

# Node: get_order_history
class PoloniexPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.POLONIEX)
        self.poloniex_key = get_key_by_exchange(EXCHANGE.POLONIEX)

    def test_balance_retrieval(self):
        status, balance = get_balance_poloniex(self.poloniex_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_poloniex(self.poloniex_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid orderNumber parameter' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid currencyPair parameter' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid currencyPair parameter' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_poloniex(self.poloniex_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_poloniex(self.poloniex_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    load_key_by_exchange(API_KEY_PATH, EXCHANGE.POLONIEX)
    self.poloniex_key = get_key_by_exchange(EXCHANGE.POLONIEX)

# Node: load_key_by_exchange
class KrakenPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.KRAKEN)
        self.kraken_key = get_key_by_exchange(EXCHANGE.KRAKEN)

    def test_balance_retrieval(self):
        status, balance = get_balance_kraken(self.kraken_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_kraken(self.kraken_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue("Invalid order'" in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('Unknown asset pair' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('Unknown asset pair' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_kraken(self.kraken_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_kraken(self.kraken_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    load_key_by_exchange(API_KEY_PATH, EXCHANGE.KRAKEN)
    self.kraken_key = get_key_by_exchange(EXCHANGE.KRAKEN)

class BittrexPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.BITTREX)
        self.bittrex_key = get_key_by_exchange(EXCHANGE.BITTREX)

    def test_balance_retrieval(self):
        status, balance = get_balance_bittrex(self.bittrex_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_bittrex(self.bittrex_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_ORDER' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_MARKET' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_MARKET' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_bittrix(self.bittrex_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_bittrex(self.bittrex_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    load_key_by_exchange(API_KEY_PATH, EXCHANGE.BITTREX)
    self.bittrex_key = get_key_by_exchange(EXCHANGE.BITTREX)

class HuobiPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.HUOBI)
        self.huobi_key = get_key_by_exchange(EXCHANGE.HUOBI)

    def test_balance_retrieval(self):
        status, balance = get_balance_huobi(self.huobi_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_huobi(self.huobi_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-order-id' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_huobi(self.huobi_key, pair_name='dashbtc')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_huobi(self.huobi_key, pair_name='dashbtc')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    load_key_by_exchange(API_KEY_PATH, EXCHANGE.HUOBI)
    self.huobi_key = get_key_by_exchange(EXCHANGE.HUOBI)

class BinancePrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.BINANCE)
        self.binance_key = get_key_by_exchange(EXCHANGE.BINANCE)

    def test_balance_retrieval(self):
        status, balance = get_balance_binance(self.binance_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_binance(self.binance_key, pair_name='NULL', order_id='1234567890')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_binance(self.binance_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_binance(self.binance_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    load_key_by_exchange(API_KEY_PATH, EXCHANGE.BINANCE)
    self.binance_key = get_key_by_exchange(EXCHANGE.BINANCE)

class BinarySearchTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        self.first = Deal(0.03172795, 0.1)
        self.non_present = Deal(10.1, 0.1)
        self.deal_update = Deal(0.03172801, 0.4)
        unsorted = [self.first, Deal(0.03172796, 0.2), Deal(0.03172798, 0.3), self.deal_update, Deal(0.03173, 0.5)]
        self.asks = sorted(unsorted, key=lambda x: x.price, reverse=False)
        self.bids = sorted(unsorted, key=lambda x: x.price, reverse=True)

    def test_bin_search_asks(self):
        item_insert_point = binary_search(self.asks, self.first, cmp_method_ask)
        self.assertEquals(item_insert_point, 0)

    def test_bin_search_asks_not_present(self):
        item_insert_point = binary_search(self.asks, self.non_present, cmp_method_ask)
        self.assertEquals(item_insert_point, len(self.asks))

    def test_bin_search_asks_update_present(self):
        idx = binary_search(self.asks, self.deal_update, cmp_method_ask)
        is_present = False
        if idx < len(self.asks):
            is_present = self.asks[idx] == self.deal_update
        self.assertTrue(is_present)

    def test_bin_search_bids(self):
        item_insert_point = binary_search(self.bids, self.first, cmp_method_bid)
        self.assertEquals(item_insert_point, -1 + len(self.bids))

    def test_bin_search_bids_not_present(self):
        item_insert_point = binary_search(self.bids, self.non_present, cmp_method_bid)
        self.assertEquals(item_insert_point, 0)

    def test_bin_search_bids_update_present(self):
        idx = binary_search(self.bids, self.deal_update, cmp_method_bid)
        is_present = False
        if idx < len(self.bids):
            is_present = self.bids[idx] == self.deal_update
        self.assertTrue(is_present)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)
    self.first = Deal(0.03172795, 0.1)
    self.non_present = Deal(10.1, 0.1)
    self.deal_update = Deal(0.03172801, 0.4)
    unsorted = [self.first, Deal(0.03172796, 0.2), Deal(0.03172798, 0.3), self.deal_update, Deal(0.03173, 0.5)]
    self.asks = sorted(unsorted, key=lambda x: x.price, reverse=False)
    self.bids = sorted(unsorted, key=lambda x: x.price, reverse=True)

class BinancePublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_binance_ticker_retrieval(self):
        timest = get_now_seconds_local()
        tickers = get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
        for ticker in tickers:
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_binance_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for currency in BINANCE_CURRENCY_PAIRS:
            period = '15m'
            candles = get_ohlc_binance(currency, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_binance_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in BINANCE_CURRENCY_PAIRS:
            order_book = get_order_book_binance(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_binance_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in BINANCE_CURRENCY_PAIRS:
            trade_history = get_history_binance(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class BittrexPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_bittrex_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in BITTREX_CURRENCY_PAIRS:
            ticker = get_ticker_bittrex(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_bittrex_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in BITTREX_CURRENCY_PAIRS:
            period = 'thirtyMin'
            candles = get_ohlc_bittrex(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_bittrex_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in BITTREX_CURRENCY_PAIRS:
            order_book = get_order_book_bittrex(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_bittrex_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in BITTREX_CURRENCY_PAIRS:
            trade_history = get_history_bittrex(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class HuobiPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_huobi_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for currency in HUOBI_CURRENCY_PAIRS:
            ticker = get_ticker_huobi(currency, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_huobi_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for currency in HUOBI_CURRENCY_PAIRS:
            period = '15min'
            candles = get_ohlc_huobi(currency, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_huobi_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in HUOBI_CURRENCY_PAIRS:
            order_book = get_order_book_huobi(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_huobi_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in HUOBI_CURRENCY_PAIRS:
            trade_history = get_history_huobi(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class KrakenPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_kraken_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in KRAKEN_CURRENCIES:
            ticker = get_ticker_kraken(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_kraken_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in KRAKEN_CURRENCIES:
            period = 15
            candles = get_ohlc_kraken(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_kraken_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in KRAKEN_CURRENCIES:
            order_book = get_order_book_kraken(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_kraken_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in KRAKEN_CURRENCIES:
            trade_history = get_history_kraken(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class PoloniexPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_poloniex_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            ticker = get_ticker_poloniex(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_poloniex_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            period = 14400
            candles = get_ohlc_poloniex(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_poloniex_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in POLONIEX_CURRENCY_PAIRS:
            order_book = get_order_book_poloniex(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_poloniex_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            trade_history = get_history_poloniex(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class BittrexSocketApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_socket_subscription(self):
        t1 = SubscriptionBittrex(CURRENCY_PAIR.BTC_TO_ETC)
        buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
        buy_subscription_thread.daemon = True
        buy_subscription_thread.start()
        sleep_for(5)
        self.assertTrue(t1.should_run)
        t1.disconnect()
        self.assertFalse(t1.should_run)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class PoloniexSocketApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_socket_subscription(self):
        t1 = SubscriptionPoloniex(CURRENCY_PAIR.BTC_TO_ETC)
        buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
        buy_subscription_thread.daemon = True
        buy_subscription_thread.start()
        sleep_for(5)
        self.assertTrue(t1.should_run)
        t1.disconnect()
        self.assertFalse(t1.should_run)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class HuobiSocketApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_socket_subscription(self):
        t1 = SubscriptionHuobi(CURRENCY_PAIR.BTC_TO_ETC)
        buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
        buy_subscription_thread.daemon = True
        buy_subscription_thread.start()
        sleep_for(5)
        self.assertTrue(t1.should_run)
        t1.disconnect()
        self.assertFalse(t1.should_run)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class BinanceSocketApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_socket_subscription(self):
        t1 = SubscriptionBinance(CURRENCY_PAIR.BTC_TO_ETC)
        buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
        buy_subscription_thread.daemon = True
        buy_subscription_thread.start()
        sleep_for(5)
        self.assertTrue(t1.should_run)
        t1.disconnect()
        self.assertFalse(t1.should_run)

def setUp(self):
    set_logging_level(LOG_ALL_ERRORS)

class CommonSettings(BaseData):

    def __init__(self, logging_level_id=LOG_ALL_DEBUG, log_folder=LOGS_FOLDER, key_path=API_KEY_PATH, cache_host=CACHE_HOST, cache_port=CACHE_PORT, db_host=DB_HOST, db_port=DB_PORT, db_name=DB_NAME, exchanges_ids=None):
        self.logging_level_id = logging_level_id
        self.logging_level_name = get_debug_level_name_by_id(self.logging_level_id)
        self.log_folder = log_folder
        self.key_path = key_path
        self.cache_host = cache_host
        self.cache_port = cache_port
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        if not exchanges_ids:
            self.exchanges = EXCHANGE.values()
        else:
            self.exchanges = exchanges_ids

    @classmethod
    def from_cfg(cls, file_name):
        config = ConfigParser.RawConfigParser()
        config.read(file_name)
        log_level_name = config.get('logging', 'log_level')
        log_level_id = get_logging_level_id_by_name(log_level_name)
        exchanges_ids = parse_exchange_ids(config.get('common', 'exchanges'))
        return CommonSettings(log_level_id, config.get('logging', 'logs_folder'), config.get('keys', 'path_to_api_keys'), config.get('redis', 'redis_host'), config.get('redis', 'redis_port'), config.get('postgres', 'db_host'), config.get('postgres', 'db_port'), config.get('postgres', 'db_name'), exchanges_ids)

def __init__(self, logging_level_id=LOG_ALL_DEBUG, log_folder=LOGS_FOLDER, key_path=API_KEY_PATH, cache_host=CACHE_HOST, cache_port=CACHE_PORT, db_host=DB_HOST, db_port=DB_PORT, db_name=DB_NAME, exchanges_ids=None):
    self.logging_level_id = logging_level_id
    self.logging_level_name = get_debug_level_name_by_id(self.logging_level_id)
    self.log_folder = log_folder
    self.key_path = key_path
    self.cache_host = cache_host
    self.cache_port = cache_port
    self.db_host = db_host
    self.db_port = db_port
    self.db_name = db_name
    if not exchanges_ids:
        self.exchanges = EXCHANGE.values()
    else:
        self.exchanges = exchanges_ids

