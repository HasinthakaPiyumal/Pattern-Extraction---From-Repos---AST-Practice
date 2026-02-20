# Cluster 31

# Node: encode
# Node: get_now_seconds_utc
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

# Node: type
# Node: _copy_order_book
# Node: sort_by_price
# Node: log_sequence_id_mismatch
# Node: insert_new_ask_preserve_order
# Node: insert_new_bid_preserve_order
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

# Node: method
# Node: ts_to_string_utc
def get_balance_poloniex(key):
    """
    https://poloniex.com/tradingApi
    {'Key': 'QN6SDFQG-XVG2CGG3-WDDG2WDV-VXZ7MYL3',
    'Sign': '368a800fcd4bc0f0d95151ed29c9f84ddf6cae6bc366d3105db1560318da72aa82281b5ea52f4d4ec929dd0eabc7339fe0e7dc824bf0f1c64e099344cd6e74d0'}
    {'nonce': 1508507033330, 'command': 'returnCompleteBalances'}

    {"LTC":{"available":"5.015","onOrders":"1.0025","btcValue":"0.078"},"NXT:{...} ... }

    """
    post_details = get_balance_poloniex_post_details(key)
    err_msg = 'check poloniex balance called'
    timest = get_now_seconds_utc()
    error_code, res = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY, timeout=POLONIEX_DEAL_TIMEOUT)
    if error_code == STATUS.SUCCESS:
        res = Balance.from_poloniex(timest, res)
    return (error_code, res)

# Node: get_balance_poloniex_post_details
def get_order_history_poloniex(key, pair_name, time_start=0, time_end=get_now_seconds_utc(), limit=POLONIEX_ORDER_HISTORY_LIMIT):
    post_details = get_order_history_poloniex_post_details(key, pair_name, time_start, time_end, limit)
    err_msg = 'get poloniex order history for time interval for pp={pp}'.format(pp=post_details)
    status_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY)
    historical_orders = []
    if status_code == STATUS.SUCCESS:
        status_code, historical_orders = get_order_history_poloniex_result_processor(json_document, pair_name)
    return (status_code, historical_orders)

# Node: get_order_history_poloniex_post_details
# Node: get_order_history_poloniex_result_processor
class ConnectionPool:

    def __init__(self, pool_size=POOL_SIZE):
        self.session = requests.Session()
        self.pool_size = pool_size
        self.network_pool = Pool(self.pool_size)

    @classmethod
    def _process_futures(cls, work_units_batch):
        """
            Operate under `WorkUnit` objects after returning from async calls.
            Try to apply job specific constructor method for response returned by exchange.
            In case constructor method fail for any reason - try to wrap all available details into debug string.

        :param work_units_batch:
        :return: array of either object, parsed from exchange responce or error messages as string
        """
        res = []
        for work_unit in work_units_batch:
            if get_logging_level() >= LOG_ALL_DEBUG:
                log_responce(work_unit)
            result = None
            if work_unit.future_value is None or work_unit.future_status_code != HTTP_SUCCESS:
                result = log_responce_cant_be_parsed(work_unit)
                res.append(result)
            else:
                try:
                    result = work_unit.method(work_unit.future_value_json, *work_unit.args)
                except Exception as e:
                    pass
                if result is not None:
                    if type(result) is list:
                        res += result
                    else:
                        res.append(result)
                else:
                    result = log_responce_cant_be_parsed(work_unit)
                    res.append(result)
        return res

    def async_get_to_list(self, work_units, timeout):
        res = []
        for work_units_batch in batch(work_units, self.pool_size):
            futures = []
            for work_unit in work_units_batch:
                some_future = self.network_pool.spawn(self.session.get, work_unit.url, timeout=timeout)
                work_unit.add_future(some_future)
                futures.append(some_future)
            gevent.joinall(futures)
            res += self._process_futures(work_units_batch)
        return res

    def async_post_to_list(self, work_units, timeout):
        res = []
        for work_units_batch in batch(work_units, self.pool_size):
            futures = []
            for work_unit in work_units_batch:
                some_future = self.network_pool.spawn(self.session.post, work_unit.post_details.final_url, data=work_unit.post_details.body, headers=work_unit.post_details.headers, timeout=timeout)
                work_unit.add_future(some_future)
                futures.append(some_future)
            gevent.joinall(futures)
            res += self._process_futures(work_units_batch)
        return res

    def process_async_get(self, work, timeout):
        return self.async_get_to_list(work, timeout)

    def process_async_post(self, work, timeout):
        return self.async_post_to_list(work, timeout)

    def _get_http_method_by_type(self, http_method_type):
        return {HTTP_REQUEST.POST: self.session.post, HTTP_REQUEST.GET: self.session.get}[http_method_type]

    def process_async_custom(self, work_units, timeout):
        """
        :param work_units:
        :param timeout:
        :return:    error_code, failure in case at least one of query were problematic in processing
                    list of results, for failed query must be set to None
        """
        err_code = STATUS.SUCCESS
        futures = []
        for work_unit in work_units:
            http_method = self._get_http_method_by_type(work_unit.http_method)
            some_future = self.network_pool.spawn(http_method, work_unit.post_details.final_url, data=work_unit.post_details.body, headers=work_unit.post_details.headers, timeout=timeout)
            work_unit.add_future(some_future)
            futures.append(some_future)
        gevent.joinall(futures)
        res = self._process_futures(work_units)
        return (err_code, res)

