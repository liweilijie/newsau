import redis

from newsau.settings import REDIS_URL

def push_url_to_redis():
    rd = redis.Redis("127.0.0.1", decode_responses=True)
    rd.lpush('abcspider:start_urls', '{ "url": "https://www.abc.net.au/news/2025-02-10/trump-to-announce-new-tariffs-on-steel-and-aluminium/104917334", "meta": {"job-id":"123xsd", "start-date":"dd/mm/yy"}}')


if __name__ == "__main__":
    push_url_to_redis()