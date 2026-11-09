import time

class ScoreboardCache:
    _cache = {}
    _ttl = 10 # 10 seconds for live contest scoreboard

    @classmethod
    def get(cls, contest_id):
        key = f"contest_sb_{contest_id}"
        entry = cls._cache.get(key)
        if entry:
            val, expires = entry
            if time.time() < expires:
                return val
            del cls._cache[key]
        return None

    @classmethod
    def set(cls, contest_id, data, ttl=None):
        key = f"contest_sb_{contest_id}"
        duration = ttl if ttl is not None else cls._ttl
        cls._cache[key] = (data, time.time() + duration)

    @classmethod
    def invalidate(cls, contest_id):
        key = f"contest_sb_{contest_id}"
        cls._cache.pop(key, None)
