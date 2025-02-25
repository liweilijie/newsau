import sys

import schedule
import time
import redis
import logging
import connection
from settings_manager import Settings

settings = Settings()

logger = logging.getLogger("parknews")

class ParkNewsSchedule(object):

    # Redis client placeholder.
    server = None

    def __init__(self, name="parknews"):
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

    def parknews_job(self):
        self.server.lpush(self.spider_key, '{"url": "https://local.6parknews.com/index.php?type_id=3"}')
        self.server.lpush(self.spider_key, '{"url": "https://local.6parknews.com/index.php?type_id=3&p=2&nomobile=0"}')
        logger.info(f'lpush {self.spider_key} {{"url": "https://local.6parknews.com/index.php?type_id=3"}}')

def main():

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')

    parknews_schedule = ParkNewsSchedule()
    parknews_schedule.parknews_job()
    schedule.every(10).minutes.do(parknews_schedule.parknews_job)

    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    sys.exit(main())