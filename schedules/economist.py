import sys

import schedule
import time
import redis
import logging
import connection
from settings_manager import Settings

settings = Settings()

logger = logging.getLogger("economist")

class EconomistSchedule(object):

    # Redis client placeholder.
    server = None

    def __init__(self, name="economist"):
        self.spider_key = f"{name}spider:start_urls"

        try:
            self.server = connection.from_settings(settings)

            if self.server.ping():
                logger.info("redis connect successful.")
            else:
                raise ValueError("redis connect failed.")
        except redis.ConnectionError as e:
            logger.error(f"redis happened error: {e}")
            raise e

    def economist_job(self):
        self.server.lpush(self.spider_key, '{"url": "https://www.economist.com", "meta": {"schedule_num":1}}')
        logger.info(f'lpush {self.spider_key} {{"url": "https://www.economist.com", "meta": {{"schedule_num":1}}}}')

def main():

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')

    economist_schedule = EconomistSchedule()
    economist_schedule.economist_job()

    schedule.every().day.at("04:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("05:15", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("06:12", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("07:20", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("08:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("09:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("09:12", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("10:13", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("10:50", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("11:20", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("12:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("13:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("14:20", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("15:30", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("16:20", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("17:10", "Australia/Sydney").do(economist_schedule.economist_job)
    schedule.every().day.at("18:40", "Australia/Sydney").do(economist_schedule.economist_job)

    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    sys.exit(main()) 