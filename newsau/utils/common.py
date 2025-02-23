import pickle
import pytz
import hashlib

from bs4 import BeautifulSoup
from newsau.settings import NEWS_ACCOUNTS

import logging

logger = logging.getLogger("common")

import re
from datetime import datetime, timedelta

from urllib.parse import urlparse, parse_qs

def contains_app_news(url):
    """
    Check if the URL contains the parameter app=news.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)  # Parse query parameters as a dictionary
    return query_params.get("app") == ["news"]  # Check if 'app' exists and its value is 'news'

# # 🔹 Example Usage
# url = "https://local.6parknews.com/index.php?app=news&act=view&nid=1291491"
# print(contains_app_news(url))  # Output: True


def is_today_or_yesterday(dt: datetime) -> bool:
    """
    Check if the given datetime object is either today or yesterday.

    Parameters:
        dt (datetime): The datetime object to be checked.

    Returns:
        bool: True if dt is today or yesterday, otherwise False.
    """
    # Get the current date
    today = datetime.today().date()
    # Calculate yesterday's date by subtracting one day from today
    yesterday = today - timedelta(days=1)
    # Check if the date part of dt is either today or yesterday
    return dt.date() in (today, yesterday)

# # Example usage
# if __name__ == '__main__':
#     now = datetime.now()
#     print(f"Current: {now} -> {is_today_or_yesterday(now)}")  # Expected output: True
#
#     some_date = datetime(2020, 1, 1)
#     print(f"2020-01-01 -> {is_today_or_yesterday(some_date)}")  # Expected output: False



def extract_datetime(text):
    """
    Extracts date and time from a string and converts it to a Python datetime object.

    :param text: The input text containing a date and time.
    :return: A datetime object if found, otherwise None.
    """
    sydney_tz = pytz.timezone("Australia/Sydney")
    match = re.search(r'(\d{4}-\d{2}-\d{2}) (\d{1,2}:\d{2}:\d{2})', text)
    if match:
        date_str = match.group(1)  # Extracted Date: YYYY-MM-DD
        time_str = match.group(2)  # Extracted Time: H:mm:ss or HH:mm:ss
        datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        return datetime_obj  # Return Python datetime object
    return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S") # Return None if no match is found

# # 🔹 Example Usage
# text = "新闻来源: 微生活 于 2025-02-19 2:05:15"
# dt = extract_datetime(text)
#
# print(dt)  # Output: 2025-02-19 02:05:15
# print(type(dt))  # Output: <class 'datetime.datetime'>


def is_valid_date(date_str, date_format):
    """
    Check if a given date string matches a valid date format.

    :param date_str: The date string to validate.
    :param date_format: The expected date format (e.g., '%Y-%m-%d' or '%Y%m%d').
    :return: True if it's a valid date, False otherwise.
    """
    try:
        datetime.strptime(date_str, date_format)  # Attempt to parse date
        return True
    except ValueError:
        return False  # Invalid date

def contains_valid_date(url):
    """
    Check if a URL contains a valid date in YYYY-MM-DD or YYYYMMDD format.

    :param url: The URL string to check.
    :return: True if a valid date is found, otherwise False.
    """
    # Match YYYY-MM-DD format
    match1 = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", url)
    if match1 and is_valid_date(match1.group(1), "%Y-%m-%d"):
        return True  # Valid YYYY-MM-DD date found

    # Match YYYYMMDD format
    match2 = re.search(r"\b(\d{8})\b", url)
    if match2 and is_valid_date(match2.group(1), "%Y%m%d"):
        return True  # Valid YYYYMMDD date found

    return False  # No valid date found

def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)

    return m.hexdigest()


# to replace the image path of download from origin website
# and use one prefix path like this: /news/abc/yy-mm-dd/url_object_id[:5]/image_url_hash.jpg
# result like this: '/news/abc/2025-02/1a0cd/ee024ebf69.jpg' for Google Cloud Storage
def get_image_url_full_path(name, url_object_id, url):
    # get the yy-mm-dd at now
    year_month = datetime.today().strftime('%Y-%m')
    image_url_hash = hashlib.shake_256(url.encode()).hexdigest(5)
    return f"news/{name}/{year_month}/{url_object_id[:5]}/{image_url_hash}.jpg"

# to replace the url in content
def get_finished_image_url(name, url_object_id, url):
    print(f'get_finished_image_url:{url}')
    return f"{NEWS_ACCOUNTS[name]['image_cdn_domain']}{get_image_url_full_path(name, url_object_id, url)}"

def afr_convert_to_datetime(date_str):
    """
    将 "Feb 13, 2025 – 6.25pm" 格式的日期转换为 datetime 对象
    :param date_str: 需要转换的日期字符串
    :return: 转换后的 datetime 对象
    """
    sydney_tz = pytz.timezone("Australia/Sydney")

    if date_str is None or date_str == "":
        return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")

    utc_time = datetime.strptime(date_str, "%b %d, %Y – %I.%M%p")
    # utc_time = utc_time.replace(tzinfo=pytz.utc)
    #
    # sydney_time = utc_time.astimezone(sydney_tz)

    # mysql_datetime = sydney_time.strftime("%Y-%m-%d %H:%M:%S")
    mysql_datetime = utc_time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"convert {date_str} to datetime: {mysql_datetime}")

    return mysql_datetime
    # return datetime.strptime(date_str, "%b %d, %Y – %I.%M%p")

def convert_to_datetime(date_str):

    sydney_tz = pytz.timezone("Australia/Sydney")

    if date_str is None or date_str == "":
        return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
    else:
        iso_time = date_str

    try:
        utc_time = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_time = utc_time.replace(tzinfo=pytz.utc)

        sydney_time = utc_time.astimezone(sydney_tz)

        mysql_datetime = sydney_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"convert {date_str} to datetime: {mysql_datetime}")
        return mysql_datetime
    except Exception as e:
        logger.error(f'convert {date_str} to datetime error: {e}')
        return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")


# trip content the beginning ```html and trip the end ```
def trip_ai_mistake(content):
    return content.lstrip('```html').rstrip('```')

def parse_content():
    from scrapy.selector import Selector
    from scrapy.http import HtmlResponse


    page_source = pickle.load(open("../../page.html", "rb"))

    body = Selector(text=page_source)

    post_title = body.xpath('//*[@id="content"]/header/h1/text()').extract_first('').strip()
    logger.info(f'post_title:{post_title}')

    post_sub_title = body.xpath('//*[@id="content"]/header/p[2]/text()').extract_first('').strip()
    logger.info(f'post_sub_title:{post_sub_title}')

    post_time = body.xpath('//*[@id="content"]/div[2]/section/div[1]/time/text()').extract_first('').strip()
    logger.info(f'post_time:{post_time}')

    post_author = body.xpath('//*[@id="content"]/header/span/span[1]/strong/a/text()').extract_first('').strip()
    logger.info(f'post_author:{post_author}')

    post_content_before = body.xpath('//*[@id="content"]/div[3]/div').extract_first('').strip()
    post_content_end = body.xpath('//div[@id="endOfArticle"]').extract_first('').strip()
    logger.info(f'post_content_before:{post_content_before}')
    logger.info(f'post_content_end:{post_content_end}')


    post_content = post_content_before + post_content_end

    soup = BeautifulSoup(post_content, "html.parser")

    # delete source element TODO: need optimization
    for picture in soup.find_all('picture'):
        for source in picture.find_all('source'):
            logger.info(f'delete source:{source}')
            source.decompose()

    for img in soup.find_all('img'):
        img['src'] = get_finished_image_url("afr", "test", img['src'])
        if "srcset" in img.attrs:
            logger.info(f'delete srcset:{img.attrs["srcset"]}')
            del img.attrs["srcset"]
        if "data-pb-im-config" in img.attrs:
            logger.info(f'delete data-pb-im-config:{img.attrs["data-pb-im-config"]}')
            del img.attrs["data-pb-im-config"]



    post_content = str(soup)
    logger.info(post_content)

if __name__ == "__main__":
    # print(get_md5("https://news.china.com.au"))
    # print(convert_to_datetime("2025-02-10T04:55:05.000Z"))
    # print(convert_to_datetime(None))
    #
    # content = '```html\n <div>\n<figure class="ContentAlignment_marginBottom__4H_6E ContentAlignment_overflowAuto__c1_IL Figure_figure__xLyBy```'
    # content = (trip_ai_mistake(content))
    # print(content)
    # content = (trip_ai_mistake(content))
    # print(content)

    # date_str = "Feb 13, 2025 – 6.25pm"
    # print(afr_convert_to_datetime(date_str))

    # 🔹 Test Cases
    test_urls = [
        "https://example.com/news/2025-02-19/article",  # ✅ YYYY-MM-DD
        "https://example.com/archive/20250219/report",  # ✅ YYYYMMDD
        "https://example.com/blog/post-123",  # ❌ No date
        "https://example.com/2025-02-30",  # ❌ Invalid date (Feb 30 does not exist)
        "https://example.com/20251319",  # ❌ Invalid date (Month 13 is invalid)
        "https://example.com/data?date=2024-04-31",  # ❌ Invalid date (April 31 does not exist)
        "https://example.com/data?date=20240430"  # ✅ YYYYMMDD (Valid April 30)
    ]

    for url in test_urls:
        print(f"{url} → {contains_valid_date(url)}")

    url = "https://www.afr.com/companies/financial-services/nab-first-quarter-profit-drops-on-small-margin-decline-20250218-p5ld4y"
    print(contains_valid_date(url))

    # parse_content()
