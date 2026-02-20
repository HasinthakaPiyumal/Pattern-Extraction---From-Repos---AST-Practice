# Cluster 26

# Node: split
def start_process_daemon(method, args):
    new_thread = threading.Thread(target=method, args=args)
    new_thread.daemon = True
    new_thread.start()
    return new_thread

# Node: Thread
# Node: start
def parse_exchange_ids(exchange_list):
    ids_list = [x.strip() for x in exchange_list.split(',') if x.strip()]
    exchanges_ids = []
    for exchange_name in ids_list:
        new_exchange_id = get_exchange_id_by_name(exchange_name)
        if new_exchange_id in EXCHANGE.values():
            exchanges_ids.append(new_exchange_id)
        else:
            log_wrong_exchange_id(new_exchange_id)
            assert new_exchange_id in EXCHANGE.values()
    return exchanges_ids

# Node: strip
# Node: get_exchange_id_by_name
# Node: log_wrong_exchange_id
def process_args(args):
    settings = CommonSettings.from_cfg(args.cfg)
    pg_conn = init_pg_connection(_db_host=settings.db_host, _db_port=settings.db_port, _db_name=settings.db_name)
    set_log_folder(settings.log_folder)
    set_logging_level(settings.logging_level_id)
    return (pg_conn, settings)

# Node: from_cfg
# Node: init_pg_connection
# Node: set_log_folder
def init_queues(app_settings):
    priority_queue = get_priority_queue(host=app_settings.cache_host, port=app_settings.cache_port)
    msg_queue = get_message_queue(host=app_settings.cache_host, port=app_settings.cache_port)
    local_cache = get_cache(host=app_settings.cache_host, port=app_settings.cache_port)
    return (priority_queue, msg_queue, local_cache)

# Node: get_priority_queue
# Node: get_message_queue
class ArbitrageWrapper(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.update_balance_run_flag = False
        self.update_min_cap_run_flag = False
        self.deal_cap = MarketCap(self.pair_id, get_now_seconds_utc())
        self.deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)
        self.update_min_cap_run_flag = False
        self.balance_state = dummy_balance_init(timest=0, default_volume=100500, default_available_volume=100500)
        self.update_balance_run_flag = False
        self.order_book_buy = None
        self.buy_order_book_synced = False
        self.order_book_sell = None
        self.sell_order_book_synced = False

    @property
    def buy_exchange_id(self):
        return self.cfg.buy_exchange_id

    @property
    def sell_exchange_id(self):
        return self.cfg.sell_exchange_id

    @property
    def pair_id(self):
        return self.cfg.pair_id

    @property
    def log_file_name(self):
        return self.cfg.log_file_name

    @property
    def threshold(self):
        return self.cfg.threshold

    @property
    def reverse_threshold(self):
        return self.cfg.reverse_threshold

    @property
    def balance_threshold(self):
        return self.cfg.balance_threshold

    @property
    def cap_update_timeout(self):
        return self.cfg.cap_update_timeout

    @property
    def balance_update_timeout(self):
        return self.cfg.balance_update_timeout

def __init__(self, cfg):
    self.cfg = cfg
    self.update_balance_run_flag = False
    self.update_min_cap_run_flag = False
    self.deal_cap = MarketCap(self.pair_id, get_now_seconds_utc())
    self.deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)
    self.update_min_cap_run_flag = False
    self.balance_state = dummy_balance_init(timest=0, default_volume=100500, default_available_volume=100500)
    self.update_balance_run_flag = False
    self.order_book_buy = None
    self.buy_order_book_synced = False
    self.order_book_sell = None
    self.sell_order_book_synced = False

# Node: MarketCap
# Node: update_max_volume_cap
# Node: dummy_balance_init
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

def update(self, exchange_id, order_book_delta):
    method = {EXCHANGE.POLONIEX: self.update_for_poloniex, EXCHANGE.BITTREX: self.update_for_bittrex, EXCHANGE.BINANCE: self.update_for_binance, EXCHANGE.HUOBI: self.update_for_huobi}[exchange_id]
    return method(order_book_delta)

# Node: method
# Node: sleep_for
# Node: disconnect
def get_cache(host=CACHE_HOST, port=CACHE_PORT):
    if LOCAL_CACHE is None:
        return connect_to_cache(host, port)
    return LOCAL_CACHE

