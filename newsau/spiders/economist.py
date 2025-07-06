import time
import scrapy
from bs4 import BeautifulSoup
import logging
from newsau.items import EconomistDataItem
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

logger = logging.getLogger('economist')

class EconomistSpider(RedisSpider):

    name = "economist"
    redis_key = "economistspider:start_urls"
    homepage = "https://www.economist.com"
    seen = set()
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'COOKIES_ENABLED': True,
    }
    redis_batch_size = 1

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        # domain = kwargs.pop("economist.com", "static.ffx.io")
        self.allowed_domains = ["www.economist.com", "economist.com", "cdn.china.com.au"]

        self.domain = "https://www.economist.com/"
        self.retry = 3

        super().__init__(*args, **kwargs)
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)
        
        # 初始化队列和计数器
        self.queue = url_queue.RedisUrlQueue(self.name, REDIS_URL)
        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS[self.name]["count_everyday"])
        logger.info(f'current count_everyday is:{self.count.get_value()}')
        
        # lpush 一条测试的数据 redis-cli lpush 'economistspider:start_urls' '{ "url": "https://www.economist.com/", "meta": {}}'
        # self.r.lpush(self.redis_key, '{ "url": "https://www.economist.com/", "meta": {}}')
        
        # 从Redis加载已见过的URL
        self.seen_key = f"{self.name}:seen_urls"
        
        # 检查seen数据量，如果超过1万条则清理
        seen_count = self.r.scard(self.seen_key)
        if seen_count > 10000:
            logger.warning(f'Seen URLs count ({seen_count}) exceeds 10000, clearing Redis seen data')
            self.r.delete(self.seen_key)
            self.seen = set()
        else:
            self.seen = set(self.r.smembers(self.seen_key))
            
        logger.info(f'Loaded {len(self.seen)} seen URLs from Redis')

    def add_to_seen(self, url):
        """将URL添加到已见过的集合中，同时保存到Redis"""
        self.seen.add(url)
        self.r.sadd(self.seen_key, url)

    def clear_seen(self):
        """清理已见过的URL集合（可选，用于重置）"""
        self.r.delete(self.seen_key)
        self.seen.clear()
        logger.info('Cleared seen URLs from Redis')

    def start_requests(self):
        for url_data in self.r.lrange(self.redis_key, 0, -1):
            logger.info(f'start_requests url_data:{url_data}')
            
            # 解析URL数据
            try:
                import json
                if url_data.startswith('{'):
                    # JSON格式
                    data = json.loads(url_data)
                    url = data.get('url', '')
                else:
                    # 直接URL格式
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
        
        # 解析URL获取domain
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
        
        # 从Redis获取cookie，使用md5(domain)作为key
        domain_md5 = common.get_md5(domain)
        cookie_key = f"cookie:{domain_md5}"
        logger.info(f'build_request cookie_key: {cookie_key}')
        
        # 修改这里，读取 hash 的 value 字段
        raw = self.r.hget(cookie_key, "value") or ""
        
        if not raw:
            logger.warning(f"No cookies found for domain {domain} (key: {cookie_key}), skipping request: {url}")
            logger.info(f"请先运行以下命令将cookie写入Redis:")
            logger.info(f"redis-cli hset '{cookie_key}' value 'your_cookie_string_here'")
            return None  # 不构造Request，直接跳过
            
        logger.info(f'build_request raw cookie length: {len(raw)}')
        cookie_dict = self._parse_raw_cookie(raw)
        logger.debug(f"Parsed cookies for {domain}: {len(cookie_dict)} cookies")
        
        return scrapy.Request(
            url=url,
            callback=callback,
            cookies=cookie_dict,
            **kwargs
        )

    def _parse_raw_cookie(self, raw):
        """解析原始cookie字符串为字典格式"""
        d = {}
        for part in raw.split(';'):
            if '=' in part:
                k, v = part.strip().split('=', 1)
                d[k] = v
        return d

    def parse(self, response):
        url = response.url.rstrip('/')
        
        if url == self.homepage:
            logger.info("Detected homepage — extracting first valid article link")
            # 获取所有文章链接
            for rel in response.css('a[href^="/"]::attr(href)').getall():
                if rel in self.seen:
                    continue
                    
                # 验证是否为有效的新闻URL
                if not self.is_valid_news_url(rel):
                    continue
                    
                abs_url = urljoin(self.homepage, rel)

                # 跳过已爬取的内容
                if orm.query_object_id(self.name, common.get_md5(abs_url)):
                    continue

                # 记录已处理链接，生成请求并退出
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

    def is_valid_news_url(self, url):
        """
        验证URL是否符合新闻文章的标准格式
        格式: /section/YYYY/MM/DD/article-title 或 https://www.economist.com/section/YYYY/MM/DD/article-title
        例如: /leaders/2025/07/03/trumponomics-20-will-erode-the-foundations-of-americas-prosperity
        """
        
        # 提取路径部分，去掉域名
        if url.startswith('http'):
            # 如果是完整URL，提取路径部分
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
        else:
            # 如果已经是相对路径，直接使用
            path = url
        
        # 正则表达式匹配 /section/YYYY/MM/DD/标题 的格式
        # section部分允许字母、数字、连字符和下划线
        # 标题部分允许字母、数字、连字符和下划线
        pattern = r'^/[a-zA-Z0-9\-_]+/\d{4}/\d{2}/\d{2}/[a-zA-Z0-9\-_]+/?$'
        
        if re.match(pattern, path):
            logger.debug(f'Valid news URL: {url}')
            return True
        else:
            logger.debug(f'Invalid news URL: {url}')
            return False

    def detail_parse(self, response):
        # 保存原始HTML方便调试
        # with open('economist.html', 'w', encoding='utf-8') as f:
        #     f.write(response.text)

        body = Selector(text=response.text)
        economist_item = EconomistDataItem()
        economist_item["name"] = self.name
        economist_item["priority"] = response.meta.get('is_priority', False)
        economist_item["url"] = response.url
        economist_item["url_object_id"] = common.get_md5(economist_item["url"])

        # 1. 判断是哪种模板
        template_xpath = '//*[@id="new-article-template"]/div[@data-test-id]'
        template_div = body.xpath(template_xpath)
        template_type = template_div.xpath('./@data-test-id').get('')

        # 2. 提取标题
        if template_type == "standard-article-template":
            title = body.xpath(
                '//*[@id="new-article-template"]/div[@data-test-id="standard-article-template"]/div/div[1]//h1/text()'
            ).get('').strip()
        elif template_type == "enhanced-article-template":
            title = body.xpath(
                '//*[@id="new-article-template"]/div[@data-test-id="enhanced-article-template"]/div[1]//h1/text()'
            ).get('').strip()
        else:
            title = ''
        if not title:
            logger.warning(f'No title found for URL: {response.url}')
            return
        economist_item["origin_title"] = title

        # 3. 提取内容
        if template_type == "standard-article-template":
            content_div2 = body.xpath(
                '//*[@id="new-article-template"]/div[@data-test-id="standard-article-template"]/div/div[2]'
            ).get('')
            section_p_list = body.xpath(
                '//*[@id="new-article-template"]/div[@data-test-id="standard-article-template"]/div/div[3]/div[1]/section//p'
            ).getall()
            if section_p_list:
                section_p_list = section_p_list[:-1]
            content_div3 = ''.join(section_p_list)
            content_html = (content_div2 or '') + (content_div3 or '')
        elif template_type == "enhanced-article-template":
            # enhanced模板正文：第二个div下所有section里的p标签
            section_p_list = body.xpath(
                '//*[@id="new-article-template"]/div[@data-test-id="enhanced-article-template"]/div[2]//section//p'
            ).getall()
            if section_p_list:
                section_p_list = section_p_list[:-1]
            content_html = ''.join(section_p_list)
        else:
            content_html = ''

        # 后续图片处理和内容赋值逻辑不变
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content_html, "html.parser")
        # 移除所有 <style> 标签
        for style in soup.find_all('style'):
            style.decompose()
        image_urls = []
        for img in soup.find_all('img'):
            max_url = None
            max_width = 0
            if img.has_attr('srcset'):
                srcset = img['srcset']
                matches = re.findall(r'(\S+)\s+(\d+)w', srcset)
                for url, width in matches:
                    width = int(width)
                    if width > max_width:
                        max_width = width
                        max_url = url
                if max_url:
                    image_urls.append(max_url)
                    img['src'] = common.get_finished_image_url(self.name, economist_item["url_object_id"], max_url)
                del img['srcset']
            else:
                if img.has_attr('src'):
                    img_url = img['src']
                    image_urls.append(img_url)
                    img['src'] = common.get_finished_image_url(self.name, economist_item["url_object_id"], img_url)
        image_urls = list(dict.fromkeys(image_urls))
        economist_item["front_image_url"] = image_urls

        # 先移出a标签内的source，再去除a标签
        for a in soup.find_all('a'):
            sources = a.find_all('source')
            for source in sources:
                a.insert_before(source)
            a.replace_with(a.get_text())

        # 移除所有 <p> 标签中包含 "Your browser does not support" 的内容
        for p in soup.find_all('p'):
            if p.get_text(strip=True).startswith("Your browser does not support"):
                p.decompose()

        economist_item["origin_content"] = str(soup)
        economist_item["topic"] = 'financial'

        if economist_item["url"] and economist_item["origin_title"] and economist_item["origin_content"]:
            logger.info(f'detail_parse economist_item: {economist_item}')
            yield economist_item
        else:
            logger.warning(f'Invalid item, missing data: {economist_item}')