@classmethod
def _process_futures(cls, work_units_batch):
    """
            Operate under `WorkUnit` objects after returning from async calls.
            Try to apply job specific constructor method for response returned by exchange.
            In case constructor method fail for any reason - try to wrap all available details into debug string.

        :param work_units_batch:
        :return: array of either object, parsed from exchange responce or error messages as string
        """
    res = []
    for work_unit in work_units_batch:
        if get_logging_level() >= LOG_ALL_DEBUG:
            log_responce(work_unit)
        result = None
        if work_unit.future_value is None or work_unit.future_status_code != HTTP_SUCCESS:
            result = log_responce_cant_be_parsed(work_unit)
            res.append(result)
        else:
            try:
                result = work_unit.method(work_unit.future_value_json, *work_unit.args)
            except Exception as e:
                pass
            if result is not None:
                if type(result) is list:
                    res += result
                else:
                    res.append(result)
            else:
                result = log_responce_cant_be_parsed(work_unit)
                res.append(result)
    return res

# Node: log_responce
# Node: log_responce_cant_be_parsed
def get_ticker(exchange_id, pair_id):
    method = get_ticker_method_by_exchange_id(exchange_id)
    pair_name = get_currency_pair_name_by_exchange_id(pair_id, exchange_id)
    if pair_name is None:
        msg = 'get_ticker for arbitrage - wrong pair_id - {pair_id} for exchange_id = {idd}!'.format(pair_id=pair_id, idd=exchange_id)
        print_to_console(msg, LOG_ALL_ERRORS)
        assert pair_name is None
    return method(pair_name, get_now_seconds_utc())

# Node: get_ticker_method_by_exchange_id
def get_ohlc(date_start, date_end):
    all_ohlc = []
    for pair_name in BITTREX_CURRENCY_PAIRS:
        period = 'thirtyMin'
        all_ohlc += get_ohlc_bittrex(pair_name, date_start, date_end, period)
        sleep_for(1)
    for pair_name in KRAKEN_CURRENCY_PAIRS:
        period = 15
        all_ohlc += get_ohlc_kraken(pair_name, date_start, date_end, period)
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        period = 14400
        all_ohlc += get_ohlc_poloniex(pair_name, date_start, date_end, period)
    for pair_name in BINANCE_CURRENCY_PAIRS:
        period = '15m'
        all_ohlc += get_ohlc_binance(pair_name, date_start, date_end, period)
    for pair_name in HUOBI_CURRENCY_PAIRS:
        period = '15min'
        all_ohlc += get_ohlc_huobi(pair_name, date_start, date_end, period)
    return all_ohlc