# Node: connect_to_cache
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
def parse_order_id(exchange_id, json_document):
    method = {EXCHANGE.POLONIEX: parse_order_id_poloniex, EXCHANGE.BITTREX: parse_order_id_bittrex, EXCHANGE.BINANCE: parse_order_id_binance, EXCHANGE.KRAKEN: parse_order_id_kraken, EXCHANGE.HUOBI: parse_order_id_huobi}[exchange_id]
    return method(json_document)

def watch_balance_for_exchange(args):
    """
            Those routine update balance at redis CACHE
            for ALL coins at ONE exchange for active key set.

            NOTE:   It still rely on REST api - i.e. not proactive
                    For some exchanges - balance not immediately updated

                    Initially all exchanges were polled sequentially
                    But it lead to delays in the past
                    due to exchange errors or throttling

    :param args: config file and exchange_id
    :return:
    """
    settings = CommonSettings.from_cfg(args.cfg)
    exchange_id = get_exchange_id_by_name(args.exchange)
    if exchange_id not in EXCHANGE.values():
        log_wrong_exchange_id(exchange_id)
        die_hard('Exchange id {} seems to be unknown? 0_o'.format(exchange_id))
    log_initial_settings('Starting balance monitoring for following exchange: \n', [exchange_id])
    cache = connect_to_cache(host=settings.cache_host, port=settings.cache_port)
    msg_queue = get_message_queue(host=settings.cache_host, port=settings.cache_port)
    load_keys(settings.key_path)
    set_log_folder(settings.log_folder)
    set_logging_level(settings.logging_level_id)
    init_balances(settings.exchanges, cache)
    cnt = 0
    while True:
        sleep_for(BALANCE_POLL_TIMEOUT)
        cnt += BALANCE_POLL_TIMEOUT
        log_balance_update_heartbeat(exchange_id)
        balance_for_exchange = update_balance_by_exchange(exchange_id, cache)
        while balance_for_exchange is None:
            log_cant_update_balance(exchange_id)
            sleep_for(1)
            balance_for_exchange = update_balance_by_exchange(exchange_id, cache)
        if cnt >= BALANCE_HEALTH_CHECK_TIMEOUT:
            cnt = 0
            log_last_balances(settings.exchanges, cache, msg_queue)
            for base_currency_id in BASE_CURRENCY:
                threshold = BASE_CURRENCIES_BALANCE_THRESHOLD[base_currency_id]
                if not balance_for_exchange.do_we_have_enough(base_currency_id, threshold):
                    log_not_enough_base_currency(exchange_id, base_currency_id, threshold, balance_for_exchange, msg_queue)

# Node: log_initial_settings
# Node: load_keys
# Node: init_balances
# Node: log_balance_update_heartbeat
# Node: log_cant_update_balance
# Node: log_last_balances
# Node: log_not_enough_base_currency
# Node: init_queues
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

