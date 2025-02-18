import time
import redis
import json

from newsau.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, NEWS_ACCOUNTS

class RedisObjectStore:
    def __init__(self, key, host='localhost', port=6379, db=2):
        self.redis = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.key = key

    def set(self, obj, timeout=None):
        """Store an object in Redis with an optional expiration time"""
        self.redis.set(self.key, json.dumps(obj), ex=timeout)

    def get(self):
        """Retrieve an object from Redis"""
        data = self.redis.get(self.key)
        return json.loads(data) if data else None

    def update(self, updates):
        """Update specific fields of the object"""
        data = self.get()
        if data:
            data.update(updates)
            self.set(data)
            return True
        return False

    def delete(self):
        """Delete the object from Redis"""
        self.redis.delete(self.key)

accounts_store = RedisObjectStore("accounts:setting", REDIS_HOST, REDIS_PORT, REDIS_DB)
accounts_store.set(NEWS_ACCOUNTS)
print(accounts_store.get())


class RedisSyncStatus:
    def __init__(self, key, host='localhost', port=6379, db=2):
        self.redis = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.key = key

    def set(self, timeout=90):
        self.redis.set(self.key, "1", ex=timeout)

    def clear(self):
        self.redis.delete(self.key)

    def check(self):
        return self.redis.exists(self.key)


# sync_status = RedisSyncStatus("afr_sync_flag")

# Example usage
if __name__ == "__main__":

    # sync_status = RedisSyncStatus("sync_flag")
    # sync_status.set(timeout=2)
    # print(sync_status.check())
    # # sync_status.clear()
    # time.sleep(3)
    # print(sync_status.check())

    # obj_store = RedisObjectStore("user:123")
    # obj_store.set({"name": "Alice", "age": 25}, timeout=300)
    # print(obj_store.get())  # Retrieve the object
    # obj_store.update({"age": 26})  # Update the object
    # print(obj_store.get())  # View the updated object
    # obj_store.delete()  # Delete the object
    print(accounts_store.get()["afr"]["image_cdn_domain"])

