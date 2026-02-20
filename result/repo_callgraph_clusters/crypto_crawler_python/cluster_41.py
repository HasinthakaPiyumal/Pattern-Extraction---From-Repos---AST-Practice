# Cluster 41

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

# Node: process_message
# Node: parse_socket_order_book_poloniex
# Node: parse_socket_update_poloniex
# Node: on_update
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

# Node: parse_socket_update_huobi
