import sys

import schedule
import time
import redis
import logging

logger = logging.getLogger("schedule")

class AbcSchedule(object):

    def __init__(self, host):
        # init redis client
        # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
        logging.basicConfig(level=logging.DEBUG)
        self.host = host
        self.r = redis.Redis(host, decode_responses=True)

    def priority_url(self, url):
        # lpush abcspider:start_urls '{ "url": "https://www.abc.net.au/news/2025-02-10/trump-to-announce-new-tariffs-on-steel-and-aluminium/104917334", "meta": {"job-id":"123xsd", "start-date":"dd/mm/yy", "schedule":"priority_url"}}'
        self.r.lpush('abcspider:start_urls', '{ "url": "{url}", "meta": {"schedule":"priority_url"}}')

    def justin_job(self):
        # lpush abcspider:start_urls '{ "url": "https://www.abc.net.au/news/justin", "meta": {"job-id":"123xsd", "start-date":"dd/mm/yy", "schedule_num":2} }'
        logger.info("justin lpush https://www.abc.net.au/news/justin")
        self.r.lpush('abcspider:start_urls', '{ "url": "https://www.abc.net.au/news/justin", "meta": {"schedule_num":1}}')

def main():

    abc_schedule = AbcSchedule("127.0.0.1")

    logger.info("start job")

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