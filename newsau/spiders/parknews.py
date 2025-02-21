import logging
import scrapy
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from scrapy_redis.spiders import RedisSpider

from newsau.db import orm
from newsau.items import ParkNewsDataItem
from newsau.utils import common
from newsau.cache import url_queue, rcount
from newsau.settings import REDIS_URL, NEWS_ACCOUNTS

logger = logging.getLogger('parknews')

class ParknewsSpider(RedisSpider):
    name = "parknews"
    redis_batch_size = 1

    redis_key = "parknewsspider:start_urls"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        # Be careful primary domain maybe contain other domain to store the image src, so you must remember allowed the domains.
        # domain = kwargs.pop("6parknews.com", "popo8.com")
        # self.allowed_domains = filter(None, domain.split(","))
        self.allowed_domains = ["6parknews.com", "popo8.com"]

        self.queue = url_queue.RedisUrlQueue(self.name, REDIS_URL)
        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS[self.name]["count_everyday"])
        logger.info(f'current count_everyday is:{self.count.get_value()}')

        self.domain = "https://local.6parknews.com/"

        super().__init__(*args, **kwargs)

    def parse(self, response):

        is_priority = False
        schedule_num = None

        if response.request.meta is not None:
            schedule = response.request.meta.get("schedule")
            if schedule is not None and schedule == "priority_url":
                is_priority = True

        if response.request.meta is not None:
            schedule_num = response.request.meta.get("schedule_num")
            if schedule_num is not None and schedule_num > 0:
                logger.info(f'before count_everyday:{self.count.get_value()}')
                self.count.increment(schedule_num)
                logger.info(f'result current count_everyday:{self.count.get_value()}')

        if not is_priority:
            if orm.check_if_exceed_num_today_and_yesterday(self.name, self.count.get_value()):
                logger.info('exceed and return.')
                return

        if common.contains_app_news(response.url):
            yield scrapy.Request(url=response.url, callback=self.detail_parse, dont_filter=True, meta={"is_priority": is_priority})
            return

        post_nodes = response.xpath('//*[@id="d_list"]/ul/li')
        for post_node in post_nodes:
            post_url = post_node.css('a::attr(href)').extract_first("").strip()
            title = post_node.css('a::text').extract_first("").strip()
            post_date = post_node.css('i::text').extract_first("").strip()
            url = urljoin(self.domain, post_url)
            if common.contains_app_news(url):
                if not orm.query_object_id(self.name, url):
                    logger.info(f'a:{url} and push to queue')
                    self.queue.push(url)
                else:
                    logger.info(f'do nothing because already in db:{url}')
            # yield scrapy.Request(url=url, callback=self.detail_parse, dont_filter=True, meta={"title":title})

        logger.info(f'we get the queue len:{self.queue.size()}')

        if orm.check_if_exceed_num_today_and_yesterday(self.name, self.count.get_value()):
            logger.warning(f'exceed and clear the pending list and nothing to do.')
            self.queue.clear()
            return

        yield from self.process_next_url()

    def process_next_url(self):
        """
        Fetch the next URL from the Redis queue and schedule it.
        """
        task = self.queue.pop()
        if task:
            next_url = task.get("url")
            if next_url:
                yield scrapy.Request(next_url, callback=self.detail_parse, dont_filter=True)

    def detail_parse(self, response):

        is_priority = response.meta.get('is_priority', False)


        if not is_priority:
            if orm.check_if_exceed_num_today_and_yesterday(self.name, self.count.get_value()):
                return

        post_title = response.css('.inlineBlock.art-main-body h2::text').extract_first("").strip()
        post_time = response.css('.art-main-body-auth::text').extract_first("").strip()
        post_content = response.xpath('//*[@id="news_content"]').extract_first("").strip()

        park_item = ParkNewsDataItem()
        park_item["name"] = self.name
        park_item["priority"] = is_priority

        park_item["origin_title"] = post_title
        # park_item["topic"] = post_topic
        park_item["url"] = response.url
        park_item["url_object_id"] = common.get_md5(park_item["url"])
        park_item["post_date"] = common.extract_datetime(post_time)

        # TODO: check this url_object_id if exist in db
        if orm.query_object_id(self.name, park_item["url_object_id"]):
            print(f"url: {park_item['url']} already exist in db nothing to do.")
            return

        park_item["front_image_url"] = []

        soup = BeautifulSoup(post_content, "html.parser")

        for img in soup.findAll('img'):
            park_item["front_image_url"].append(img['src'])  # append origin url to download
            img['src'] = common.get_finished_image_url(self.name, park_item["url_object_id"], img['src'])  # replace our website image url from cdn

        # find all a label
        for a in soup.find_all('a'):
            # replace all a label with its text
            a.replace_with(a.text)

        post_content = str(soup)
        park_item["origin_content"] = post_content
        park_item["post_type"] = "newsflashes"


        if park_item["url"] != "" and park_item["origin_title"] != "" and park_item["origin_content"] != "":
            yield park_item
        else:
            print("nothing to do due to invalid item: ", park_item)