def update_min_cap(self):
    log_to_file('Subscribing for updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)
    while self.update_min_cap_run_flag:
        update_min_cap(self.cfg, self.deal_cap, self.processor)
        for _ in xrange(self.cap_update_timeout):
            if self.update_min_cap_run_flag:
                sleep_for(1)
    log_to_file('Exit from updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)

# Node: update_min_cap
# Node: xrange
def update_balance(self):
    while self.update_balance_run_flag:
        cur_timest_sec = get_now_seconds_utc()
        self.balance_state = get_updated_balance_arbitrage(cfg, self.balance_state, self.local_cache)
        if self.balance_state.expired(cur_timest_sec, self.buy_exchange_id, self.sell_exchange_id, BALANCE_EXPIRED_THRESHOLD):
            log_balance_expired_errors(cfg, self.msg_queue, self.balance_state)
            assert False
        sleep_for(self.balance_update_timeout)

# Node: get_updated_balance_arbitrage
# Node: expired
# Node: log_balance_expired_errors
def shutdown_subscriptions(self):
    self.sell_subscription.disconnect()
    self.buy_subscription.disconnect()

def arbitrage_between_pair(args):
    cfg = ArbitrageConfig.from_args(args)
    app_settings = CommonSettings.from_cfg(args.cfg)
    set_logging_level(app_settings.logging_level_id)
    set_log_folder(app_settings.log_folder)
    load_keys(app_settings.key_path)
    priority_queue, msg_queue, local_cache = init_queues(app_settings)
    processor = ConnectionPool(pool_size=2)
    for exchange_id in [args.sell_exchange_id, args.buy_exchange_id]:
        pair_name = get_currency_pair_name_by_exchange_id(cfg.pair_id, exchange_id)
        if pair_name is None:
            log_dont_supported_currency(cfg, exchange_id, cfg.pair_id)
            exit()
    deal_cap = MarketCap(cfg.pair_id, get_now_seconds_utc())
    deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)
    update_min_cap(cfg, deal_cap, processor)
    balance_state = dummy_balance_init(timest=0, default_volume=Decimal('0'), default_available_volume=Decimal('0'))
    if not YES_I_KNOW_WHAT_AM_I_DOING:
        die_hard('LIVE TRADING!')
    while True:
        if get_now_seconds_utc() - deal_cap.last_updated > MIN_CAP_UPDATE_TIMEOUT:
            update_min_cap(cfg, deal_cap, processor)
        for mode_id in [DEAL_TYPE.ARBITRAGE, DEAL_TYPE.REVERSE]:
            cur_timest_sec = get_now_seconds_utc()
            method = search_for_arbitrage if mode_id == DEAL_TYPE.ARBITRAGE else adjust_currency_balance
            active_threshold = cfg.threshold if mode_id == DEAL_TYPE.ARBITRAGE else cfg.reverse_threshold
            balance_state = get_updated_balance_arbitrage(cfg, balance_state, local_cache)
            if balance_state.expired(cur_timest_sec, cfg.buy_exchange_id, cfg.sell_exchange_id, BALANCE_EXPIRED_THRESHOLD):
                log_balance_expired_errors(cfg, msg_queue, balance_state)
                die_hard('Balance expired')
            order_book_src, order_book_dst = get_order_books_for_arbitrage_pair(cfg, cur_timest_sec, processor)
            if order_book_dst is None or order_book_src is None:
                log_failed_to_retrieve_order_book(cfg)
                sleep_for(3)
                continue
            if is_order_books_expired(order_book_src, order_book_dst, local_cache, msg_queue, cfg.log_file_name):
                sleep_for(3)
                continue
            local_cache.cache_order_book(order_book_src)
            local_cache.cache_order_book(order_book_dst)
            status_code, deal_pair = method(order_book_src, order_book_dst, active_threshold, cfg.balance_threshold, init_deals_with_logging_speedy, balance_state, deal_cap, type_of_deal=mode_id, worker_pool=processor, msg_queue=msg_queue)
            add_orders_to_watch_list(deal_pair, priority_queue)
            print_to_console('I am still alive! ', LOG_ALL_DEBUG)
            sleep_for(2)
        sleep_for(3)
        deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)

# Node: from_args
# Node: log_dont_supported_currency
# Node: exit
# Node: get_order_books_for_arbitrage_pair
# Node: log_failed_to_retrieve_order_book
# Node: is_order_books_expired
# Node: cache_order_book
def process_placed_orders(args):
    """
            Check for new orders placed by ANY of trading bots


    :param args:
    :return:
    """
    pg_conn, settings = process_args(args)
    msg_queue = get_message_queue(host=settings.cache_host, port=settings.cache_port)
    cnt = 0
    while True:
        order = msg_queue.get_next_order(ORDERS_MSG)
        if order is not None:
            save_order_into_pg(order, pg_conn)
            print_to_console('Saving {} in db'.format(order), LOG_ALL_ERRORS)
        sleep_for(1)
        cnt += 1
        if cnt >= HEARTBEAT_TIMEOUT:
            cnt = 0
            print_to_console('Order storing heartbeat', LOG_ALL_ERRORS)

