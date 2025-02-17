import sys

import schedule
import time
import redis
import logging

logger = logging.getLogger("afr_schedule")

class AfcSchedule(object):

    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)

    def afr_job(self):
        logger.info("lpush https://www.afr.com")
        self.r.lpush('afrspider:start_urls', '{ "url": "https://www.afr.com", "meta": {"schedule_num":1}}')

def main():
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s:%(name)s:%(levelname)s:%(lineno)d:%(module)s:%(message)s')
    logger.info("new redis 2 start job")

    afc_schedule = AfcSchedule()
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