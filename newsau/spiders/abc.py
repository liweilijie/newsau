import pickle
from urllib import parse
import re
import logging

import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from newsau.items import AbcDataItem
from newsau.utils import common
from scrapy_redis.spiders import RedisSpider
from newsau.db import orm
from newsau.cache import url_queue
from newsau.cache import rcount
from newsau.settings import REDIS_URL
from newsau.settings import NEWS_ACCOUNTS

logger = logging.getLogger('abc')

class AbcSpider(RedisSpider):

    name = "abc"
    # be careful primary domain maybe contain other domain to store the image src, so you must remember allowed the domains.
    # allowed_domains = ["abc.net.au", "live-production.wcms.abc-cdn.net.au"]

    # when we use scrapy_redis, so this start_urls don't need it.
    # start_urls = ["https://www.abc.net.au/news/justin"]
    total_urls = 0
    redis_key = "abcspider:start_urls"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    }
    # Number of url to fetch from redis on each attempt
    # Update this as needed - this will be 16 by default (like the concurrency default)
    redis_batch_size = 1

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        # Be careful primary domain maybe contain other domain to store the image src, so you must remember allowed the domains.
        domain = kwargs.pop("abc.net.au", "live-production.wcms.abc-cdn.net.au")
        self.allowed_domains = filter(None, domain.split(","))

        self.domain = "https://www.abc.net.au/"

        self.queue = url_queue.RedisUrlQueue(self.name, REDIS_URL)
        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS[self.name]["count_everyday"])
        logger.info(f'current count_everyday is:{self.count.get_value()}')

        super().__init__(*args, **kwargs)

    def parse(self, response):

        is_priority = response.meta.get("schedule") == "priority_url"
        schedule_num = response.meta.get("schedule_num", 0)

        if schedule_num > 0:
            logger.info(f'Before count_everyday: {self.count.get_value()}')
            self.count.increment(schedule_num)
            logger.info(f'After increment, count_everyday: {self.count.get_value()}')

        if not is_priority and orm.check_if_exceed_num(self.name, self.count.get_value()):
            logger.info('Exceeded daily limit, stopping crawl.')
            return

        # if response.request.meta is not None:
        #     schedule = response.request.meta.get("schedule")
        #     if schedule is not None and schedule == "priority_url":
        #         is_priority = True
        #
        # if response.request.meta is not None:
        #     schedule_num = response.request.meta.get("schedule_num")
        #     if schedule_num is not None and schedule_num > 0:
        #         logger.info(f'before count_everyday:{self.count.get_value()}')
        #         self.count.increment(schedule_num)
        #         logger.info(f'result current count_everyday:{self.count.get_value()}')
        #
        # if not is_priority:
        #     if orm.check_if_exceed_num(self.name, self.count.get_value()):
        #         logger.info('exceed and return.')
        #         return

        if common.contains_valid_date(response.url):
            yield scrapy.Request(url=response.url, callback=self.detail_parse, dont_filter=True, meta={"is_priority": True})
            return

        post_nodes = response.xpath('//div[@data-component="PaginationList"]//ul/li')

        # for post_node in post_nodes[:11]:
        for post_node in post_nodes:
            post_url = post_node.css('h3 a::attr(href)').extract_first("").strip()
            # post_title = post_node.css('h3 a::text').extract_first("")
            # post_topic = post_node.css('div a[data-component="SubjectTag"] p::text').extract_first("")
            # post_first_image_url = post_node.css('div[data-component="Thumbnail"] img::attr(src)').extract_first("").strip()

            if post_url:
                url = urljoin(self.domain, post_url)
                logger.info(f'url:{url}, post_url:{post_url}')
                if common.contains_valid_date(url) and not orm.query_object_id(self.name, common.get_md5(url)):
                    logger.info(f'New URL found: {url}, adding to queue.')
                    self.queue.push(url)
                else:
                    logger.info(f'URL already processed or invalid: {url}')
                # if common.contains_valid_date(url):
                #     if not orm.query_object_id(self.name, common.get_md5(url)):
                #         logger.info(f'a:{url} and push to queue')
                #         self.queue.push(url)
                #     else:
                #         logger.info(f'do nothing because already in db:{url}')

        logger.info(f'Queue size: {self.queue.size()}')

        if orm.check_if_exceed_num(self.name, self.count.get_value()):
            logger.warning('Daily limit reached, clearing queue.')
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


    # scrapy shell https://www.abc.net.au/news/2025-02-03/alice-springs-cairns-flight-central-australia-tourism-season/104888858
    # scrapy shell to manual code the css selector
    def detail_parse(self, response):

        is_priority = response.meta.get('is_priority', False)


        if not is_priority and orm.check_if_exceed_num(self.name, self.count.get_value()):
            logger.info('Exceeded daily limit, skipping this URL.')
            return

        # if not is_priority:
        #     if orm.check_if_exceed_num(self.name, self.count.get_value()):
        #         return

        logger.info(f'Processing detail page: {response.url}')
        # self.log(f"I just visited parse detail {response.url}")

        abc_item = AbcDataItem()
        abc_item["name"] = self.name
        abc_item["priority"] = is_priority

        post_title = response.xpath('//*[@id="content"]/article//header//h1/text()').extract_first("").strip()
        if not post_title:
        # if post_title == '':
            post_title = response.css('div[data-component="ArticleWeb"] h1::text').extract_first("").strip()

        if not post_title:
            logger.warning(f'No title found for URL: {response.url}')
            yield from self.process_next_url()  # Process next URL
            return
        # if post_title == '' or post_title is None:
        #     self.log(f"no title found in {response.url}")
        #     return

        post_topic = response.xpath('//*[@id="content"]/article//header//ul/li//p/text()').extract_first("").strip()
        if post_topic == '':
            post_topic = response.css('div[data-component="ArticleWeb"] li a[data-component="SubjectTag"] p::text').extract_first("").strip()
            # //*[@id="content"]/article/div/div[1]/div/div[2]/ul/li[2]/span/a
        if post_topic == '':
            post_topic = response.xpath('//*[@id="content"]/article/div//a[@data-component="InfoSourceTag"]/p/text()').extract_first("").strip()

        # post_content_first_image_url = response.css('figure[data-component="Figure"] div img::attr(src)').extract_first("").strip()

        # //*[@id="content"]/article/div/div[1]/div[1]/div[3]
        post_header = response.xpath('//*[@id="content"]/article/div/div[1]/div[1]/div[3]').extract_first("").strip()

        post_content = response.xpath('//*[@id="body"]//div[contains(@class,ArticleRender)]/text()').extract_first("").strip()
        if not post_content:
            post_content = response.xpath('//*[@id="content"]/article/div/div[2]/div/div[1]').extract_first("").strip()


        if not post_content:
            logger.warning(f'No content found for URL: {response.url}')
            yield from self.process_next_url()  # Process next URL
            return
        # if post_content == '' or post_content is None:
        #     self.log(f"not content found in {response.url}")
        #     return

        # pickle.dump(post_content, open("abc.html", "wb"))

        # data-component = "Timestamp"
        # datetime = "2025-02-10T04:55:05.000Z"
        # //*[@id="content"]/article/div/div[1]/div[1]/div[2]/div/time[1]
        post_time = response.xpath('//time[@data-component="Timestamp"]/@datetime').extract_first("").strip()
        abc_item["post_date"] = common.convert_to_datetime(post_time)

        if post_header != '':
            post_content = post_header + post_content


        abc_item["origin_title"] = post_title
        abc_item["topic"] = post_topic
        abc_item["url"] = response.url
        abc_item["url_object_id"] = common.get_md5(abc_item["url"])


        if orm.query_object_id(self.name, abc_item["url_object_id"]):
            logger.info(f'URL already processed: {abc_item["url"]}')
            yield from self.process_next_url()  # Process next URL
            return

        # # TODO: check this url_object_id if exist in db
        # if orm.query_object_id(self.name, abc_item["url_object_id"]):
        #     print(f"url: {abc_item['url']} already exist in db nothing to do.")
        #     return

        # abc_item["category"] = orm.get_category(self.name, abc_item["topic"])

        abc_item["front_image_url"] = []

        # process the content
        # find all the images src in the post_content
        # and store these images src
        # and replace the domain of the src in post_content
        soup = BeautifulSoup(post_content,"html.parser")
        for img in soup.findAll('img'):
            abc_item["front_image_url"].append(img['src']) # append origin url to download
            img['src'] = common.get_finished_image_url(self.name, abc_item["url_object_id"], img['src']) # replace our website image url from cdn

        # find all a label
        for a in soup.find_all('a'):
            # replace all a label with its text
            a.replace_with(a.text)

        # trim div data-component="EmbedBlock"
        # soup.find('div', {"data-component":"EmbedBlock"}).decompose()
        for div in soup.find_all('div', {"data-component":"EmbedBlock"}):
            div.decompose()

        # trim span data-component="Loading" data-print="inline-media"
        for span in soup.find_all('span', {"data-component":"Loading"}):
            span.decompose()

        post_content = str(soup)
        abc_item["origin_content"] = post_content


        if abc_item["url"] != "" and abc_item["origin_title"] != "" and abc_item["origin_content"] != "":
            yield abc_item
        else:
            logger.warning(f'Invalid item, missing data: {abc_item}')
            yield from self.process_next_url()  # Process next URL