import time
import scrapy
from bs4 import BeautifulSoup
import logging
from newsau.items import NytimesDataItem
from newsau.utils import common
from scrapy_redis.spiders import RedisSpider
from scrapy.selector import Selector
from urllib.parse import urljoin, urlparse
from newsau.db import orm
from newsau.settings import REDIS_URL
from redis import Redis
from newsau.cache import url_queue, rcount
from newsau.settings import NEWS_ACCOUNTS
import re

logger = logging.getLogger('nytimes')

class NYTimesSpider(RedisSpider):
    name = "nytimes"
    redis_key = "nytimesspider:start_urls"
    homepage = "https://www.nytimes.com/section/world/australia"
    seen = set()
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'COOKIES_ENABLED': True,
    }
    redis_batch_size = 1

    def __init__(self, *args, **kwargs):
        # 允许的域名
        self.allowed_domains = ["www.nytimes.com", "nytimes.com", "static01.nyt.com"]
        self.domain = "https://www.nytimes.com/"
        self.retry = 3
        super().__init__(*args, **kwargs)
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)
        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS.get(self.name, {}).get("count_everyday", 100))
        logger.info(f'current count_everyday is:{self.count.get_value()}')

        # lpush 一条测试的数据 redis-cli lpush 'economistspider:start_urls' '{ "url": "https://www.economist.com/", "meta": {}}'
        self.r.lpush(self.redis_key, '{ "url": "https://www.nytimes.com/section/world/australia", "meta": {}}')

        self.seen_key = f"{self.name}:seen_urls"
        seen_count = self.r.scard(self.seen_key)
        if seen_count > 10000:
            logger.warning(f'Seen URLs count ({seen_count}) exceeds 10000, clearing Redis seen data')
            self.r.delete(self.seen_key)
            self.seen = set()
        else:
            self.seen = set(self.r.smembers(self.seen_key))
        logger.info(f'Loaded {len(self.seen)} seen URLs from Redis')

    def add_to_seen(self, url):
        self.seen.add(url)
        self.r.sadd(self.seen_key, url)

    def clear_seen(self):
        self.r.delete(self.seen_key)
        self.seen.clear()
        logger.info('Cleared seen URLs from Redis')

    def start_requests(self):
        for url_data in self.r.lrange(self.redis_key, 0, -1):
            logger.info(f'start_requests url_data:{url_data}')
            try:
                import json
                if url_data.startswith('{'):
                    data = json.loads(url_data)
                    url = data.get('url', '')
                else:
                    url = url_data
                if url:
                    logger.info(f'start_requests parsed url:{url}')
                    yield self._build_request(url, callback=self.parse)
                else:
                    logger.warning(f'Invalid URL data: {url_data}')
            except Exception as e:
                logger.error(f'Error parsing URL data: {url_data}, error: {e}')

    def _build_request(self, url, callback, **kwargs):
        logger.info(f'build_request url: {url}')
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            logger.info(f'build_request parsed domain: {domain}')
            if not domain:
                logger.error(f'Could not extract domain from URL: {url}')
                return None
        except Exception as e:
            logger.error(f'Error parsing URL {url}: {e}')
            return None
        domain_md5 = common.get_md5(domain)
        cookie_key = f"cookie:{domain_md5}"
        logger.info(f'build_request cookie_key: {cookie_key}')
        raw = self.r.hget(cookie_key, "value") or ""
        if not raw:
            logger.warning(f"No cookies found for domain {domain} (key: {cookie_key}), skipping request: {url}")
            logger.info(f"请先运行以下命令将cookie写入Redis:")
            logger.info(f"redis-cli hset '{cookie_key}' value 'your_cookie_string_here'")
            return None
        logger.info(f'build_request raw cookie length: {len(raw)}')
        cookie_dict = self._parse_raw_cookie(raw)
        logger.debug(f"Parsed cookies for {domain}: {len(cookie_dict)} cookies")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nytimes.com/section/world/australia",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            # "Host": "www.nytimes.com",  # Host 通常不用手动加
        }
        return scrapy.Request(
            url=url,
            callback=callback,
            cookies=cookie_dict,
            headers=headers,
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
        if url == self.homepage.rstrip('/'):
            logger.info("Detected homepage — extracting first valid article link")
            for rel in response.css('a[href^="/"]::attr(href)').getall():
                if rel in self.seen:
                    continue
                if not self.is_valid_news_url(rel):
                    continue
                abs_url = urljoin(self.domain, rel)
                if orm.query_object_id(self.name, common.get_md5(abs_url)):
                    continue
                self.add_to_seen(rel)
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
                return
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

    def is_valid_news_url(self, url):
        if url.startswith('http'):
            from urllib.parse import urlparse
            path = urlparse(url).path
        else:
            path = url
        pattern1 = r'^/world/australia/\d{4}/\d{2}/\d{2}/[a-zA-Z0-9\-_]+\.html$'
        pattern2 = r'^/\d{4}/\d{2}/\d{2}/world/australia/[a-zA-Z0-9\-_]+\.html$'
        if re.match(pattern1, path) or re.match(pattern2, path):
            logger.debug(f'Valid news URL: {url}')
            return True
        else:
            logger.debug(f'Invalid news URL: {url}')
            return False

    def detail_parse(self, response):
        body = Selector(text=response.text)
        nytimes_item = NytimesDataItem()
        nytimes_item["name"] = self.name
        nytimes_item["priority"] = response.meta.get('is_priority', False)
        nytimes_item["url"] = response.url
        nytimes_item["url_object_id"] = common.get_md5(nytimes_item["url"])
        # 1. 标题
        title = body.xpath('//header//h1/text()').get('')
        if not title:
            logger.warning(f'No title found for URL: {response.url}')
            return
        nytimes_item["origin_title"] = title.strip()
        # 2. 摘要
        summary_html = body.xpath('//header//p[@id="article-summary"]').get('')
        # 3. 头图
        imageblock_html = body.xpath('//header//div[@data-testid="imageblock-wrapper"]').get('')
        # 4. 正文
        article_section_html = body.xpath('//section[@name="articleBody"]').get('')
        # 5. 拼接内容
        content_html = (summary_html or '') + (imageblock_html or '') + (article_section_html or '')
        # 6. 用BeautifulSoup清洗广告
        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(content_html, "html.parser")
        # 移除Dropzone广告
        for div in soup.find_all('div', attrs={'data-testid': re.compile(r'^Dropzone-\\d+$')}):
            div.decompose()
        # 移除所有 <style> 标签
        for style in soup.find_all('style'):
            style.decompose()
        # 移除所有 <p> 标签中包含 "Your browser does not support" 的内容
        for p in soup.find_all('p'):
            if p.get_text(strip=True).startswith("Your browser does not support"):
                p.decompose()
        # 7. 图片处理
        image_urls = []
        for img in soup.find_all('img'):
            max_url = None
            max_width = 0
            # 解析srcset，选最大宽度
            if img.has_attr('srcset'):
                matches = re.findall(r'(\S+)[\s]+(\d+)w', img['srcset'])
                for url, width in matches:
                    width = int(width)
                    if width > max_width:
                        max_width = width
                        max_url = url
            # 如果没有srcset，直接用src
            if not max_url and img.has_attr('src'):
                max_url = img['src']
            # 收集最大图片原始地址
            if max_url:
                image_urls.append(max_url)
                img['src'] = common.get_finished_image_url(self.name, nytimes_item["url_object_id"], max_url)
            # 移除srcset属性
            if img.has_attr('srcset'):
                del img['srcset']
        image_urls = list(dict.fromkeys(image_urls))
        nytimes_item["front_image_url"] = image_urls
        # 8. a标签处理
        for a in soup.find_all('a'):
            sources = a.find_all('source')
            for source in sources:
                a.insert_before(source)
            a.replace_with(a.get_text())
        nytimes_item["origin_content"] = str(soup)
        nytimes_item["topic"] = 'australia'
        if nytimes_item["url"] and nytimes_item["origin_title"] and nytimes_item["origin_content"]:
            logger.info(f'detail_parse nytimes_item: {nytimes_item}')
            # yield nytimes_item
        else:
            logger.warning(f'Invalid item, missing data: {nytimes_item}') 