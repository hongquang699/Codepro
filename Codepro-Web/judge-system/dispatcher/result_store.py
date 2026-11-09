"""Redis-backed mapping for Judge Manager results across process restarts."""
import json


class ResultStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.key = 'judge:queue:results'

    def __setitem__(self, job_id, value):
        self.redis.hset(self.key, job_id, json.dumps(value))

    def __getitem__(self, job_id):
        data = self.get(job_id)
        if data is None:
            raise KeyError(job_id)
        return data

    def __contains__(self, job_id):
        return bool(self.redis.hexists(self.key, job_id))

    def get(self, job_id, default=None):
        data = self.redis.hget(self.key, job_id)
        return json.loads(data) if data else default

    def values(self):
        return [json.loads(data) for data in self.redis.hvals(self.key)]
