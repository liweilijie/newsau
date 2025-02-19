import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCounter:
    def __init__(self, key, redis_url):
        """
        Initialize the RedisCounter with a Redis connection and a key.

        :param redis_url: The Redis connection URL.
        :param key: The key used to store the numeric value in Redis.
        """
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.key = f'{key}:count_everyday'

    def set_value(self, value):
        """
        Set the counter to a specific integer value.

        :param value: The integer value to set.
        """
        if isinstance(value, int):
            self.redis.set(self.key, value)
            logger.info(f"Set {self.key} to {value}")
        else:
            logger.error("Value must be an integer")

    def get_value(self):
        """
        Get the current value of the counter.

        :return: The integer value stored in Redis, or None if not set.
        """
        value = self.redis.get(self.key)
        return int(value) if value is not None and value.isdigit() else None

    def increment(self, amount=1):
        """
        Increment the counter by a specified integer amount.

        :param amount: The amount to increment by (default is 1).
        :return: The new value after incrementing.
        """
        new_value = self.redis.incr(self.key, amount)
        logger.info(f"Incremented {self.key} by {amount}, new value: {new_value}")
        return new_value

    def decrement(self, amount=1):
        """
        Decrement the counter by a specified integer amount.

        :param amount: The amount to decrement by (default is 1).
        :return: The new value after decrementing.
        """
        new_value = self.redis.decr(self.key, amount)
        logger.info(f"Decremented {self.key} by {amount}, new value: {new_value}")
        return new_value

    def delete(self):
        """
        Delete the counter from Redis.
        """
        self.redis.delete(self.key)
        logger.info(f"Deleted key: {self.key}")

# 🔹 Example Usage
if __name__ == "__main__":
    redis_url = "redis://localhost:6379/0"  # Change this to your Redis URL
    counter = RedisCounter(redis_url, "abc")

    counter.set_value(10)       # Set to 10
    print(counter.get_value())  # Output: 10

    counter.increment(5)        # Increment by 5
    print(counter.get_value())  # Output: 15

    counter.decrement(3)        # Decrement by 3
    print(counter.get_value())  # Output: 12

    counter.delete()            # Delete the key
