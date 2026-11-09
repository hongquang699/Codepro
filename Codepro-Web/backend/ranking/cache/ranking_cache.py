import time

class RankingCache:
    _cache = {}
    _ttl = 30 # seconds

    @classmethod
    def get(cls, key):
        entry = cls._cache.get(key)
        if entry:
            val, expires_at = entry
            if time.time() < expires_at:
                return val
            del cls._cache[key]
        return None

    @classmethod
    def set(cls, key, val, ttl=None):
        duration = ttl if ttl is not None else cls._ttl
        cls._cache[key] = (val, time.time() + duration)

    @classmethod
    def invalidate(cls, key_prefix=''):
        if not key_prefix:
            cls._cache.clear()
        else:
            keys_to_del = [k for k in cls._cache if k.startswith(key_prefix)]
            for k in keys_to_del:
                del cls._cache[k]
