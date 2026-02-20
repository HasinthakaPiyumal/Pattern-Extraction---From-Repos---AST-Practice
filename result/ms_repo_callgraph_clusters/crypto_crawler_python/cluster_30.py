# Cluster 30

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