# Node: get_ohlc_bittrex
# Node: get_ohlc_kraken
# Node: get_ohlc_poloniex
# Node: get_ohlc_binance
# Node: get_ohlc_huobi
def parse_order_id(exchange_id, json_document):
    method = {EXCHANGE.POLONIEX: parse_order_id_poloniex, EXCHANGE.BITTREX: parse_order_id_bittrex, EXCHANGE.BINANCE: parse_order_id_binance, EXCHANGE.KRAKEN: parse_order_id_kraken, EXCHANGE.HUOBI: parse_order_id_huobi}[exchange_id]
    return method(json_document)

def get_history(prev_time, now_time):
    all_history = []
    for currency in POLONIEX_CURRENCY_PAIRS:
        all_history += get_history_poloniex(currency, prev_time, now_time)
    for currency in KRAKEN_CURRENCY_PAIRS:
        all_history += get_history_kraken(currency, prev_time, now_time)
    for currency in BITTREX_CURRENCY_PAIRS:
        all_history += get_history_bittrex(currency, prev_time, now_time)
    for currency in BINANCE_CURRENCY_PAIRS:
        all_history += get_history_binance(currency, prev_time, now_time)
    for currency in HUOBI_CURRENCY_PAIRS:
        all_history += get_history_huobi(currency, prev_time, now_time)
    return all_history

# Node: get_history_poloniex
# Node: get_history_kraken
# Node: get_history_bittrex
# Node: get_history_binance
# Node: get_history_huobi
def get_balance_huobi(key):
    post_details = get_balance_huobi_post_details(key)
    err_msg = 'check huobi balance called'
    timest = get_now_seconds_utc()
    status_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=HUOBI_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        log_to_file(res, 'balance.log')
    if status_code == STATUS.SUCCESS:
        status_code, res = get_balance_huobi_result_processor(res, timest)
    return (status_code, res)

# Node: get_balance_huobi_post_details
# Node: get_balance_huobi_result_processor
def get_order_history_huobi_post_details(key, pair_name, time_start, time_end):
    """
        NOTE: limit can be used as well
        limit=HUOBI_ORDER_HISTORY_LIMIT
    """
    final_url = HUOBI_API_URL + HUOBI_GET_TRADE_HISTORY + '?'
    ts1 = None
    ts2 = None
    if time_start == 0:
        time_start = time_end - 3600 * 24
    elif time_end - time_start > 3600 * 24:
        msg = 'Huobi allow time range not bigger than 24 hours! start: {} end: {}'.format(time_start, time_end)
        print_to_console(msg, LOG_ALL_ERRORS)
    if 0 < time_start <= time_end:
        ts1 = ts_to_string_utc(time_start, format_string='%Y-%m-%d')
        ts2 = ts_to_string_utc(time_end, format_string='%Y-%m-%d')
    body = init_body(key)
    body.append(('direct', ''))
    if ts1 is None or ts2 is None:
        body.append(('end-date', ''))
    else:
        body.append(('end-date', ts2))
    body.extend([('from', ''), ('size', '')])
    if ts1 is None or ts2 is None:
        body.append(('start-date', ''))
    else:
        body.append(('start-date', ts1))
    body.extend([('states', 'filled,partial-canceled'), ('symbol', pair_name), ('types', '')])
    message = _urlencode(body).encode('utf8')
    msg = 'GET\n{base_url}\n{path}\n{msg1}'.format(base_url=HUOBI_API_ONLY, path=HUOBI_GET_TRADE_HISTORY, msg1=message)
    signature = sign_string_256_base64(key.secret, msg)
    body.append(('Signature', signature))
    final_url += _urlencode(body)
    params = {}
    post_details = PostRequestDetails(final_url, HUOBI_GET_HEADERS, params)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get orders history huobi: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

