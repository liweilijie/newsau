import pickle
import time
from typing import Any

import scrapy
from bs4 import BeautifulSoup
import logging

from scrapy.http import Response

from newsau.items import AfrDataItem
from newsau.utils import common
from newsau.db import mysqldb
from newsau.settings import NEWS_ACCOUNTS
from scrapy_redis.spiders import RedisSpider
import undetected_chromedriver as uc
import selenium.webdriver.support.expected_conditions as EC  # noqa
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from scrapy.selector import Selector
from newsau.settings import AFR_USER, AFR_PASSWORD
from urllib.parse import urljoin
from newsau.parse import afrparse

logger = logging.getLogger('afr')

class AfrSpider(RedisSpider):
    name = "afr"
    home_url = "https://afr.com"
    # allowed_domains = ["afr.com"]
    # start_urls = ["https://afr.com"]
    custom_settings = {
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    }

    total_urls = 0
    redis_key = "afrspider:start_urls"

    # Number of url to fetch from redis on each attempt
    # Update this as needed - this will be 16 by default (like the concurrency default)
    redis_batch_size = 1


    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        # Be careful primary domain maybe contain other domain to store the image src, so you must remember allowed the domains.
        domain = kwargs.pop("afr.com", "static.ffx.io")
        self.allowed_domains = filter(None, domain.split(","))
        self.mysqlObj = mysqldb.MySqlObj() # for find the object_url_id duplicate
        self.home_url = "afr.com"
        self.domain = "https://www.afr.com/"

        # self.driver = uc.Chrome(headless=False, use_subprocess=True)
        # self.wait = WebDriverWait(self.driver, 1, 0.5)
        self.retry = 3
        self.cookies = None

        self.user = AFR_USER
        self.password = AFR_PASSWORD
        # TODO: use_subprocess
        self.driver = uc.Chrome(headless=False, use_subprocess=False)
        self.wait = WebDriverWait(self.driver, 20)
        self.is_login = False
        self.js = "window.scrollTo(0, document.body.scrollHeight)"

        self.headers = {
            'Referer': 'https://www.afr.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'

        }

        # try:
        #     self.cookies = pickle.load(open("cookies.pkl", "rb"))
        # except Exception as e:
        #     logger.error(f"pickup load cookies error:{e}")
        #     self.cookies = None
        #
        # if self.cookies is None:
        #     raise "cookies cannot find."
        #
        # logger.info(f'read cookies:{self.cookies}')


        # self.mysqlObj = mysqldb.MySqlObj() # for find the object_url_id duplicate
        super().__init__(*args, **kwargs)


    # def start_requests(self):
    #     self.login()
    #
    #     url = 'https://www.afr.com/world/middle-east/trump-may-be-wrong-about-many-things-but-he-s-right-about-hamas-20250212-p5lbgn'
    #     yield scrapy.Request(url=url, cookies=self.cookies, callback=self.detail_parse, dont_filter=True)

    # def parse(self, response):
    #     print(response.url)
    #     yield scrapy.Request(url=response.url, headers=self.headers, cookies=self.cookies, callback=self.detail_parse, dont_filter=True)

    def __del__(self):
        self.driver.close()

    def parse(self, response):
        self.loop_login()

        if not self.is_login:
            logger.info('this website is not login so nothing to do.')
            return

        logger.info(f'we start get {response.url}')

        if not response.url.rstrip('/').endswith(self.home_url):
            self.total_urls += 1
            logger.info(f'total_urls:{self.total_urls} and {response.url} not in {self.home_url} and detail_parse to process.')
            yield scrapy.Request(url=response.url, callback=self.detail_parse, dont_filter=True)
            return

        self.driver.get(response.url)
        time.sleep(5)

        self.driver.execute_script(self.js)

        page_text = self.driver.page_source
        logger.debug(f'page_text:{page_text}')

        # pickle.dump(page_text, open("home.html", "wb"))

        body = Selector(text=page_text)

        sections = body.xpath('//*[@id="content"]/section[2]')

        for a in sections.xpath('//a/@href').extract():
            url = urljoin(self.domain, a)
            if afrparse.contains_date(url):
                logger.info(f'a:{url}')
                self.total_urls += 1
                logger.info(f'total_urls:{self.total_urls} and process:{url}')
                yield scrapy.Request(url=url, callback=self.detail_parse, dont_filter=True)



    def detail_parse(self, response):

        current_count = self.mysqlObj.count_urls_today(self.name)

        if current_count >= NEWS_ACCOUNTS[self.name]["count_everyday"]:
            self.log(f"afr we had {current_count} >= {NEWS_ACCOUNTS[self.name]["count_everyday"]} and exceed the count limit and do nothing.")
            return


        self.loop_login()

        if not self.is_login:
            logger.info('this website is not login so nothing to do.')
            return

        logger.info(f'we start get {response.url}')

        self.driver.get(response.url)

        time.sleep(5)

        try:
            end = WebDriverWait(self.driver, timeout=10).until(
                EC.presence_of_element_located((By.ID, "endOfArticle"))
            )

            end.click()
        except Exception as e:
            logger.error(f"wait endOfArticle error:{e}")

        self.driver.save_screenshot('t3.png')

        # js = "window.scrollTo(0, document.body.scrollHeight)"
        self.driver.execute_script(self.js)

        page_text = self.driver.page_source
        logger.debug(f'page_text:{page_text}')

        body = Selector(text=page_text)
        # content = Selector(text=page_text).xpath('//div[@id="endOfArticle"]').extract_first('').strip()
        # print(content)

        # pickle.dump(page_text, open("p1.html", "wb"))

        # //*[@id="content"]/header/h1
        # //*[@id="content"]/header/div[1]/h1
        post_content = ""

        post_title = body.xpath('//*[@id="content"]/header//h1/text()').extract_first('').strip()
        if post_title == '' or post_title is None:
            self.log(f"afr no title found in {response.url}")
            return
        logger.info(f'post_title:{post_title}')
        # //*[@id="content"]/header/div[1]/p
        post_sub_title = body.xpath('//*[@id="content"]/header/p[2]/text()').extract_first('').strip()
        logger.info(f'post_sub_title:{post_sub_title}')
        if post_sub_title == '' or post_sub_title is None:
            post_sub_title = body.xpath('//*[@id="content"]/header/div[1]/p').extract_first('').strip()
        if post_sub_title == '' or post_sub_title is None:
            # //*[@id="content"]/header/p
            post_sub_title = body.xpath('//*[@id="content"]/header/p').extract_first('').strip()

        if post_sub_title == '' or post_sub_title is None:
            logger.info(f'post_sub_title is empty.')
        else:
            post_content = post_sub_title

        post_time = body.xpath('//*[@id="content"]/div[2]/section/div[1]/time/text()').extract_first('').strip()
        logger.info(f'post_time:{post_time}')
        if post_time == '' or post_time is None:
            # //*[@id="content"]/div[1]/section/section/section/div[1]/time
            post_time = body.xpath('//*[@id="content"]//time[@data-testid="ArticleTimestamp-time"]/text()').extract_first('').strip()

        post_author = body.xpath('//*[@id="content"]/header/span/span[1]/strong/a/text()').extract_first('').strip()
        logger.info(f'post_author:{post_author}')
        if post_author == '' or post_author is None:
            # //*[@id="content"]/div[1]/section/section/div/span/span
            post_author = body.xpath('//*[@id="content"]/div[1]/section/section/div/span[@data-testid="AuthorNames"]/span')

        post_content_before = body.xpath('//div[@id="beyondwords-player"]//parent::div/following-sibling::*[name()="p"]').extract()
        if not post_content_before:
            logger.info(f'post_content_before is empty by beyondwords-player.')
            # //*[@id="content"]/div[2]
            post_content_before = body.xpath('//*[@id="content"]/div[2]').extract_first('').strip()
            if post_content_before == "" or post_content_before is None:
                # //*[@id="content"]/div[1]/section
                post_content_before = body.xpath('//*[@id="content"]/div[1]/section').extract_first('').strip()
                logger.info(f'post_content_before is empty.')
            else:
                post_content += post_content_before


        else:
            post_content_before = ''.join(post_content_before)
            post_content += post_content_before

        logger.info(f'post_content_before:{post_content_before}')


        post_content_end = body.xpath('//*[@id="endOfArticle"]').extract_first('').strip()
        if post_content_end == "" or post_content_end is None:
            # //*[@id="endOfArticle"]
            logger.info(f'post_content_end is empty.')
        else:
            post_content = post_content + post_content_end

        logger.info(f'post_content_end:{post_content_end}')

        if body.xpath('//*[@id="content"]/div[2]/div[1]').xpath('@id').extract_first('') == 'endOfArticle':
            logger.warning(f'post_content only one part.')
            post_content = body.xpath('//*[@id="endOfArticle"]').extract_first('').strip()

        afr_item = AfrDataItem()
        afr_item["name"] = self.name

        afr_item["origin_title"] = post_title
        afr_item["topic"] = 'financial'
        afr_item["url"] = response.url
        afr_item["url_object_id"] = common.get_md5(afr_item["url"])
        afr_item["post_date"] = common.afr_convert_to_datetime(afr_item["post_time"])

        # TODO: check this url_object_id if exist in db
        if self.mysqlObj.query_url_object_id(self.name, afr_item["url_object_id"]) is not None:
            logger.warning(f"url: {afr_item['url']} already exist in db nothing to do.")
            return


        # 'Feb 12, 2025 – 10.41am'
        # afr_item["post_date"] = common.convert_to_datetime(post_time)
        afr_item["post_date"] = common.convert_to_datetime(None)

        # self.mysqlObj.get_news_category(self.name, afr_item["topic"])
        afr_item["category"] = "投资、理财"

        afr_item["front_image_url"] = []

        logger.info(f'post_content:{post_content}')

        if post_content == '':
            logger.warning(f'post_content is empty and return nothing to do {response.url}.')
            return

        # process the content
        # find all the images src in the post_content
        # and store these images src
        # and replace the domain of the src in post_content
        soup = BeautifulSoup(post_content,"html.parser")

        # delete source element TODO: need optimization
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                source.decompose()

        for img in soup.find_all('img'):
            if img['src'].startswith("https") or img['src'].startswith("http"):
                afr_item["front_image_url"].append(img['src'])  # append origin url to download
                img['src'] = common.get_finished_image_url('afr', afr_item["url_object_id"],
                                                           img['src'])  # replace our website image url from cdn
                if "srcset" in img.attrs:
                    del img.attrs["srcset"]
                if "data-pb-im-config" in img.attrs:
                    del img.attrs["data-pb-im-config"]
            else:
                img.decompose()
        # for img in soup.find_all('img'):
        #     afr_item["front_image_url"].append(img['src']) # append origin url to download
        #     img['src'] = common.get_finished_image_url(self.name, afr_item["url_object_id"], img['src']) # replace our website image url from cdn
        #     if "srcset" in img.attrs:
        #         del img.attrs["srcset"]
        #     if "data-pb-im-config" in img.attrs:
        #         del img.attrs["data-pb-im-config"]


        # find all a label
        for a in soup.find_all('a'):
            # replace all a label with its text
            a.replace_with(a.text)

        # trim data-testid="beyondwords-player-wrapper"
        for div in soup.find_all('div', {"data-testid":"beyondwords-player-wrapper"}):
            div.decompose()

        # trim div id="beyondwords-player"
        for div in soup.find_all('div', {"id":"beyondwords-player"}):
            div.decompose()

        # trim div data-experiment-target="relatedStory"
        for div in soup.find_all('div', {"data-experiment-target":"relatedStory"}):
            div.decompose()

        # trim span data-component="Loading" data-print="inline-media"
        for span in soup.find_all('span', {"data-component":"Loading"}):
            span.decompose()
            
        # trim <small class="acd99af3e011c9b90ee4" style="display: block;">Advertisement</small>
        for small in soup.find_all('small', string="Advertisement"):
            small.decompose()

        # aria-label="Advertisement"
        for label in soup.find_all('iframe', {"aria-label":"Advertisement"}):
            label.decompose()

        # num_text_element = bsobj.find('span', {'class': 'nums_text'})
        # nums = filter(lambda s: s == ',' or s.isdigit(), num_text_element.text)
        # elements = soup.find_all('div', {'class': re.compile('c-container')})
        # for element in elements:
        #     title = element.h3.a.text.strip() if element.h3 and element.h3.a else ""
        #     link = element.h3.a['href'] if element.h3 and element.h3.a else ""

        post_content = str(soup)
        afr_item["origin_content"] = post_content

        logger.info(f'afr_item:{afr_item}')

        if afr_item["url"] != "" and afr_item["origin_title"] != "" and afr_item["origin_content"] != "":
            logger.info(f'afr_item:{afr_item}')
            yield afr_item
        else:
            print("nothing to do due to invalid item: ", afr_item)


    def login(self):
        logger.info("must go to login.")
        self.driver.get('https://afr.com')
        self.driver.maximize_window()  # For maximizing window
        self.driver.implicitly_wait(5)  # gives an implicit wait for 20 seconds
        time.sleep(2)

        retry = 0

        while retry <= self.retry:
            retry += 1
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//li/button/span[contains(text(), "Log in")]'))
                )

                login_button.click()

                # self.driver.find_element(By.XPATH, '//li/button/span[contains(text(), "Log in")]').click()

                login_email = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@id="loginEmail"]'))
                )

                # login_email = self.driver.find_element(By.XPATH, '//input[@id="loginEmail"]')
                login_email.send_keys(self.user)

                login_password = self.driver.find_element(By.XPATH, '//input[@id="loginPassword"]')
                login_password.send_keys(self.password)
                login_submit = self.driver.find_element(By.XPATH, '//button[@data-testid="LoginPassword-submit"]')

                login_submit.click()

                time.sleep(5)
                self.driver.save_screenshot('t1.png')


                # # //*[@id="nav"]/header/div[1]/div/div[2]/ul/li/button/span
                # # //*[@id="nav"]/header/div[1]/div/div[2]/ul/li/button
                # # check login successful
                # check_name = WebDriverWait(self.driver, 10).until(
                #    EC.presence_of_element_located(By.XPATH, '//*[@id="nav"]/header//button["aria-label":"User menu"]/span')
                # )
                #
                # logger.info(f'check_name:{check_name}')
                # logger.info(f'check_name text:{check_name.text}')

            except Exception as e:
                logger.error(f'retry:{retry} and login error:{e}')
            finally:
                body = Selector(text=self.driver.page_source)
                check_name = body.xpath('//*[@id="nav"]/header//button[@aria-label="User menu"]/span/text()').extract_first('').strip()
                logger.info(f'retry:{retry} check_name:{check_name}')
                if check_name != "" and check_name is not None and check_name == 'hugh':
                    self.is_login = True
                    logger.info(f"retry:{retry} and successful so break.")
                    break

        # WebDriverWait(driver, timeout=3).until(
        #     EC.presence_of_element_located((By.ID, "rso"))
        # )


        # self.driver.get("https://www.afr.com/world/middle-east/trump-may-be-wrong-about-many-things-but-he-s-right-about-hamas-20250212-p5lbgn")
        # time.sleep(3)
        # self.driver.save_screenshot('t3.png')
        # page_text = self.driver.page_source
        # logger.info(f'page_text:{page_text}')

        if not self.is_login:
            logger.error(f'login failed')
            return

        # get cookies
        # cookies = self.driver.get_cookies()
        # if cookies is not None and len(cookies) > 0:
        #     logger.info("set first_request is False.")
        # self.cookies_dict = {}
        # for cookie in cookies:
        #     self.cookies_dict[cookie['name']] = cookie['value']
        # self.cookies_dict+= '{}={};'.format(cookie.get('name'), cookie.get('value'))


        # pickle.dump(cookies, open("cookies.pkl", "wb"))
        # logger.info(f'origin cookies:{cookies}')
        # logger.info(f'save dict successful cookies:{self.cookies_dict}')

        # username = None
        # while (username == None):
        #     username = WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located((By.ID, "username"))
        #     )
        # username.send_keys('myusername@email.com')
        return

    def loop_login(self):
        retry = 0
        while retry <= self.retry:
            retry += 1

            if not self.is_login:
                self.login()

            if self.check_is_login():
                return
            else:
                self.is_login = False

        logger.error(f'login retry:{retry} failed and close driver and next time to login again.')
        self.driver.close()
        time.sleep(5)
        self.driver = uc.Chrome(headless=False, use_subprocess=False)
        self.wait = WebDriverWait(self.driver, 20)



    def check_is_login(self):

        if not self.is_login:
            return self.is_login

        self.is_login = False
        body = Selector(text=self.driver.page_source)
        check_name = body.xpath('//*[@id="nav"]/header//button[@aria-label="User menu"]/span/text()').extract_first('').strip()
        if check_name != "" and check_name is not None and check_name == 'hugh':
            logger.info(f'check_is_login:check_name:{check_name} is login')
            self.is_login = True
        else:
            logger.info(f'check_is_login:check_name:{check_name} is not login')

        return self.is_login

