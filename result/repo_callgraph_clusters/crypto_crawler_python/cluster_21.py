# Cluster 21

# Node: dumps
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

def redis_test():
    r = _redis.StrictRedis(host='0.0.0.0', port=6379, db=0)
    ts = int(round(time.time() * 1000))
    r.set('nonce', str(ts))
    r.delete('SYNC_STAGE')

# Node: delete
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
