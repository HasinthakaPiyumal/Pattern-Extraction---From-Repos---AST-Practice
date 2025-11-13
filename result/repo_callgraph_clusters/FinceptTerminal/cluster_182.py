# Cluster 182

class DataCache:
    """Redis-based caching for data feeds"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.default_ttl = CONFIG.agent.cache_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int]=None) -> bool:
        """Set cached data"""
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            return False

    def generate_key(self, source: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        param_str = json.dumps(params, sort_keys=True)
        return f'{source}:{hashlib.md5(param_str.encode()).hexdigest()}'

def __init__(self):
    self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    self.default_ttl = CONFIG.agent.cache_ttl

