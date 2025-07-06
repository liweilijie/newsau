from urllib import parse
import logging
import time
import re

import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scrapy.selector import Selector

from newsau.items import AbcDataItem
from newsau.utils import common
from scrapy_redis.spiders import RedisSpider
from newsau.db import orm
from newsau.cache import rcount
from newsau.settings import REDIS_URL
from newsau.settings import NEWS_ACCOUNTS
from redis import Redis

import undetected_chromedriver as uc
import selenium.webdriver.support.expected_conditions as EC  # noqa
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger('abc')

class AbcSpider(RedisSpider):

    name = "abc"
    # be careful primary domain maybe contain other domain to store the image src, so you must remember allowed the domains.
    # allowed_domains = ["abc.net.au", "live-production.wcms.abc-cdn.net.au"]

    # when we use scrapy_redis, so this start_urls don't need it.
    # start_urls = ["https://www.abc.net.au"]
    total_urls = 0
    redis_key = "abcspider:start_urls"
    homepage = "https://www.abc.net.au"
    seen = set()
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

        self.count = rcount.RedisCounter(self.name, REDIS_URL)
        if self.count.get_value() is None or self.count.get_value() <= 0:
            self.count.set_value(NEWS_ACCOUNTS[self.name]["count_everyday"])
        logger.info(f'current count_everyday is:{self.count.get_value()}')

        super().__init__(*args, **kwargs)
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)
        
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

        # 根据操作系统自动选择Chrome和ChromeDriver路径
        import platform
        import os
        
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # macOS上的Chrome路径
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            chromedriver_path = "/usr/local/bin/chromedriver"
            
            # 检查Chrome是否存在，如果不存在则尝试其他路径
            if not os.path.exists(chrome_path):
                # 尝试其他可能的Chrome路径
                possible_chrome_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                    "/usr/bin/google-chrome",
                    "/usr/bin/chromium-browser"
                ]
                
                for path in possible_chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break
                else:
                    logger.warning("未找到Chrome浏览器，请确保已安装Google Chrome")
                    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            # 检查ChromeDriver是否存在
            if not os.path.exists(chromedriver_path):
                logger.warning(f"ChromeDriver不存在于 {chromedriver_path}")
                logger.info("请运行以下命令安装ChromeDriver:")
                logger.info("brew install chromedriver")
                logger.info("或者从 https://chromedriver.chromium.org/ 下载并安装")
                
        elif system == "Linux":
            # Linux上的路径
            chrome_path = "/usr/bin/google-chrome"
            chromedriver_path = "/home/sp/drivers/chromedriver"
            
            # 检查Chrome是否存在
            if not os.path.exists(chrome_path):
                logger.warning(f"Chrome不存在于 {chrome_path}")
                chrome_path = "/usr/bin/google-chrome"
                
        else:  # Windows或其他系统
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            chromedriver_path = "chromedriver.exe"
            
        logger.info(f"使用Chrome路径: {chrome_path}")
        logger.info(f"使用ChromeDriver路径: {chromedriver_path}")

        options = Options()

        options.headless = True  # Linux环境下使用无头模式
        options.add_argument("--log-level=3")  # just show error
        options.add_argument("--silent")  # not show log
        # 显式设置版本匹配
        self.driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_path,
            use_subprocess=False, # 禁用子进程
            version_main=134  # 非常重要，强制使用 Chrome 133 匹配逻辑
        )
        # TODO: use_subprocess
        # self.driver = uc.Chrome(headless=True, use_subprocess=False)
        self.wait = WebDriverWait(self.driver, 20)
        self.js = "window.scrollTo(0, document.body.scrollHeight)"

    def scroll_page_gradually(self, scroll_pause_time=1.5, scroll_step=300):
        """
        模拟人为行为，逐步滚动页面到底部，以便懒加载的图片能够完全加载
        
        Args:
            scroll_pause_time (float): 每次滚动后的暂停时间（秒）
            scroll_step (int): 每次滚动的像素距离
        """
        logger.info("开始逐步滚动页面以加载懒加载内容...")
        
        # 获取页面初始高度
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        scroll_count = 0
        no_change_count = 0
        max_no_change_count = 3
        
        logger.info(f"页面初始高度: {last_height}px")
        
        while True:
            # 逐步滚动
            current_position += scroll_step
            logger.info(f"滚动到位置: {current_position}px (第{scroll_count + 1}次滚动)")
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            
            # 等待页面加载
            time.sleep(scroll_pause_time)
            
            # 检查是否有新内容加载
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"滚动后页面高度: {new_height}px")
            
            # 如果页面高度没有变化，可能已经到底部
            if new_height == last_height:
                no_change_count += 1
                logger.info(f"页面高度未变化，计数: {no_change_count}")
                
                if no_change_count >= max_no_change_count:
                    # 再尝试滚动一次，确保真的到底部
                    logger.info("连续多次高度未变化，尝试最后一次滚动到底部")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_pause_time)
                    final_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if final_height == new_height:
                        logger.info(f"页面滚动完成，总共滚动 {scroll_count} 次")
                        break
                    else:
                        last_height = final_height
                        current_position = final_height
                        no_change_count = 0
                else:
                    last_height = new_height
                    current_position = new_height
            else:
                last_height = new_height
                current_position = new_height
                no_change_count = 0
            
            scroll_count += 1
            
            # 防止无限滚动（最多滚动50次）
            if scroll_count > 50:
                logger.warning("达到最大滚动次数限制，停止滚动")
                break
        
        # 最后滚动到顶部，确保所有内容都已加载
        logger.info("滚动到页面顶部")
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        logger.info("页面滚动和内容加载完成")

    def scroll_page_with_intersection_observer(self, scroll_pause_time=1.0):
        """
        使用Intersection Observer API检测图片加载的滚动方法（更智能）
        
        Args:
            scroll_pause_time (float): 每次滚动后的暂停时间（秒）
        """
        logger.info("使用智能滚动方法加载懒加载内容...")
        
        # 注入JavaScript来监控图片加载
        js_code = """
        return new Promise((resolve) => {
            let loadedImages = 0;
            let totalImages = 0;
            let scrollAttempts = 0;
            const maxScrollAttempts = 30;
            let lastHeight = 0;
            let noChangeCount = 0;
            const maxNoChangeCount = 3;
            
            console.log('开始智能滚动...');
            
            // 创建Intersection Observer来监控图片
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            loadedImages++;
                            console.log('加载图片:', img.src);
                        }
                    }
                });
            }, {
                rootMargin: '100px 0px'
            });
            
            // 监控所有图片
            const images = document.querySelectorAll('img[data-src], img[src*="placeholder"], img[loading="lazy"], img[data-component="Image"]');
            totalImages = images.length;
            console.log('找到图片数量:', totalImages);
            images.forEach(img => imageObserver.observe(img));
            
            // 滚动函数
            function scrollAndWait() {
                console.log('执行滚动函数，当前次数:', scrollAttempts);
                
                if (scrollAttempts >= maxScrollAttempts) {
                    console.log('达到最大滚动次数限制');
                    resolve({loadedImages, totalImages, scrollAttempts});
                    return;
                }
                
                const currentHeight = document.body.scrollHeight;
                console.log('滚动前页面高度:', currentHeight, '当前滚动次数:', scrollAttempts);
                
                window.scrollTo(0, currentHeight);
                scrollAttempts++;
                
                setTimeout(() => {
                    const newHeight = document.body.scrollHeight;
                    console.log('滚动后页面高度:', newHeight);
                    
                    // 检查页面高度是否变化
                    if (newHeight === lastHeight) {
                        noChangeCount++;
                        console.log('页面高度未变化，计数:', noChangeCount);
                    } else {
                        noChangeCount = 0;
                        lastHeight = newHeight;
                    }
                    
                    // 检查是否还有未加载的图片
                    const remainingImages = document.querySelectorAll('img[data-src], img[src*="placeholder"]');
                    console.log('剩余未加载图片:', remainingImages.length);
                    
                    if (remainingImages.length === 0 || noChangeCount >= maxNoChangeCount || scrollAttempts >= maxScrollAttempts) {
                        console.log('滚动完成，最终统计');
                        resolve({loadedImages, totalImages, scrollAttempts});
                    } else {
                        console.log('继续下一次滚动...');
                        scrollAndWait();
                    }
                }, 1500);
            }
            
            // 开始滚动
            scrollAndWait();
        });
        """
        
        try:
            # 先检查页面是否有图片
            check_images_js = """
            const images = document.querySelectorAll('img');
            const lazyImages = document.querySelectorAll('img[data-src], img[src*="placeholder"], img[loading="lazy"], img[data-component="Image"]');
            return {
                totalImages: images.length,
                lazyImages: lazyImages.length,
                pageHeight: document.body.scrollHeight,
                viewportHeight: window.innerHeight
            };
            """
            page_info = self.driver.execute_script(check_images_js)
            logger.info(f"页面信息: 总图片数={page_info['totalImages']}, 懒加载图片数={page_info['lazyImages']}, 页面高度={page_info['pageHeight']}px, 视窗高度={page_info['viewportHeight']}px")
            
            result = self.driver.execute_script(js_code)
            self._last_scroll_attempts = result['scrollAttempts']
            logger.info(f"智能滚动完成：加载了 {result['loadedImages']}/{result['totalImages']} 张图片，滚动 {result['scrollAttempts']} 次")
        except Exception as e:
            logger.warning(f"智能滚动失败，回退到普通滚动方法: {e}")
            self.scroll_page_gradually(scroll_pause_time)
            
    def force_scroll_40_times(self, scroll_pause_time=3.0):
        """
        强制滚动40次，每次滚动一屏高度，确保所有图片都被加载
        """
        logger.info("开始强制滚动40次...")
        
        # 获取视窗高度
        viewport_height = self.driver.execute_script("return window.innerHeight")
        logger.info(f"视窗高度: {viewport_height}px")
        
        # 先滚动到顶部确保起始位置
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 无条件滚动40次，每次滚动一屏高度
        for i in range(40):
            scroll_count = i + 1
            current_position = scroll_count * viewport_height
            
            logger.info(f"执行第 {scroll_count}/40 次滚动，滚动到位置: {current_position}px")
            
            # 滚动到指定位置
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(scroll_pause_time)
            
            # 检查当前滚动位置和页面高度
            scroll_position = self.driver.execute_script("return window.pageYOffset")
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            logger.info(f"第 {scroll_count} 次滚动后 - 页面高度: {current_height}px, 当前滚动位置: {scroll_position}px")
            
            # 如果已经滚动到底部，继续滚动但不再增加位置
            if scroll_position + viewport_height >= current_height:
                logger.info("已到达页面底部，继续滚动但位置不变")
        
        # 滚动回顶部
        logger.info("滚动到页面顶部")
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 检查最终图片数量
        final_image_count = self.driver.execute_script("""
            const images = document.querySelectorAll('img');
            const lazyImages = document.querySelectorAll('img[data-src], img[src*="placeholder"], img[loading="lazy"], img[data-component="Image"]');
            const loadedImages = document.querySelectorAll('img[src]:not([src*="placeholder"])');
            return {
                totalImages: images.length,
                lazyImages: lazyImages.length,
                loadedImages: loadedImages.length
            };
        """)
        
        logger.info(f"强制滚动完成 - 总图片数: {final_image_count['totalImages']}, 懒加载图片数: {final_image_count['lazyImages']}, 已加载图片数: {final_image_count['loadedImages']}")
        logger.info("强制滚动40次完成")
        
        # 现在执行智能滚动判断
        logger.info("开始智能滚动判断...")
        self.scroll_page_with_intersection_observer(scroll_pause_time=1.0)

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
        for url in self.r.lrange(self.redis_key, 0, -1):
            logger.info(f'start_requests url:{url}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        url = response.url.rstrip('/')
        
        if url == self.homepage:
            logger.info("Detected homepage — extracting all valid article links")
            # 获取所有文章链接 - 更新XPath选择器
            article_links = []
            
            # 查找所有包含新闻链接的a标签
            links = response.xpath('//a[contains(@href, "/news/")]')
            for link in links:
                href = link.xpath('@href').extract_first("").strip()
                if href and self.is_valid_news_url(href):
                    article_links.append(href)
            
            # 去重
            unique_links = list(set(article_links))
            logger.info(f'Found {len(unique_links)} unique valid article links on homepage')
            
            for post_url in unique_links:
                # 跳过已见过的链接
                if post_url in self.seen:
                    logger.info(f'URL already seen: {post_url}')
                    continue
                    
                abs_url = urljoin(self.domain, post_url)
                logger.info(f'Found valid article URL: {abs_url}')
                
                # 跳过已爬取的内容
                if orm.query_object_id(self.name, common.get_md5(abs_url)):
                    logger.info(f'URL already processed: {abs_url}')
                    self.add_to_seen(post_url)  # 标记为已见过
                    continue
                
                # 检查是否包含有效日期
                if not common.contains_valid_date(abs_url):
                    logger.info(f'URL does not contain valid date: {abs_url}')
                    self.add_to_seen(post_url)  # 标记为已见过
                    continue
                
                # 检查是否超过每日限制
                if orm.check_if_exceed_num(self.name, self.count.get_value()):
                    logger.info('Exceeded daily limit, stopping crawl.')
                    return
                
                # 记录已处理链接，生成请求并退出
                self.add_to_seen(post_url)
                yield scrapy.Request(
                    abs_url,
                    callback=self.detail_parse,
                    dont_filter=True,
                    meta={"is_priority": True}
                )
                return  # 抓取首条链接后立即退出
            
            logger.info("No valid new link found on homepage")
        else:
            # 直接处理文章页面
            yield scrapy.Request(
                response.url,
                callback=self.detail_parse,
                dont_filter=True,
                meta={"is_priority": True}
            )

    def is_valid_news_url(self, url):
        """
        验证URL是否符合新闻文章的标准格式
        格式: /news/YYYY-MM-DD/article-title/数字 或 https://www.abc.net.au/news/YYYY-MM-DD/article-title/数字
        例如: /news/2025-07-04/foul-fatbergs-hit-record-levels-in-perth-sewers/105495552
        """
        import re
        
        # 提取路径部分，去掉域名
        if url.startswith('http'):
            # 如果是完整URL，提取路径部分
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
        else:
            # 如果已经是相对路径，直接使用
            path = url
        
        # 正则表达式匹配 /news/日期/标题/数字 的格式
        # 标题部分允许字母、数字、连字符和下划线
        pattern = r'^/news/\d{4}-\d{2}-\d{2}/[a-zA-Z0-9\-_]+/\d+/?$'
        
        if re.match(pattern, path):
            logger.debug(f'Valid news URL: {url}')
            return True
        else:
            logger.debug(f'Invalid news URL: {url}')
            return False

    def detail_parse(self, response):
        is_priority = response.meta.get('is_priority', False)

        if not is_priority and orm.check_if_exceed_num(self.name, self.count.get_value()):
            logger.info('Exceeded daily limit, skipping this URL.')
            return

        logger.info(f'Processing detail page: {response.url}')


        self.driver.get(response.url)
        time.sleep(5)

        # 执行强制滚动40次，然后智能判断
        logger.info("执行强制滚动40次，然后智能判断")
        self.force_scroll_40_times(scroll_pause_time=5.0)

        # 最后滚动到底部确保所有内容都已加载
        self.driver.execute_script(self.js)

        page_text = self.driver.page_source

        # 将response的网页内容写入abc.html 再通过下面的命令用来手动调试
        # scrapy shell 'file:///Volumes/rs/bakup/coding/py/newsau/abc.html' --set SCHEDULER=scrapy.core.scheduler.Scheduler
        with open("abc.html", "w", encoding="utf-8") as f:
            f.write(page_text)
            f.close()

        # logger.debug(f'page_text:{page_text}')

        # pickle.dump(page_text, open("home.html", "wb"))

        body = Selector(text=page_text)

        abc_item = AbcDataItem()
        abc_item["name"] = self.name
        abc_item["priority"] = is_priority
        trim_first_div = False

        if body.xpath("//main[@id='content']/article//div[@data-component='ArticleWeb']"):
            logger.info(f'Processing article page: {response.url}')
            post_title = body.xpath('//*[@id="content"]/article//header//h1/text()').extract_first("").strip()
            if not post_title:
                post_title = body.css('div[data-component="ArticleWeb"] h1::text').extract_first("").strip()

            if not post_title:
                logger.warning(f'No title found for URL: {response.url}')
                # 把首页重新推入 Redis, 重新选择一个链接
                payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
                self.r.lpush(self.redis_key, payload)
                return

            post_topic = body.xpath('//*[@id="content"]/article//header//ul/li//p/text()').extract_first("").strip()
            if post_topic == '':
                post_topic = body.css('div[data-component="ArticleWeb"] li a[data-component="SubjectTag"] p::text').extract_first("").strip()
            if post_topic == '':
                post_topic = body.xpath('//*[@id="content"]/article/div//a[@data-component="InfoSourceTag"]/p/text()').extract_first("").strip()

            post_header = body.xpath('//*[@id="content"]/article/div/div[1]/div[1]/div[3]').extract_first("").strip()

            post_content = body.xpath('//*[@id="body"]//div[contains(@class,ArticleRender)]/text()').extract_first("").strip()
            if not post_content:
                post_content = body.xpath('//*[@id="content"]/article/div/div[2]/div/div[1]').extract_first("").strip()

            if not post_content:
                logger.warning(f'No content found for URL: {response.url}')
                # 把首页重新推入 Redis, 重新选择一个链接
                payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
                self.r.lpush(self.redis_key, payload)
                return

            # data-component = "Timestamp"
            # datetime = "2025-02-10T04:55:05.000Z"
            # //*[@id="content"]/article/div/div[1]/div[1]/div[2]/div/time[1]
            post_time = body.xpath('//time[@data-component="Timestamp"]/@datetime').extract_first("").strip()
            abc_item["post_date"] = common.convert_to_datetime(post_time)

            if post_header != '':
                post_content = post_header + post_content
        else:
            logger.info(f'Processing trim first div article page: {response.url}')
            # 获取主内容区域
            main_content = body.xpath("//main[@id='content']")

            # 再从main_content中提取h1作为标题
            post_title = main_content.xpath("//h1/text()").get()
            
            if not post_title:
                logger.warning(f'No title found for URL: {response.url}')
                # 把首页重新推入 Redis, 重新选择一个链接
                payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
                self.r.lpush(self.redis_key, payload)
                return
            
            trim_first_div = True

            # 然后将main_content中的所有内容提取出来
            post_content = main_content.extract_first("").strip()

            if not post_content:
                logger.warning(f'No content found for URL: {response.url}')
                # 把首页重新推入 Redis, 重新选择一个链接
                payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
                self.r.lpush(self.redis_key, payload)
                return

            # 在else分支中添加缺失的变量定义
            post_topic = ""  # 初始化post_topic
            post_header = ""  # 初始化post_header
            post_time = body.xpath('//time[@data-component="Timestamp"]/@datetime').extract_first("").strip()
            abc_item["post_date"] = common.convert_to_datetime(post_time)

        abc_item["origin_title"] = post_title
        abc_item["topic"] = post_topic
        abc_item["url"] = response.url
        abc_item["url_object_id"] = common.get_md5(abc_item["url"])

        if orm.query_object_id(self.name, abc_item["url_object_id"]):
            logger.info(f'URL already processed: {abc_item["url"]}')
            # 把首页重新推入 Redis, 重新选择一个链接
            payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
            self.r.lpush(self.redis_key, payload)
            return

        abc_item["front_image_url"] = []

        # 添加正则表达式定义
        import re
        pattern_size = re.compile(r"width=(\d+)&height=(\d+)")
        pattern_id = re.compile(r"/([\da-f]{32})\?")  # 提取图片唯一ID

        # 用于去重的字典，记录每张图片的最大尺寸版本
        image_dict = dict()

        # process the content
        # find all the images src in the post_content
        # and store these images src
        # and replace the domain of the src in post_content
        soup = BeautifulSoup(post_content,"html.parser")

        if trim_first_div:
            # trim the first div
            soup.find('div').decompose()

        # 处理HTML中的所有img标签，替换为处理后的链接
        for img in soup.findAll('img'):
            if img.get('src'):
                # 提取图片ID和尺寸
                url = img['src']
                m_id = pattern_id.search(url)
                m_size = pattern_size.search(url)
                
                if m_id:
                    image_id = m_id.group(1)
                    width = int(m_size.group(1)) if m_size else 0
                    height = int(m_size.group(2)) if m_size else 0
                    pixels = width * height
                    
                    # 只保留最大尺寸的版本
                    if image_id not in image_dict or pixels > image_dict[image_id]["pixels"]:
                        image_dict[image_id] = {
                            "url": url,
                            "width": width,
                            "height": height,
                            "pixels": pixels
                        }
                else:
                    # 如果无法提取ID，直接添加
                    abc_item["front_image_url"].append(img['src'])
                    # 用原始URL生成new_url
                    img['src'] = common.get_finished_image_url(self.name, abc_item["url_object_id"], img['src'])
        
        # 处理picture标签中的source标签，只保留一张图片
        source_count = 0
        initial_source_count = len(soup.findAll('source'))
        logger.info(f"开始处理前，HTML中有{initial_source_count}个source标签")
        
        # 收集所有独立的source标签（不在picture内的）
        standalone_sources = []
        
        for source in soup.findAll('source'):
            source_count += 1
            if source.get('srcset'):
                logger.info(f"处理第{source_count}个source标签: {source['srcset']}")
                
                # 检查source标签是否在picture标签内
                parent = source.parent
                if parent and parent.name != 'picture':
                    # 这是一个独立的source标签，需要包装在picture标签中
                    standalone_sources.append(source)
                    continue
                
                # 从srcset中找到最大尺寸的图片
                srcset_parts = source['srcset'].split(',')
                max_url = None
                max_pixels = 0
                
                for part in srcset_parts:
                    if part.strip():
                        url_part = part.strip().split()[0]  # 获取URL部分
                        # 提取尺寸信息
                        size_info = ' '.join(part.strip().split()[1:]) if len(part.strip().split()) > 1 else ''
                        
                        # 尝试从URL中提取尺寸
                        m_size = pattern_size.search(url_part)
                        m_id = pattern_id.search(url_part)
                        
                        if m_size and m_id:
                            width = int(m_size.group(1))
                            height = int(m_size.group(2))
                            pixels = width * height
                            image_id = m_id.group(1)
                            
                            # 只保留最大尺寸的版本
                            if image_id not in image_dict or pixels > image_dict[image_id]["pixels"]:
                                image_dict[image_id] = {
                                    "url": url_part,
                                    "width": width,
                                    "height": height,
                                    "pixels": pixels
                                }
                            
                            if pixels > max_pixels:
                                max_pixels = pixels
                                max_url = url_part
                        else:
                            # 如果无法提取ID或尺寸，直接添加到front_image_url
                            abc_item["front_image_url"].append(url_part)
                
                # 如果找到了最大尺寸的图片，替换srcset
                if max_url:
                    # 生成新的URL并替换srcset
                    new_url = common.get_finished_image_url(self.name, abc_item["url_object_id"], max_url)
                    # 只保留这一张图片
                    source['srcset'] = new_url
                    logger.info(f"更新source标签srcset: {new_url}")
        
        # 处理独立的source标签，将它们包装在picture标签中
        for source in standalone_sources:
            # 创建picture标签
            picture_tag = soup.new_tag('picture')
            
            # 创建img标签作为后备
            img_tag = soup.new_tag('img')
            if source.get('srcset'):
                # 从srcset中提取URL
                srcset_parts = source['srcset'].split(',')
                if srcset_parts:
                    img_url = srcset_parts[0].strip().split()[0]
                    img_tag['src'] = img_url
                    img_tag['alt'] = 'Image'
            
            # 将img标签添加到picture标签内
            picture_tag.append(img_tag)
            
            # 将source标签移动到picture标签内
            source.extract()
            picture_tag.append(source)
            
            # 将picture标签插入到原source标签的位置
            source.parent.insert_before(picture_tag)
        
        logger.info(f"总共处理了{source_count}个source标签，其中{len(standalone_sources)}个被包装在picture标签中")
        
        # 检查处理后的source标签数量
        after_process_source_count = len(soup.findAll('source'))
        logger.info(f"处理完成后，HTML中有{after_process_source_count}个source标签")
        
        # 将去重后的图片添加到front_image_url
        for img in image_dict.values():
            abc_item["front_image_url"].append(img["url"])
        
        # 更新所有img标签的src，使用去重后的URL生成new_url
        for img in soup.findAll('img'):
            if img.get('src'):
                url = img['src']
                m_id = pattern_id.search(url)
                if m_id:
                    image_id = m_id.group(1)
                    # 找到对应的去重后的URL
                    for img_info in image_dict.values():
                        img_info_id = pattern_id.search(img_info["url"])
                        if img_info_id and img_info_id.group(1) == image_id:
                            # 用去重后的URL生成new_url
                            img['src'] = common.get_finished_image_url(self.name, abc_item["url_object_id"], img_info["url"])
                            break
        
        logger.info(f"去重后的图片数量: {len(abc_item['front_image_url'])}")

        # 检查清理操作前的source标签数量
        before_cleanup_source_count = len(soup.findAll('source'))
        logger.info(f"清理操作前，HTML中有{before_cleanup_source_count}个source标签")

        # find all a label, but preserve source tags inside
        for a in soup.find_all('a'):
            # 检查a标签内是否有source标签
            source_tags = a.find_all('source')
            if source_tags:
                # 如果有source标签，保留它们
                for source in source_tags:
                    # 将source标签移到a标签外面
                    a.parent.insert_before(source)
                # 然后删除a标签，但保留其文本内容
                a.replace_with(a.text)
            else:
                # 如果没有source标签，直接替换为文本
                a.replace_with(a.text)

        # trim div data-component="EmbedBlock"
        # for div in soup.find_all('div', {"data-component":"EmbedBlock"}):
        #     div.decompose()

        # trim div data-component="InlineSubscribe"
        for div in soup.find_all('div', {"data-component":"InlineSubscribe"}):
            div.decompose()

        # trim p class="FormatCredit"
        for p in soup.find_all('p', {"class":"FormatCredit"}):
            p.decompose()

        # trim div role="dialog"
        for div in soup.find_all('div', {"role":"dialog"}):
            div.decompose()


        # trim span data-component="Loading" data-print="inline-media"
        for span in soup.find_all('span', {"data-component":"Loading"}):
            span.decompose()

        # trim div data-component="ZendeskForm"
        for div in soup.find_all('div', {"data-component":"ZendeskForm"}):
            div.decompose()

        # 检查清理操作后的source标签数量
        after_cleanup_source_count = len(soup.findAll('source'))
        logger.info(f"清理操作后，HTML中有{after_cleanup_source_count}个source标签")

        post_content = str(soup)
        abc_item["origin_content"] = post_content
        
        # 检查最终HTML中是否还有source标签
        final_soup = BeautifulSoup(post_content, "html.parser")
        final_source_count = len(final_soup.findAll('source'))
        logger.info(f"最终HTML中的source标签数量: {final_source_count}")
        if final_source_count > 0:
            for i, source in enumerate(final_soup.findAll('source')):
                logger.info(f"最终HTML中第{i+1}个source标签: {source}")

        if abc_item["url"] != "" and abc_item["origin_title"] != "" and abc_item["origin_content"] != "":
            logger.info(f'Processing item: {abc_item}')
            # 打印多少张图片
            logger.info(f'{len(abc_item["front_image_url"])} images found')
            yield abc_item
        else:
            logger.warning(f'Invalid item, missing data: {abc_item}')
            # 把首页重新推入 Redis, 重新选择一个链接
            payload = '{"url": "' + self.homepage + '", "meta": {"schedule_num":1}}'
            self.r.lpush(self.redis_key, payload)