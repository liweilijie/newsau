import redis

class RedisQueue:
    def __init__(self, name='abc', redis_url="redis://localhost:6379/2"):
        self.set_name = f'{name}:sequential'
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def push(self, url):
        self.redis.sadd(self.set_name, url)

    def pop(self):
        url = self.redis.spop(self.set_name)
        return url

    def size(self):
        return self.redis.scard(self.set_name)
