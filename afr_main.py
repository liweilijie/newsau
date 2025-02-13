import os.path
import sys
import time
import pickle

from scrapy.cmdline import execute

from selenium.webdriver.remote.webdriver import By
import selenium.webdriver.support.expected_conditions as EC  # noqa
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import By
import selenium.webdriver.support.expected_conditions as EC  # noqa
import undetected_chromedriver as uc
from selenium.webdriver.support.wait import WebDriverWait
import logging
from newsau.settings import AFR_USER, AFR_PASSWORD

def main():
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(['scrapy', 'crawl', 'afr'])

logger = logging.getLogger(__name__)

class AfrCookies(object):
    def __init__(self):
        self.user = AFR_USER
        self.password = AFR_PASSWORD


    def login(self):
        driver = uc.Chrome(headless=False, use_subprocess=True)
        driver.get('https://afr.com')

        # WebDriverWait(driver, timeout=3).until(
        #     EC.presence_of_element_located((By.ID, "rso"))
        # )

        login_element = driver.find_element(By.XPATH, '//li/button/span[contains(text(), "Log in")]')
        login_element.click()
        login_email = driver.find_element(By.XPATH, '//input[@id="loginEmail"]')
        login_email.send_keys(self.user)

        login_password = driver.find_element(By.XPATH, '//input[@id="loginPassword"]')
        login_password.send_keys(self.password)
        login_submit = driver.find_element(By.XPATH, '//button[@data-testid="LoginPassword-submit"]')

        login_submit.click()

        time.sleep(3)

        # get cookies
        cookies = driver.get_cookies()
        # self.cookies_dict = {}
        # for cookie in cookies:
        #     self.cookies_dict[cookie['name']] = cookie['value']
            # self.cookies_dict+= '{}={};'.format(cookie.get('name'), cookie.get('value'))


        pickle.dump(cookies, open("cookies.pkl", "wb"))
        logger.info(f'origin cookies:{cookies}')
        # logger.info(f'save dict successful cookies:{self.cookies_dict}')

        driver.close()

        return


if __name__ == "__main__":
    main()
    # afr_cookies = AfrCookies()
    # afr_cookies.login()