# Node: init_body
# Node: extend
# Node: sign_string_256_base64
def init_body(key):
    return [('AccessKeyId', key.api_key), ('SignatureMethod', 'HmacSHA256'), ('SignatureVersion', 2), ('Timestamp', ts_to_string_utc(get_now_seconds_utc(), '%Y-%m-%dT%H:%M:%S'))]

def generate_url(key, base_url, path):
    body = [('AccessKeyId', key.api_key), ('SignatureMethod', 'HmacSHA256'), ('SignatureVersion', 2), ('Timestamp', ts_to_string_utc(get_now_seconds_utc(), '%Y-%m-%dT%H:%M:%S'))]
    message = _urlencode(body).encode('utf8')
    msg = 'POST\n{base_url}\n{path}\n{msg1}'.format(base_url=base_url, path=path, msg1=message)
    signature = sign_string_256_base64(key.secret, msg)
    body.append(('Signature', signature))
    return _urlencode(body)

def generate_body_and_url_get_request(key, base_url, path):
    body = [('AccessKeyId', key.api_key), ('SignatureMethod', 'HmacSHA256'), ('SignatureVersion', 2), ('Timestamp', ts_to_string_utc(get_now_seconds_utc(), '%Y-%m-%dT%H:%M:%S'))]
    message = _urlencode(body).encode('utf8')
    msg = 'GET\n{base_url}\n{path}\n{msg1}'.format(base_url=base_url, path=path, msg1=message)
    signature = sign_string_256_base64(key.secret, msg)
    body.append(('Signature', signature))
    return (body, _urlencode(body))

def get_open_orders_huobi_post_details(key, pair_name):
    final_url = HUOBI_API_URL + HUOBI_GET_OPEN_ORDERS + '?'
    body = [('AccessKeyId', key.api_key), ('SignatureMethod', 'HmacSHA256'), ('SignatureVersion', 2), ('Timestamp', ts_to_string_utc(get_now_seconds_utc(), '%Y-%m-%dT%H:%M:%S')), ('direct', ''), ('end_date', ''), ('from', ''), ('size', ''), ('start_date', ''), ('states', 'pre-submitted,submitted,partial-filled'), ('symbol', pair_name), ('types', '')]
    message = _urlencode(body).encode('utf8')
    msg = 'GET\n{base_url}\n{path}\n{msg1}'.format(base_url=HUOBI_API_ONLY, path=HUOBI_GET_OPEN_ORDERS, msg1=message)
    signature = sign_string_256_base64(key.secret, msg)
    body.append(('Signature', signature))
    final_url += _urlencode(body)
    params = {}
    res = PostRequestDetails(final_url, HUOBI_GET_HEADERS, params)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_open_orders_huobi: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def get_balance_binance(key):
    post_details = get_balance_binance_post_details(key)
    err_msg = 'check binance balance called'
    timest = get_now_seconds_utc()
    status_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BINANCE_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        log_to_file(res, 'balance.log')
    if status_code == STATUS.SUCCESS:
        status_code, res = get_balance_binance_result_processor(res, timest)
    return (status_code, res)

# Node: get_balance_binance_post_details
# Node: get_balance_binance_result_processor
def get_balance_kraken(key):
    """
    Example of request and responce
        https://api.kraken.com/0/private/Balance
        {'API-Key': 'whatever',
         'API-Sign': u'whatever'}
        {'nonce': 1508503223939}

    Responce:
    {u'result': {u'DASH': u'33.2402410500', u'BCH': u'22.4980093900', u'ZUSD': u'12747.4370', u'XXBT': u'3.1387700870',
                 u'EOS': u'2450.8822990100', u'USDT': u'77.99709699', u'XXRP': u'0.24804100',
                 u'XREP': u'349.7839715600', u'XETC': u'508.0140331400', u'XETH': u'88.6104554900'}, u'error': []}
    """
    post_details = get_balance_kraken_post_details(key)
    err_msg = 'check kraken balance called'
    timest = get_now_seconds_utc()
    status_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=KRAKEN_NUM_OF_DEAL_RETRY)
    balance = None
    if status_code == STATUS.SUCCESS:
        status_code, balance = get_balance_kraken_result_processor(json_document, timest)
    return (status_code, balance)

