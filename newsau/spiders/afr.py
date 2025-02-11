import scrapy
from scrapy.http import FormRequest
import requests


class AfrSpider(scrapy.Spider):
    name = "afr"
    allowed_domains = ["afr.com"]
    start_urls = ["https://afr.com"]
    custom_settings = {
        'COOKIES_ENABLED': True
    }

    def start_requests(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'
        }

        login_url = 'https://api.afr.com/api/member-auth/v0/member/auth'

        params = {
            'response_type': 'code',
            'redirect_uri': 'https://www.afr.com/companies/games-and-wagering/star-entertainment-mulls-walking-away-from-brisbane-casino-ownership-20250209-p5lao0'
        }


        response = requests.post(login_url, params=params, data=data, headers=headers)

        print(response)
        # cookies = browser.get_cookies()
        # cookie_dict = {}
        # for cookie in cookies:
        #     cookie_dict[cookie['name']] = cookie['value']

        # for url in self.start_urls:
        #     yield scrapy.Request(url, cookies=cookie_dict, headers=headers, callback=self.parse, dont_filter=True)
        #
        # login_url = ''
        # return scrapy.Request(login_url, callback=self.login)

    def login(self, response):
        return FormRequest.from_response(response, formdata={'loginID':'yingyw0920@gmail.com', 'password':'0401042861'}, callback=self.start_scraping)

    def parse(self, response):
        pass
