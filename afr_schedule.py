import sys
import os

import schedule
import time
import redis
import logging
from dotenv import load_dotenv

logger = logging.getLogger("afr_schedule")

class AfcSchedule(object):

    def __init__(self, host="127.0.0.1", port=6379, db=2, password=None):
        self.spider_key = "afrspider:start_urls"
        try:
            self.r = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)

            if self.r.ping():
                logger.info("Redis connect successful.")
            else:
                logger.error("Redis connect failed！")
        except redis.ConnectionError as e:
            logger.error(f"Redis happened error: {e}")
            raise e

    def afr_job(self):
        self.r.lpush(self.spider_key, '{ "url": "https://www.afr.com", "meta": {"schedule_num":1}}')
        logger.info(f'lpush {self.spider_key} https://www.afr.com')

def main():
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')

    load_dotenv()

    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "2"))

    logger.info(f"REDIS_HOST: {REDIS_HOST}, REDIS_PASSWORD: {REDIS_PASSWORD}, REDIS_PORT: {REDIS_PORT}, REDIS_DB: {REDIS_DB}")

    afc_schedule = AfcSchedule(REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD)
    afc_schedule.afr_job()

    schedule.every().hour.do(afc_schedule.afr_job)

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