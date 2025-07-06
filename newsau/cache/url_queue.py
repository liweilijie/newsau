import redis
import json
import logging

logger = logging.getLogger(__name__)

class RedisUrlQueue:
    def __init__(self, spider_name, redis_url="redis://localhost:6379/2"):
        """
        Initialize Redis connection and queue.

        :param spider_name: The name of the spider (used as Redis queue key).
        :param redis_url: Redis connection URL.
        """
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.queue_key = f"{spider_name}spider:start_urls"  # Default scrapy_redis queue

    def push(self, url, meta=None):
        """
        Push a new URL into the Redis queue as a JSON object.

        :param url: The URL to be added.
        :param meta: Additional metadata (default: None).
        :param url_cookie_key: Unique cookie/session key (default: None).
        """
        task = {
            "url": url,
            "meta": meta if meta else {},  # Ensure meta is always a dictionary
        }

        json_task = json.dumps(task)  # Convert task to JSON
        self.redis_client.lpush(self.queue_key, json_task)  # Push to Redis queue
        logger.info(f"✅ Task added to queue: {json_task}")

    def pop(self):
        """
        Pop a URL task from the queue (FIFO).

        :return: A dictionary with `url`, `meta`, and `url_cookie_key`, or None if empty.
        """
        task_json = self.redis_client.rpop(self.queue_key)  # Fetch from Redis
        if task_json:
            task = json.loads(task_json)  # Convert JSON back to dictionary
            logger.info(f"🚀 Task popped from queue: {task}")
            return task
        else:
            logger.warning("⚠️ Queue is empty")
            return None

    def size(self):
        """
        Get the current queue size.

        :return: The number of tasks in the queue.
        """
        count = self.redis_client.llen(self.queue_key)
        logger.info(f"📊 Queue size: {count}")
        return count

    def clear(self):
        """
        Clear all tasks from the queue.
        """
        self.redis_client.delete(self.queue_key)
        logger.info(f"🗑️ Task queue {self.queue_key} has been cleared!")