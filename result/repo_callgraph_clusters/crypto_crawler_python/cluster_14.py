# Cluster 14

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

# Node: log_subscribe_to_exchange_heartbeat
# Node: send
# Node: sleep_for
# Node: log_send_heart_beat_failed
# Node: log_unsubscribe_to_exchange_heartbeat
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

# Node: enableTrace
# Node: create_connection
# Node: settimeout
# Node: disconnect
# Node: log_conect_to_websocket
# Node: recv
# Node: on_public
# Node: log_error_on_receive_from_socket
# Node: log_heartbeat_is_missing
# Node: log_subscription_cancelled
def get_cache(host=CACHE_HOST, port=CACHE_PORT):
    if LOCAL_CACHE is None:
        return connect_to_cache(host, port)
    return LOCAL_CACHE

# Node: connect_to_cache
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

# Node: on_open
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

def _init_infrastructure(self, app_settings):
    self.priority_queue, self.msg_queue, self.local_cache = init_queues(app_settings)
    self.processor = ConnectionPool(pool_size=2)
    self.sell_exchange_updates = Queue()
    self.buy_exchange_updates = Queue()
    buy_subscription_constructor = get_subcribtion_by_exchange(self.buy_exchange_id)
    sell_subscription_constructor = get_subcribtion_by_exchange(self.sell_exchange_id)
    self.buy_subscription = buy_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)
    self.sell_subscription = sell_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)

# Node: init_queues
# Node: ConnectionPool
# Node: Queue
# Node: get_subcribtion_by_exchange
# Node: buy_subscription_constructor
# Node: sell_subscription_constructor
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
def load_order_books(args):
    """
        Periodically retrieve FULL order books
        from ALL supported exchanges via REST api
        and save it for further analysis in DB.

        Under the hood requests are sent in async fashion via gevent library

    :param args: config file
    :return:
    """
    pg_conn, _ = process_args(args)
    processor = ConnectionPool()
    while True:
        ts = get_now_seconds_utc()
        results = get_order_book_speedup(ts, processor)
        order_book = filter(lambda x: type(x) != str, results)
        load_to_postgres(order_book, ORDER_BOOK_TYPE_NAME, pg_conn)
        order_book_size = len(order_book)
        order_book_ask_size = 0
        order_book_bid_size = 0
        for entry in order_book:
            if entry is not None:
                order_book_ask_size += len(entry.ask)
                order_book_bid_size += len(entry.bid)
        if should_print_debug():
            msg = 'Orderbook retrieval at {tt}:\n            Order book size - {num1} Order book asks - {num10} Order book bids - {num20}'.format(tt=ts, num1=order_book_size, num10=order_book_ask_size, num20=order_book_bid_size)
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'order_book.log')
        print_to_console('Before sleep...', LOG_ALL_ERRORS)
        sleep_for(ORDER_BOOK_POLL_TIMEOUT)

# Node: get_order_book_speedup
# Node: filter
# Node: load_to_postgres
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
def load_all_public_data(args):
    """
                06.08.2019 As far as I remember it is NOT main data retrieval routine

                Retrieve ticker, trade history, candles and order book
                from ALL supported exchanges
                and store it within DB
                every TIMEOUT seconds through REST api.

                Majority of exchanges tend to throttle clients who send too many requests
                from the same ip - so be mindful about timeout.

    :param args:
    :return:
    """
    pg_conn, settings = process_args(args)
    processor = ConnectionPool()

    def split_on_errors(raw_response):
        valid_objects = filter(lambda x: type(x) != str, raw_response)
        error_strings = filter(lambda x: type(x) != str, raw_response)
        return (valid_objects, error_strings)
    while True:
        end_time = get_now_seconds_utc()
        start_time = end_time - POLL_PERIOD_SECONDS
        candles, errs = split_on_errors(get_ohlc_speedup(start_time, end_time, processor))
        bulk_insert_to_postgres(pg_conn, Candle.table_name, Candle.columns, candles)
        trade_history, errs = split_on_errors(get_history_speedup(start_time, end_time, processor))
        bulk_insert_to_postgres(pg_conn, TradeHistory.table_name, TradeHistory.columns, trade_history)
        tickers, errs = split_on_errors(get_ticker_speedup(end_time, processor))
        bulk_insert_to_postgres(pg_conn, Ticker.table_name, Ticker.columns, tickers)
        if should_print_debug():
            msg = 'History retrieval at {ts}:\n                Candle size - {num}\n                Ticker size - {num3}\n                Trade history size - {num2}\n                '.format(ts=end_time, num=len(candles), num3=len(tickers), num2=len(trade_history))
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'candles_trade_history.log')
        print_to_console('Before sleep...', LOG_ALL_ERRORS)
        sleep_for(POLL_PERIOD_SECONDS)

def split_on_errors(raw_response):
    valid_objects = filter(lambda x: type(x) != str, raw_response)
    error_strings = filter(lambda x: type(x) != str, raw_response)
    return (valid_objects, error_strings)

# Node: split_on_errors
# Node: get_ohlc_speedup
# Node: bulk_insert_to_postgres
# Node: get_history_speedup
# Node: get_ticker_speedup
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
def analyse_tickers(pg_connection, notify_queue):
    """
            Retrieve tickers from ALL exchanges via REST api and save into DB.

            NOTE: Very first routine to analyse gap between rates at different exchanges.

    :param pg_connection:
    :param notify_queue:
    :return:
    """
    processor = ConnectionPool()
    while True:
        timest = get_now_seconds_utc()
        results = get_ticker_speedup(timest, processor)
        tickers = filter(lambda x: type(x) != str, results)
        res = compare_price(tickers, TRIGGER_THRESHOLD, check_highest_bid_bigger_than_lowest_ask)
        for entry in res:
            msg = 'Condition: {msg} at {ts}\n            Date: {dt}\n            Pair: {pair_name}, {ask_exchange}: {ask_price:.7f} {sell_exchange}: {sell_price:.7f}\n            TAG: {ask_exchange}-{sell_exchange}\n            '.format(msg=entry[0], ts=timest, dt=ts_to_string_local(timest), pair_name=get_pair_name_by_id(entry[1]), ask_exchange=entry[2].exchange, ask_price=entry[2].bid, sell_exchange=entry[3].exchange, sell_price=entry[3].ask)
            print_to_console(msg, LOG_ALL_ERRORS)
            notify_queue.add_message(ARBITRAGE_MSG, msg)
            save_alarm_into_pg(entry[2], entry[3], pg_connection)
        print_to_console('Total amount of tickers = {num}'.format(num=len(tickers)), LOG_ALL_DEBUG)
        load_to_postgres(tickers, TICKER_TYPE_NAME, pg_connection)
        print_to_console('Before sleep...', LOG_ALL_DEBUG)
        sleep_for(POLL_PERIOD_SECONDS)

# Node: compare_price
# Node: save_alarm_into_pg
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

