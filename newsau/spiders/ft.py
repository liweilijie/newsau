import logging

import scrapy
from scrapy import Selector
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from redis import Redis

from newsau.db import orm
from newsau.utils import common
from newsau.items import FtDataItem
from scrapy_redis.spiders import RedisSpider
from newsau.settings import REDIS_URL
from newsau.cache import url_queue
from newsau.cache import rcount
from newsau.settings import NEWS_ACCOUNTS

logger = logging.getLogger('ft')

class FtSpider(RedisSpider):

    name = "ft"
    redis_key = "ftspider:start_urls"
    homepage = "https://www.ft.com"
    seen = set()
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/132.0.0.0 Safari/537.36',
        'COOKIES_ENABLED': True,
    }
    # Number of url to fetch from redis on each attempt
    # Update this as needed - this will be 16 by default (like the concurrency default)

    def __init__(self, *args, **kwargs):
        domain = kwargs.pop("ft.com", "")
        self.allowed_domains = list(filter(None, domain.split(",")))
        super().__init__(*args, **kwargs)
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)

        self.queue = url_queue.RedisUrlQueue(self.name, REDIS_URL)
        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS[self.name]["count_everyday"])
        logger.info(f'current count_everyday is:{self.count.get_value()}')

    def start_requests(self):
        for url in self.r.lrange(self.redis_key, 0, -1):
            logger.info(f'start_requests url:{url}')
            yield self._build_request(url, callback=self.parse)

    def _build_request(self, url, callback, **kwargs):
        domain = urlparse(url).netloc
        # logger.info(f'build_request domain:{domain}')
        raw = self.r.get(f"cookies:{domain}:raw") or ""
        if not raw:
            logger.warning(f"No cookies found for domain {domain}, skipping request: {url}")
            return None  # 不构造Request，直接跳过
        # logger.info(f'build_request raw:{raw}')
        cookie_dict = self._parse_raw_cookie(raw)
        # logger.debug(f"Parsed cookies for {domain}: {cookie_dict}")
        return scrapy.Request(
            url=url,
            callback=callback,
            cookies=cookie_dict,
            **kwargs
        )

    def _parse_raw_cookie(self, raw):
        d = {}
        for part in raw.split(';'):
            if '=' in part:
                k, v = part.strip().split('=', 1)
                d[k] = v
        return d

    def parse(self, response):
        url = response.url.rstrip('/')
        homepage = "https://www.ft.com"
        if url == homepage:
            logger.info("Detected homepage — extracting first valid article link")
            # 获取所有文章链接
            for rel in response.css(
                    'a[data-trackable="heading-link"][href^="/content/"]::attr(href)'
            ).getall():
                if rel in self.seen:
                    continue
                abs_url = urljoin(homepage, rel)

                # 跳过已爬取的内容
                if orm.query_object_id(self.name, common.get_md5(abs_url)):
                    continue

                # 记录已处理链接，生成请求并退出
                self.seen.add(rel)
                req = self._build_request(
                    abs_url,
                    callback=self.detail_parse,
                    dont_filter=True,
                    meta={"is_priority": True}
                )
                if req:
                    yield req
                else:
                    logger.warning(f"Skipped building request for {abs_url} due to missing cookies")
                return  # 抓取首条链接后立即退出

            logger.info("No valid new link found on homepage")
        else:
            req = self._build_request(
                response.url,
                callback=self.detail_parse,
                dont_filter=True,
                meta={"is_priority": True}
            )
            if req:
                yield req

    def detail_parse(self, response):
        logger.info(f'Processing detail page: {response.url}')
        # logger.info(f'content:{response.text}')

        # filename = 'ft.html'
        # with open(filename, 'w', encoding='utf-8') as f:
        #     f.write(response.text)
        # logger.info(f"Saved HTML to {filename}")

        ft_item = FtDataItem()
        ft_item["name"] = self.name
        ft_item["priority"] = True

        # park_item["topic"] = post_topic
        ft_item["url"] = response.url
        ft_item["url_object_id"] = common.get_md5(ft_item["url"])

        if orm.query_object_id(self.name, ft_item["url_object_id"]):
            return

        ft_item["post_date"] = common.extract_datetime(None)

        sel = Selector(text=response.text)
        title = sel.xpath('//h1[contains(@class,"o-topper__headline")]/span/text()').get()
        ft_item["origin_title"] = title
        full_html = sel.xpath('//article[@id="article-body"]').extract_first()
        if not full_html:
            logger.warning(f"{response.url}: No article-body found")
            # 把首页重新推入 Redis, 重新选择一个链接
            payload = '{"url": "https://www.ft.com", "meta": {"schedule_num":1}}'
            self.r.lpush(self.redis_key, payload)
            return

        article_body, originals, cdns = self.process_article_images(full_html, ft_item["url_object_id"])
        ft_item["front_image_url"] = originals or []
        ft_item["origin_content"] = article_body

        # logger.info(f"article_body:{article_body}")
        # logger.info(f"originals:{originals}")
        # logger.info(f"cdns:{cdns}")

        if ft_item["url"] != "" and ft_item["origin_title"] != "" and ft_item["origin_content"] != "":
            # logger.info(f"ft:{ft_item}")
            yield ft_item
        else:
            logger.warning(f'Invalid item, missing data: {ft_item}')

    def process_article_images(self, html_content: str, url_object_id: str):
        """
        处理 <article> 内图片：
          - 删除 <picture> 下的 <source>；
          - 替换 <img> 的 src 为 CDN 地址；
          - 删除 srcset, data-pb-im-config 等不必要属性；
        返回处理后的 HTML + 原图 / CDN 图 列表。
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # ——— 删除视频区域更清晰精准 ———
        # 删除视频容器
        for video_div in soup.find_all("div", class_="cp-clip__video-container"):
            video_div.decompose()
        # 删除视频下方描述区域
        for meta_div in soup.find_all("div", class_="cp-clip__video-meta-info"):
            meta_div.decompose()

        # find all a label
        for a in soup.find_all('a'):
            # replace all a label with its text
            a.replace_with(soup.new_string(a.get_text()))

        # 删除 <picture> 下的所有 <source>
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                logger.debug(f"delete source: {source}")
                source.decompose()

        original_urls = []
        cdn_urls = []

        # 处理所有 <img> 标签
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue

            if src.startswith("http") or src.startswith("https"):
                original_urls.append(src)
                # 构造 CDN URL
                new_src = common.get_finished_image_url(self.name, url_object_id, src)
                cdn_urls.append(new_src)

                # 替换 src
                img['src'] = new_src

                # 删除不必要属性
                for attr in ['srcset', 'data-pb-im-config']:
                    if attr in img.attrs:
                        logger.debug(f"delete {attr}: {img.attrs.get(attr)}")
                        del img.attrs[attr]

        # 返回新的 HTML
        return str(soup), original_urls, cdn_urls