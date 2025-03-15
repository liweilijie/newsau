import sys

import schedule
import time
import redis
import logging
import connection
from settings_manager import Settings

settings = Settings()

logger = logging.getLogger("afr")

class AfrSchedule(object):

    # Redis client placeholder.
    server = None

    def __init__(self, name="afr"):
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

    def afr_job(self):
        self.server.lpush(self.spider_key, '{"url": "https://www.afr.com", "meta": {"schedule_num":1}}')
        logger.info(f'lpush {self.spider_key} {{"url": "https://www.afr.com", "meta": {{"schedule_num":1}}}}')

def main():

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')

    afr_schedule = AfrSchedule()
    afr_schedule.afr_job()

    schedule.every().day.at("06:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("07:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("08:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("09:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("10:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("11:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("12:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("13:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("14:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("15:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("16:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("17:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("18:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("19:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("20:00", "Australia/Sydney").do(afr_schedule.afr_job)
    schedule.every().day.at("21:00", "Australia/Sydney").do(afr_schedule.afr_job)

    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    sys.exit(main())