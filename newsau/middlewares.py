# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import pickle
import time

from scrapy import signals
import undetected_chromedriver as uc
import selenium.webdriver.support.expected_conditions as EC  # noqa

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import HtmlResponse
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger('liwmiddleware')


class NewsauSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class NewsauDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class NewsSeleniumMiddleware(object):

    def __init__(self, timeout=50):
        self.cookies = pickle.load(open("cookies.pkl", "rb"))
        logger.info(f'pickup cookies:{self.cookies}')
        self.driver = uc.Chrome(headless=True, use_subprocess=True)
        self.add_cookie_flg = False
        # for c in self.cookies:
        #     logger.info(f'add cookie:{c}')
        #     self.driver.add_cookie(c)
        self.timeout = timeout
        self.wait = WebDriverWait(self.driver, self.timeout)

    def __del__(self):
        self.driver.close()


    def process_request(self, request, spider):
        if spider.name == "afr":

            # just do once.
            if self.add_cookie_flg == False:
                self.driver.get(spider.home_url)
                self.add_cookie_flg = True
                for c in self.cookies:
                    logger.info(f'add cookie:{c}')
                    self.driver.add_cookie(c)

            logger.info('afr selenium middleware.')
            self.driver.get(request.url)
            # self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.media-info-title-t')))
            time.sleep(5)
            self.driver.save_screenshot('tt.png')
            url = self.driver.current_url
            body = self.driver.page_source
            return HtmlResponse(url=url, body=body, encoding='utf-8', request=request)

        elif spider.name == "abc":
            logger.info('abc selenium middleware.')
