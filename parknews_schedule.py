import sys

import schedule
import time
import redis
import logging
import os
from dotenv import load_dotenv


logger = logging.getLogger("parknews_schedule")

class ParkNewsSchedule(object):

    def __init__(self, name, redis_url):
        self.spider_key = f"{name}spider:start_urls"
        try:
            self.r = redis.Redis.from_url(redis_url, decode_responses=True)

            if self.r.ping():
                logger.info("Redis connect successful.")
            else:
                logger.error("Redis connect failed！")
        except redis.ConnectionError as e:
            logger.error(f"Redis happened error: {e}")
            raise e

    def au_job(self):
        self.r.lpush(self.spider_key, '{"url": "https://local.6parknews.com/index.php?type_id=3"}')
        self.r.lpush(self.spider_key, '{"url": "https://local.6parknews.com/index.php?type_id=3&p=2&nomobile=0"}')
        logger.info(f'lpush {self.spider_key} {{"url": "https://local.6parknews.com/index.php?type_id=3"}}')

def main():
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')
    logger.info("new redis 2 start job")

    load_dotenv()

    redis_url = os.getenv("REDIS_URL")

    logger.info(f"redis_url:{redis_url}")

    park_schedule = ParkNewsSchedule("parknews", redis_url)

    park_schedule.au_job()

    schedule.every(10).minutes.do(park_schedule.au_job)
    # schedule.every().hour.do(park_schedule.au_job)
    # schedule.every().day.at("21:00", "Australia/Sydney").do(park_schedule.justin_job)

    # schedule.every(10).minutes.do(job)
    # schedule.every().hour.do(job)
    # schedule.every().day.at("10:30").do(job)
    # schedule.every().monday.do(job)
    # schedule.every().wednesday.at("13:15").do(job)
    # schedule.every().day.at("12:42", "Europe/Amsterdam").do(job)
    # schedule.every().minute.at(":17").do(job)

    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    sys.exit(main())