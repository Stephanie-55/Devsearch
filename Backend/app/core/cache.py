# app/core/cache.py
import time

class SimpleCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.store = {}

    def get(self, key):
        item = self.store.get(key)
        if not item:
            return None

        value, expires_at = item
        if time.time() > expires_at:
            del self.store[key]
            return None

        return value

    def set(self, key, value):
        expires_at = time.time() + self.ttl
        self.store[key] = (value, expires_at)


cache = SimpleCache(ttl=300)  # 5 minutes