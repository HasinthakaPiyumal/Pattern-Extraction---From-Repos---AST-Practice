# Cluster 2

class AsyncSafeDict:

    def __init__(self):
        self.dict = {}
        self.lock = asyncio.Lock()

    async def put(self, key, value):
        async with self.lock:
            self.dict[key] = value

    async def get(self, key, default=None):
        async with self.lock:
            return self.dict.get(key, default)

    async def pop(self, key, default=None):
        async with self.lock:
            return self.dict.pop(key, default)

    async def keys(self):
        async with self.lock:
            return list(self.dict.keys())

def __init__(self):
    self.dict = {}
    self.lock = asyncio.Lock()