# Node: process_args
# Node: get_next_order
# Node: save_order_into_pg
def forward_new_messages(args):
    settings = CommonSettings.from_cfg(args.cfg)
    set_log_folder(settings.log_folder)
    set_logging_level(settings.logging_level_id)
    msg_queue = get_message_queue(host=settings.cache_host, port=settings.cache_port)
    do_we_have_data = False
    while True:
        for topic_id in QUEUE_TOPICS:
            msg = msg_queue.get_message_nowait(topic_id)
            if msg is not None:
                do_we_have_data = True
                notification_id = get_notification_id_by_topic_name(topic_id)
                err_code = send_single_message(msg, notification_id)
                if err_code == STATUS.FAILURE:
                    err_msg = "telegram_notifier can't send message to telegram. Message will be re-processed on next iteration.\n                        {msg}".format(msg=msg)
                    log_to_file(err_msg, 'telegram_notifier.log')
                    print_to_console(err_msg, LOG_ALL_ERRORS)
                    msg_queue.add_message_to_start(topic_id, msg)
                    sleep_for(1)
        if not do_we_have_data:
            sleep_for(1)
        do_we_have_data = False

# Node: get_message_nowait
# Node: get_notification_id_by_topic_name
# Node: send_single_message
# Node: add_message_to_start
def process_failed_orders(args):
    """
                We try to address following issue

            Due to network issue or just bugs we may end up in situation that we are failed to place order
            Or we think so. Such orders registered in dedicated queue. We want to re-process them
            to minimise loss.

            Option 1: We managed to place order, just didn't get proper response from exchange
            - i.e. didn't wait enough for exchange to response
            Option 2: We managed to place order, just exchange were overloaded and decided to
            return to us some errors ()
            Option 3: We didn't managed to place order
                nonce issue - particular poloniex
                exchange issue - kraken
                ill fate - :(
            Option 4: ??? TODO

            First we try to find order in open or executed.
            In case we find it - update order_id in db.
            If it still open add it to watch list for expired orders processing.

            If not we can replace it by market with idea that there is high probability that other arbitrage deal were
            successfully placed

    :param args:
    :return:
    """
    pg_conn, settings = process_args(args)
    load_keys(settings.key_path)
    priority_queue, msg_queue, local_cache = init_queues(settings)
    cnt = 0
    while True:
        order = msg_queue.get_next_order(FAILED_ORDERS_MSG)
        if order is not None:
            process_failed_order(order, msg_queue, priority_queue, local_cache, pg_conn)
        sleep_for(1)
        cnt += 1
        if cnt >= HEARTBEAT_TIMEOUT:
            cnt = 0
            print_to_console('Failed orders processing heartbeat', LOG_ALL_ERRORS)

# Node: process_failed_order
def load_trade_history(args):
    """
        Retrieve executed trades from ALL exchanges via REST api
        and save into db

        Those data later will be used for analysis
        of profitability of trading and bot's performance

    :param args: period, exchanges, connection details
    :return:
    """
    pg_conn, settings = process_args(args)
    log_initial_settings('Starting trade history retrieval for bots using following exchanges: \n', settings.exchanges)
    if args.start_time is None or args.end_time is None:
        end_time = get_now_seconds_utc()
        start_time = end_time - 24 * 3600
    else:
        end_time = parse_time(args.end_time, '%Y-%m-%d %H:%M:%S')
        start_time = parse_time(args.start_time, '%Y-%m-%d %H:%M:%S')
    if start_time == end_time or end_time <= start_time:
        die_hard('Wrong time interval provided! {ts0} - {ts1}'.format(ts0=start_time, ts1=end_time))
    load_keys(settings.key_path)
    while True:
        for exchange_id in settings.exchanges:
            method = get_trade_retrieval_method_by_exchange(exchange_id)
            method(pg_conn, start_time, end_time)
            sleep_for(1)
        print_to_console('Trade retrieval heartbeat', LOG_ALL_DEBUG)
        sleep_for(TRADE_POLL_TIMEOUT)
        end_time = get_now_seconds_utc()
        start_time = end_time - 24 * 3600

