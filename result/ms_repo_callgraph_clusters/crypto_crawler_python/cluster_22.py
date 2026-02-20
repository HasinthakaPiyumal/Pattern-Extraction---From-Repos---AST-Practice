# Cluster 22

def float_to_str(f):
    """
    :param f:   Float or Decimal number
    :return: to be represented within EXACT precision as string
    NOTE: For Decimal you may end up with following numbers:
    0.0019120000000000000710265180003943896736018359661102294921875
    """
    float_string = str(f).lower()
    if 'e' in float_string:
        digits, exp = float_string.split('e')
        digits = digits.replace('.', '').replace('-', '')
        exp = int(exp)
        zero_padding = '0' * (abs(int(exp)) - 1)
        sign = '-' if f < 0 else ''
        if exp > 0:
            float_string = '{}{}{}.0'.format(sign, digits, zero_padding)
        else:
            float_string = '{}0.{}{}'.format(sign, zero_padding, digits)
    elif float_string[-2:] == '.0':
        float_string = float_string[:-2]
    return float_string

# Node: lower
# Node: abs
class ExchangeKey(object):

    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret

    @classmethod
    def from_file(cls, path, exchange_name):
        array = []
        full_path = os.path.join(path, exchange_name.lower() + '.key')
        with open(full_path, 'r') as myfile:
            for line in myfile:
                array.append(line.rstrip())
                if len(array) == 2:
                    break
        return ExchangeKey(array[0], array[1])

@classmethod
def from_file(cls, path, exchange_name):
    array = []
    full_path = os.path.join(path, exchange_name.lower() + '.key')
    with open(full_path, 'r') as myfile:
        for line in myfile:
            array.append(line.rstrip())
            if len(array) == 2:
                break
    return ExchangeKey(array[0], array[1])

# Node: rstrip
# Node: ExchangeKey
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

# Node: dumps
def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

