# Cluster 9

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

def first(self, topic_id):
    return self.r.zrevrange(topic_id, 0, 0)[0]

# Node: zrevrange
