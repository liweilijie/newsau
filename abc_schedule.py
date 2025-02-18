import sys

import schedule
import time
import redis
import logging
import os
from dotenv import load_dotenv


logger = logging.getLogger("abc_schedule")

class AbcSchedule(object):

    def __init__(self, host="127.0.0.1", port=6379, db=2, password=None):
        self.spider_key = "abcspider:start_urls"
        try:
            self.r = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)

            if self.r.ping():
                logger.info("Redis connect successful.")
            else:
                logger.error("Redis connect failed！")
        except redis.ConnectionError as e:
            logger.error(f"Redis happened error: {e}")
            raise e

    def justin_job(self):
        self.r.lpush(self.spider_key, '{"url": "https://www.abc.net.au/news/justin", "meta": {"schedule_num":2}}')
        logger.info("justin lpush https://www.abc.net.au/news/justin")

def main():
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')
    logger.info("new redis 2 start job")

    load_dotenv()

    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "2"))

    logger.info(f"REDIS_HOST: {REDIS_HOST}, REDIS_PASSWORD: {REDIS_PASSWORD}, REDIS_PORT: {REDIS_PORT}, REDIS_DB: {REDIS_DB}")

    abc_schedule = AbcSchedule(REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD)
    abc_schedule.justin_job()

    schedule.every().day.at("07:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("08:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("09:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("10:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("11:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("12:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("13:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("14:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("15:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("16:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("17:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("18:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("19:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("20:00", "Australia/Sydney").do(abc_schedule.justin_job)
    schedule.every().day.at("21:00", "Australia/Sydney").do(abc_schedule.justin_job)

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