# Node: get_trade_retrieval_method_by_exchange
def process_expired_orders(args):
    """

    :param args: file name
    :return:
    """
    settings = CommonSettings.from_cfg(args.cfg)
    set_log_folder(settings.log_folder)
    set_logging_level(settings.logging_level_id)
    load_keys(settings.key_path)
    priority_queue, msg_queue, local_cache = init_queues(settings)
    cnt = 0
    while True:
        curr_ts = get_now_seconds_utc()
        order = priority_queue.get_oldest_order(ORDERS_EXPIRE_MSG)
        if order:
            msg = 'Current expired order - {}'.format(order)
            log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)
            order_age = curr_ts - order.create_time
            if order_age < ORDER_EXPIRATION_TIMEOUT:
                msg = 'A bit early - {t1} {t2} WILLL SLEEP'.format(t1=order_age, t2=ORDER_EXPIRATION_TIMEOUT)
                log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)
                sleep_for(ORDER_EXPIRATION_TIMEOUT - order_age)
            process_expired_order(order, msg_queue, priority_queue, local_cache)
        sleep_for(1)
        cnt += 1
        if cnt >= HEARTBEAT_TIMEOUT:
            cnt = 0
            print_to_console('Watch list is empty sleeping', LOG_ALL_ERRORS)
            log_to_file('Watch list is empty sleeping', EXPIRED_ORDER_PROCESSING_FILE_NAME)

# Node: get_oldest_order
# Node: process_expired_order
def register_and_wait_for_commands(args):
    settings = CommonSettings.from_cfg(args.cfg)
    command_queue = CommandQueue(settings.cache_host, settings.cache_port)
    server_name = socket.gethostname()
    command_queue.register_node(server_name)
    while True:
        cmd = command_queue.get_command()
        if cmd:
            print_to_console('Subscriber: {} - {}'.format(server_name, cmd), LOG_ALL_DEBUG)
        sleep_for(1)

# Node: CommandQueue
# Node: gethostname
# Node: register_node
# Node: get_command
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

def test_socket_subscription(self):
    t1 = SubscriptionBittrex(CURRENCY_PAIR.BTC_TO_ETC)
    buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
    buy_subscription_thread.daemon = True
    buy_subscription_thread.start()
    sleep_for(5)
    self.assertTrue(t1.should_run)
    t1.disconnect()
    self.assertFalse(t1.should_run)

# Node: SubscriptionBittrex
# Node: assertFalse
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

def test_socket_subscription(self):
    t1 = SubscriptionPoloniex(CURRENCY_PAIR.BTC_TO_ETC)
    buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
    buy_subscription_thread.daemon = True
    buy_subscription_thread.start()
    sleep_for(5)
    self.assertTrue(t1.should_run)
    t1.disconnect()
    self.assertFalse(t1.should_run)

# Node: SubscriptionPoloniex
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

def test_socket_subscription(self):
    t1 = SubscriptionHuobi(CURRENCY_PAIR.BTC_TO_ETC)
    buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
    buy_subscription_thread.daemon = True
    buy_subscription_thread.start()
    sleep_for(5)
    self.assertTrue(t1.should_run)
    t1.disconnect()
    self.assertFalse(t1.should_run)

# Node: SubscriptionHuobi
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

def test_socket_subscription(self):
    t1 = SubscriptionBinance(CURRENCY_PAIR.BTC_TO_ETC)
    buy_subscription_thread = threading.Thread(target=t1.subscribe, args=())
    buy_subscription_thread.daemon = True
    buy_subscription_thread.start()
    sleep_for(5)
    self.assertTrue(t1.should_run)
    t1.disconnect()
    self.assertFalse(t1.should_run)

# Node: SubscriptionBinance
class ExchangeArbitrageSettings(BaseData):

    def __init__(self, src_exchange_name, dst_exchange_name, list_of_pairs):
        self.src_exchange_name = src_exchange_name
        self.src_exchange_id = get_exchange_id_by_name(self.src_exchange_name)
        self.dst_exchange_name = dst_exchange_name
        self.dst_exchange_id = get_exchange_id_by_name(self.dst_exchange_name)
        self.list_of_pairs = list_of_pairs

def __init__(self, src_exchange_name, dst_exchange_name, list_of_pairs):
    self.src_exchange_name = src_exchange_name
    self.src_exchange_id = get_exchange_id_by_name(self.src_exchange_name)
    self.dst_exchange_name = dst_exchange_name
    self.dst_exchange_id = get_exchange_id_by_name(self.dst_exchange_name)
    self.list_of_pairs = list_of_pairs