# Node: range
# Node: min
class RedisConnection(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._connect()

    def _connect(self):
        self.r = _redis.StrictRedis(host=self.host, port=self.port, db=0)

def _connect(self):
    self.r = _redis.StrictRedis(host=self.host, port=self.port, db=0)

# Node: StrictRedis
class PriorityQueue(RedisConnection):

    def add_order_to_watch_queue(self, topic_id, order):
        """
            Place orders to watch list = priority queue by TIME.
            We have to use current time instead of create time of orders to avoid collisions and overwrites.

        :param topic_id: Redis key
        :param order:
        :return:
        """
        assert order is not None
        return self.r.zadd(topic_id, -get_now_seconds_utc_ms(), pickle.dumps(order))

    def first(self, topic_id):
        return self.r.zrevrange(topic_id, 0, 0)[0]

    def get_oldest_order(self, topic_id):
        try:
            _item = self.first(topic_id)
            while self.r.zrem(topic_id, _item) == 0:
                _item = self.first(topic_id)
            return pickle.loads(_item)
        except IndexError:
            pass
        return None

def add_order_to_watch_queue(self, topic_id, order):
    """
            Place orders to watch list = priority queue by TIME.
            We have to use current time instead of create time of orders to avoid collisions and overwrites.

        :param topic_id: Redis key
        :param order:
        :return:
        """
    assert order is not None
    return self.r.zadd(topic_id, -get_now_seconds_utc_ms(), pickle.dumps(order))

# Node: zadd
class MemoryCache(RedisConnection):

    def get_counter(self):
        return self.r.incr('nonce')

    def get_arbitrage_id(self):
        return self.r.incr('arbitrage_id')

    def _init_nonce(self):
        ts = int(round(time.time() * 1000))
        self.r.set('nonce', str(ts))

    def update_balance(self, exchange_name, balance):
        self.r.set(exchange_name, pickle.dumps(balance))

    def get_balance(self, exchange_id):
        exchange_name = get_exchange_name_by_id(exchange_id)
        return pickle.loads(self.r.get(exchange_name))

    def get_value(self, key_name):
        return self.r.get(key_name)

    def set_value(self, key_name, key_value):
        return self.r.set(key_name, key_value)

    def cache_order_book(self, order_book):
        """
            We cannot rely on order book time because in case exchange return dublicative order book
            time may be different.

        :param order_book:
        :return:
        """
        key = '{}-{}'.format(order_book.exchange_id, order_book.pair_id)
        self.r.set(key, pickle.dumps(order_book))

    def get_last_order_book(self, pair_id, exchange_id):
        key = '{}-{}'.format(exchange_id, pair_id)
        value = self.r.get(key)
        if value is None:
            return None
        return pickle.loads(value)

def _init_nonce(self):
    ts = int(round(time.time() * 1000))
    self.r.set('nonce', str(ts))

# Node: round
# Node: time
# Node: set
def update_balance(self, exchange_name, balance):
    self.r.set(exchange_name, pickle.dumps(balance))

def set_value(self, key_name, key_value):
    return self.r.set(key_name, key_value)

def cache_order_book(self, order_book):
    """
            We cannot rely on order book time because in case exchange return dublicative order book
            time may be different.

        :param order_book:
        :return:
        """
    key = '{}-{}'.format(order_book.exchange_id, order_book.pair_id)
    self.r.set(key, pickle.dumps(order_book))

class MessageQueue(RedisConnection):

    def add_message(self, topic_id, msg):
        msg_with_ts = '{msg}\nTS:{ts}'.format(msg=msg, ts=get_now_seconds_utc_ms())
        self.r.rpush(topic_id, msg_with_ts)

    def get_topic_size(self, topic_id):
        return self.r.llen(topic_id)

    def empty(self, topic_id):
        return self.get_topic_size(topic_id) == 0

    def get_message(self, topic_id, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        item = self.r.lpop(topic_id)
        return item

    def get_message_nowait(self, topic_id):
        """Equivalent to get(False)."""
        return self.get_message(topic_id, True)

    def add_message_to_start(self, topic_id, msg):
        self.r.lpush(topic_id, msg)

    def add_order(self, topic_id, balance):
        self.r.lpush(topic_id, pickle.dumps(balance))

    def get_next_order(self, topic_id):
        entry = self.get_message(topic_id, True)
        if entry:
            return pickle.loads(entry)
        return None

def add_message_to_start(self, topic_id, msg):
    self.r.lpush(topic_id, msg)

# Node: lpush
def add_order(self, topic_id, balance):
    self.r.lpush(topic_id, pickle.dumps(balance))

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

def is_error(response):
    """

    Proper response should contain 'response' key.

    EGeneral:Invalid arguments
    EService:Unavailable
    ETrade:Invalid request
    EOrder:Cannot open position
    EOrder:Cannot open opposing position
    EOrder:Margin allowance exceeded
    EOrder:Margin level too low
    EOrder:Insufficient margin (exchange does not have sufficient funds to allow margin trading)
    EOrder:Insufficient funds (insufficient user funds)
    EOrder:Order minimum not met (volume too low)
    EOrder:Orders limit exceeded
    EOrder:Positions limit exceeded
    EOrder:Rate limit exceeded
    EOrder:Scheduled orders limit exceeded
    EOrder:Unknown position

    :param response: raw responce from requests
    :return: True or False as indicator for possible errors
    """
    if response is None or 'result' not in response:
        return True
    str_repr = json.dumps(response)
    for entry in KRAKEN_ERRORS:
        if entry in str_repr:
            return True
    return False

# Node: do_we_have_enough
# Node: search_for_arbitrage
def redis_test():
    r = _redis.StrictRedis(host='0.0.0.0', port=6379, db=0)
    ts = int(round(time.time() * 1000))
    r.set('nonce', str(ts))
    r.delete('SYNC_STAGE')

# Node: delete
def get_change(current, previous, provide_abs=True):
    """

    :param provide_abs:
    :param current:
    :param previous:
    :return: difference in percentage between current & previous
    """
    tot = Decimal(0.5) * Decimal(current + previous)
    if provide_abs:
        diff = Decimal(abs(current - previous))
    else:
        diff = Decimal(current - previous)
    percent = 0.001
    if tot != 0:
        z = diff / tot
        if z > 0.001:
            percent = truncate_float(z * 100, 2)
    return percent

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

def is_order_books_expired(order_book_src, order_book_dst, local_cache, msg_queue, log_file_name):
    for order_book in [order_book_src, order_book_dst]:
        prev_order_book = local_cache.get_last_order_book(order_book.pair_id, order_book.exchange_id)
        if prev_order_book is None:
            continue
        total_asks = len(order_book.ask)
        number_of_same_asks = len(set(order_book.ask).intersection(prev_order_book.ask))
        total_bids = len(order_book.bid)
        number_of_same_bids = len(set(order_book.bid).intersection(prev_order_book.bid))
        if total_asks == number_of_same_asks or total_bids == number_of_same_bids:
            log_dublicative_order_book(log_file_name, order_book, prev_order_book, msg_queue)
            return True
    return False

# Node: get_last_order_book
# Node: intersection
# Node: log_dublicative_order_book