# Node: get_balance_kraken_post_details
# Node: get_balance_kraken_result_processor
def get_order_history_kraken(key, pair_name=None, time_start=0, time_end=get_now_seconds_utc()):
    post_details = get_closed_orders_kraken_post_details(key, pair_name, time_start, time_end)
    err_msg = 'check kraken closed orders called'
    error_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=5)
    closed_orders = EMPTY_LIST
    if error_code == STATUS.SUCCESS:
        closed_orders = get_order_history_kraken_result_processor(json_document, pair_name)
    return (error_code, closed_orders)

# Node: get_closed_orders_kraken_post_details
# Node: get_order_history_kraken_result_processor
def get_balance_bittrex(key):
    """
        https://bittrex.com/api/v1.1/account/getbalances?apikey=8a2dd16465b0469197574ec0a516badb&nonce=1508507525325
        {'apisign': 'e6bfb1cc60dcd93d291542cf6c4084e942659be7c363633f710336338a3158b37eb3f999250e5113ffc9e48c18ebe24cf9f4d496f6348a319cbd7f1bc0fc680c'} {}
        {u'message': u'',
        u'result': [{u'Available': 21300.0, u'Currency': u'ARDR', u'Balance': 21300.0, u'Pending': 0.0,
        u'CryptoAddress': u'76730d86115b49b9b7f71578feb35b7da1ca6c13e5f745aa9b630707f5439e68'},

        {u'Available': 49704.04069438, u'Currency': u'BAT', u'Balance': 49704.04069438, u'Pending': 0.0,
        u'CryptoAddress': None},

        {u'Available': 0.0, u'Currency': u'BCC', u'Balance': 0.0, u'Pending': 0.0,
        u'CryptoAddress': u'1H24rzfFWy8thV1AYQch3GByrQQuXA65LY'},

        {u'Available': 0.28912516, u'Currency': u'BTC', u'Balance': 0.28912516, u'Pending': 0.0,
        u'CryptoAddress': u'1EJztGvnKbNj3GeFbt83HhsKeLBYeu8jGq'},

        {u'Available': 0.0, u'Currency': u'BTS', u'Balance': 0.0, u'Pending': 0.0, u'CryptoAddress': u'490d0054055c43ada6e'},

        Added 07.01.2018
        Funny bittrex tend to return this:
        {u'message': u'', u'result': [], u'success': True}
        It will lead to error message - so such case should not be considered as proper response.
    """
    post_details = get_balance_bittrex_post_details(key)
    err_msg = 'check bittrex balance called'
    timest = get_now_seconds_utc()
    status_code, res = send_post_request_with_header(post_details, err_msg, max_tries=BITTREX_NUM_OF_DEAL_RETRY, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        log_to_file(res, DEBUG_LOG_FILE_NAME)
    if status_code == STATUS.SUCCESS:
        status_code, res = get_balance_bittrex_result_processor(res, timest)
    return (status_code, res)

# Node: get_balance_bittrex_post_details
# Node: get_balance_bittrex_result_processor
class ArbitrageListener(ArbitrageWrapper):

    def __init__(self, cfg, app_settings):
        ArbitrageWrapper.__init__(self, cfg)
        self._init_infrastructure(app_settings)

    def start(self):
        self.reset_arbitrage_state()
        while True:
            if self.buy_subscription.is_running() and self.sell_subscription.is_running():
                sleep_for(1)
            else:
                while self.buy_subscription.is_running() or self.sell_subscription.is_running():
                    sleep_for(1)
                self.reset_arbitrage_state()

    def reset_arbitrage_state(self):
        local_timeout = 1
        while True:
            sleep_for(local_timeout)
            log_init_reset()
            set_stage(ORDER_BOOK_SYNC_STAGES.RESETTING)
            self.update_balance_run_flag = False
            self.update_min_cap_run_flag = False
            clear_queue(self.sell_exchange_updates)
            clear_queue(self.buy_exchange_updates)
            self._init_arbitrage_state()
            self.subscribe_to_order_book_update()
            self.sync_order_books()
            log_reset_final_stage()
            if get_stage() != ORDER_BOOK_SYNC_STAGES.AFTER_SYNC:
                self.shutdown_subscriptions()
                log_to_file('reset_arbitrage_state - cant sync order book, lets try one more time!', SOCKET_ERRORS_LOG_FILE_NAME)
                while self.buy_subscription.is_running() or self.sell_subscription.is_running():
                    sleep_for(1)
                local_timeout += 1
            else:
                break
        log_reset_stage_successfully()

    def _init_infrastructure(self, app_settings):
        self.priority_queue, self.msg_queue, self.local_cache = init_queues(app_settings)
        self.processor = ConnectionPool(pool_size=2)
        self.sell_exchange_updates = Queue()
        self.buy_exchange_updates = Queue()
        buy_subscription_constructor = get_subcribtion_by_exchange(self.buy_exchange_id)
        sell_subscription_constructor = get_subcribtion_by_exchange(self.sell_exchange_id)
        self.buy_subscription = buy_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)
        self.sell_subscription = sell_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)

    def _init_arbitrage_state(self):
        self.init_deal_cap()
        self.init_balance_state()
        self.init_order_books()
        self.sell_order_book_synced = False
        self.buy_order_book_synced = False
        set_stage(ORDER_BOOK_SYNC_STAGES.BEFORE_SYNC)

    def init_deal_cap(self):
        self.update_min_cap_run_flag = True

    def update_min_cap(self):
        log_to_file('Subscribing for updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)
        while self.update_min_cap_run_flag:
            update_min_cap(self.cfg, self.deal_cap, self.processor)
            for _ in xrange(self.cap_update_timeout):
                if self.update_min_cap_run_flag:
                    sleep_for(1)
        log_to_file('Exit from updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)

    def init_balance_state(self):
        self.update_balance_run_flag = True

    def init_order_books(self):
        cur_timest_sec = get_now_seconds_utc()
        self.order_book_sell = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.sell_exchange_id)
        self.order_book_buy = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.buy_exchange_id)

    def update_from_queue(self, exchange_id, order_book, queue):
        while True:
            if not self.buy_subscription.is_running() or not self.sell_subscription.is_running():
                return STATUS.FAILURE
            try:
                order_book_update = queue.get(block=False)
            except:
                order_book_update = None
            if order_book_update is None:
                break
            if STATUS.SUCCESS != order_book.update(exchange_id, order_book_update):
                return STATUS.FAILURE
            queue.task_done()
        return STATUS.SUCCESS

    def sync_sell_order_book(self):
        if self.sell_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
            self.order_book_sell = get_order_book(self.sell_exchange_id, self.pair_id)
            if self.order_book_sell is None:
                return
            self.order_book_sell.sort_by_price()
            if STATUS.FAILURE == self.update_from_queue(self.sell_exchange_id, self.order_book_sell, self.sell_exchange_updates):
                self.sell_order_book_synced = False
                return
        log_finishing_syncing_order_book('SELL')
        self.sell_order_book_synced = True

    def sync_buy_order_book(self):
        if self.buy_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
            self.order_book_buy = get_order_book(self.buy_exchange_id, self.pair_id)
            if self.order_book_buy is None:
                return
            self.order_book_buy.sort_by_price()
            if STATUS.FAILURE == self.update_from_queue(self.buy_exchange_id, self.order_book_buy, self.buy_exchange_updates):
                self.buy_order_book_synced = False
                return
        log_finishing_syncing_order_book('BUY')
        self.buy_order_book_synced = True

    def sync_order_books(self):
        msg = 'sync_order_books - stage status is {}'.format(get_stage())
        log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
        sync_sell_order_book_thread = start_process_daemon(self.sync_sell_order_book, args=())
        sync_buy_order_book_thread = start_process_daemon(self.sync_buy_order_book, args=())
        sync_sell_order_book_thread.join()
        sync_buy_order_book_thread.join()
        if self.sell_order_book_synced and self.buy_order_book_synced:
            set_stage(ORDER_BOOK_SYNC_STAGES.AFTER_SYNC)
        log_all_order_book_synced()

    def subscribe_cap_update(self):
        start_process_daemon(self.update_min_cap, args=())

    def update_balance(self):
        while self.update_balance_run_flag:
            cur_timest_sec = get_now_seconds_utc()
            self.balance_state = get_updated_balance_arbitrage(cfg, self.balance_state, self.local_cache)
            if self.balance_state.expired(cur_timest_sec, self.buy_exchange_id, self.sell_exchange_id, BALANCE_EXPIRED_THRESHOLD):
                log_balance_expired_errors(cfg, self.msg_queue, self.balance_state)
                assert False
            sleep_for(self.balance_update_timeout)

    def subscribe_balance_update(self):
        start_process_daemon(self.update_balance, args=())

    def subscribe_to_order_book_update(self):
        start_process_daemon(self.buy_subscription.subscribe, args=())
        start_process_daemon(self.sell_subscription.subscribe, args=())

    def shutdown_subscriptions(self):
        self.sell_subscription.disconnect()
        self.buy_subscription.disconnect()

    def on_order_book_update(self, exchange_id, order_book_updates):
        """
        :param exchange_id:
        :param order_book_updates:  parsed OrderBook or OrderBookUpdates according to exchange specs
        :param stage:               whether BOTH orderbook synced or NOT
        :return:
        """
        exchange_name = get_exchange_name_by_id(exchange_id)
        print_to_console('Got update for {exch} Current number of threads: {thr_num}'.format(exch=exchange_name, thr_num=threading.active_count()), LOG_ALL_ERRORS)
        current_stage = get_stage()
        if not self.buy_subscription.is_running() or not self.sell_subscription.is_running():
            log_one_of_subscriptions_failed(self.buy_subscription.is_running(), self.sell_subscription.is_running(), current_stage)
            self.shutdown_subscriptions()
            return
        if order_book_updates is None:
            print_to_console('Order book update is NONE! for {}'.format(exchange_name), LOG_ALL_ERRORS)
            return
        if current_stage == ORDER_BOOK_SYNC_STAGES.BEFORE_SYNC:
            print_to_console('Syncing in progress ...', LOG_ALL_ERRORS)
            if exchange_id == self.buy_exchange_id:
                if self.buy_order_book_synced:
                    order_book_update_status = self.order_book_buy.update(exchange_id, order_book_updates)
                    if order_book_update_status == STATUS.FAILURE:
                        log_order_book_update_failed_pre_sync('BUY', exchange_id, order_book_updates)
                        self.shutdown_subscriptions()
                else:
                    self.buy_exchange_updates.put(order_book_updates)
            elif self.sell_order_book_synced:
                order_book_update_status = self.order_book_sell.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_pre_sync('SELL', exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
            else:
                self.sell_exchange_updates.put(order_book_updates)
        elif current_stage == ORDER_BOOK_SYNC_STAGES.AFTER_SYNC:
            print_to_console('Update after syncing... {}'.format(exchange_name), LOG_ALL_ERRORS)
            if exchange_id == self.buy_exchange_id:
                order_book_update_status = self.order_book_buy.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_post_sync(exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
                    return
            else:
                order_book_update_status = self.order_book_sell.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_post_sync(exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
                    return
            print_top10(exchange_id, self.order_book_buy, self.order_book_sell)
            if not YES_I_KNOW_WHAT_AM_I_DOING:
                die_hard('LIVE TRADING!')
                ts1 = get_now_seconds_utc_ms()
                status_code, deal_pair = search_for_arbitrage(self.order_book_sell, self.order_book_buy, self.threshold, self.balance_threshold, init_deals_with_logging_speedy, self.balance_state, self.deal_cap, type_of_deal=DEAL_TYPE.ARBITRAGE, worker_pool=self.processor, msg_queue=self.msg_queue)
                ts2 = get_now_seconds_utc_ms()
                msg = 'Start: {ts1} ms End: {ts2} ms Runtime: {d} ms'.format(ts1=ts1, ts2=ts2, d=ts2 - ts1)
                log_to_file(msg, 'profile.txt')
                add_orders_to_watch_list(deal_pair, self.priority_queue)
            self.deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)

def sync_sell_order_book(self):
    if self.sell_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
        self.order_book_sell = get_order_book(self.sell_exchange_id, self.pair_id)
        if self.order_book_sell is None:
            return
        self.order_book_sell.sort_by_price()
        if STATUS.FAILURE == self.update_from_queue(self.sell_exchange_id, self.order_book_sell, self.sell_exchange_updates):
            self.sell_order_book_synced = False
            return
    log_finishing_syncing_order_book('SELL')
    self.sell_order_book_synced = True

# Node: get_order_book
# Node: update_from_queue
# Node: log_finishing_syncing_order_book
def sync_buy_order_book(self):
    if self.buy_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
        self.order_book_buy = get_order_book(self.buy_exchange_id, self.pair_id)
        if self.order_book_buy is None:
            return
        self.order_book_buy.sort_by_price()
        if STATUS.FAILURE == self.update_from_queue(self.buy_exchange_id, self.order_book_buy, self.buy_exchange_updates):
            self.buy_order_book_synced = False
            return
    log_finishing_syncing_order_book('BUY')
    self.buy_order_book_synced = True

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

def test_balance_retrieval(self):
    status, balance = get_balance_poloniex(self.poloniex_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_poloniex
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

def test_balance_retrieval(self):
    status, balance = get_balance_kraken(self.kraken_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_kraken
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

def test_balance_retrieval(self):
    status, balance = get_balance_bittrex(self.bittrex_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_bittrex
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

def test_balance_retrieval(self):
    status, balance = get_balance_huobi(self.huobi_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_huobi
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

def test_balance_retrieval(self):
    status, balance = get_balance_binance(self.binance_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_binance
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

# Node: get_order_book_binance
def test_binance_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in BINANCE_CURRENCY_PAIRS:
        trade_history = get_history_binance(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

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

# Node: get_order_book_bittrex
def test_bittrex_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in BITTREX_CURRENCY_PAIRS:
        trade_history = get_history_bittrex(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

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

# Node: get_order_book_huobi
def test_huobi_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in HUOBI_CURRENCY_PAIRS:
        trade_history = get_history_huobi(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

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

# Node: get_order_book_kraken
def test_kraken_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in KRAKEN_CURRENCIES:
        trade_history = get_history_kraken(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

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

# Node: get_order_book_poloniex
def test_poloniex_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        trade_history = get_history_poloniex(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

def update_min_cap(cfg, deal_cap, processor):
    cur_timest_sec = get_now_seconds_utc()
    tickers = get_ticker_for_arbitrage(cfg.pair_id, cur_timest_sec, [cfg.buy_exchange_id, cfg.sell_exchange_id], processor)
    new_cap = compute_new_min_cap_from_tickers(cfg.pair_id, tickers)
    if new_cap > 0:
        msg = 'Updating old cap {op}'.format(op=deal_cap)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)
        deal_cap.update_min_volume_cap(new_cap, cur_timest_sec)
        msg = 'New cap {op}'.format(op=deal_cap)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)
    else:
        msg = "CAN'T update minimum_volume_cap for {pair_id} at following\n        exchanges: {exch1} {exch2}".format(pair_id=cfg.pair_id, exch1=get_exchange_name_by_id(cfg.buy_exchange_id), exch2=get_exchange_name_by_id(cfg.sell_exchange_id))
        print_to_console(msg, LOG_ALL_ERRORS)
        log_to_file(msg, cfg.log_file_name)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)

# Node: get_ticker_for_arbitrage
# Node: compute_new_min_cap_from_tickers
# Node: update_min_volume_cap
