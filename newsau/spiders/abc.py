from urllib import parse
import re

import scrapy
from bs4 import BeautifulSoup

# from scrapy import Request

from newsau.items import AbcDataItem
from newsau.utils import common
from newsau.db import mysqldb
from scrapy_redis.spiders import RedisSpider
from newsau.settings import NEWS_ACCOUNTS


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
        self.mysqlObj = mysqldb.MySqlObj() # for find the object_url_id duplicate
        super().__init__(*args, **kwargs)

    def parse(self, response):
        self.log(f"I just visited and parse {response.url}")

        post_nodes = response.xpath('//div[@data-component="PaginationList"]//ul/li')

        for post_node in post_nodes[:11]:
        # for post_node in post_nodes:
            post_url = post_node.css('h3 a::attr(href)').extract_first("")
            post_title = post_node.css('h3 a::text').extract_first("")
            post_topic = post_node.css('div a[data-component="SubjectTag"] p::text').extract_first("")
            post_first_image_url = post_node.css('div[data-component="Thumbnail"] img::attr(src)').extract_first("").strip()

            if post_url != "":
                self.total_urls += 1
                yield scrapy.Request(url=parse.urljoin(response.url, post_url), meta={"post_first_image_url": post_first_image_url}, callback=self.parse_detail, dont_filter=True)


        if len(post_nodes) <= 0:
            if self._check_detail_page_by_url(response.url) is not None:
                yield scrapy.Request(url=response.url, callback=self.parse_detail, dont_filter=True)

        # get the url of sub new and call the callback function to parse

        # get next page url and to download
        # get more load button
        # load_more_stories = response.css('button[data-component="PaginationLoadMoreButton"]')
        print("total urls:", self.total_urls)


    # scrapy shell https://www.abc.net.au/news/2025-02-03/alice-springs-cairns-flight-central-australia-tourism-season/104888858
    # scrapy shell to manual code the css selector
    def parse_detail(self, response):

        current_count = self.mysqlObj.count_urls_today(self.name)

        if current_count >= NEWS_ACCOUNTS[self.name]["count_everyday"]:
            self.log(f"we had {current_count} >= {NEWS_ACCOUNTS[self.name]["count_everyday"]} and exceed the count limit and do nothing.")
            return

        self.log(f"I just visited detail {response.url}")

        abc_item = AbcDataItem()
        abc_item["name"] = self.name

        post_title = response.xpath('//*[@id="content"]/article//header//h1/text()').extract_first("").strip()
        if post_title == '':
            post_title = response.css('div[data-component="ArticleWeb"] h1::text').extract_first("").strip()

        if post_title == '' or post_title is None:
            self.log(f"no title found in {response.url}")
            return

        post_topic = response.xpath('//*[@id="content"]/article//header//ul/li//p/text()').extract_first("").strip()
        if post_topic == '':
            post_topic = response.css('div[data-component="ArticleWeb"] li a[data-component="SubjectTag"] p::text').extract_first("").strip()

        # post_content_first_image_url = response.css('figure[data-component="Figure"] div img::attr(src)').extract_first("").strip()

        # //*[@id="content"]/article/div/div[1]/div[1]/div[3]
        post_header = response.xpath('//*[@id="content"]/article/div/div[1]/div[1]/div[3]').extract_first("").strip()

        post_content = response.xpath('//*[@id="body"]//div[contains(@class,ArticleRender)]/text()').extract_first("").strip()
        if post_content == '':
            post_content = response.xpath('//*[@id="content"]/article/div/div[2]/div/div[1]').extract_first("").strip()


        if post_content == '' or post_content is None:
            self.log(f"not content found in {response.url}")
            return


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

        # TODO: check this url_object_id if exist in db
        if self.mysqlObj.query_url_object_id(abc_item["url_object_id"]) is not None:
            print(f"url: {abc_item['url']} already exist in db nothing to do.")
            return

        abc_item["category"] = self.mysqlObj.get_news_category(self.name, abc_item["topic"])

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

        post_content = str(soup)
        abc_item["origin_content"] = post_content


        if abc_item["url"] != "" and abc_item["origin_title"] != "" and abc_item["origin_content"] != "":
            yield abc_item
        else:
            print("nothing to do due to invalid item: ", abc_item)


    # check if it is detail url or not by search the year-month-day
    # https://www.abc.net.au/news/2025-02-09/sam-konstas-the-gabba-new-south-wales-queensland/104915602
    def _check_detail_page_by_url(self, url):
        m = re.search(r'(20\d{2})[/:-]([0-1]?\d)[/:-]([0-3]?\d)', url)
        res = ' '.join(m.groups()) if m else None
        return res

