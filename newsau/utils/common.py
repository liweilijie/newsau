import pickle
from datetime import datetime
import pytz
import hashlib

from bs4 import BeautifulSoup

from newsau.cache.rsync_status import accounts_store
import logging

logger = logging.getLogger("common")

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
    return f"{accounts_store.get()[name]['image_cdn_domain']}{get_image_url_full_path(name, url_object_id, url)}"

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


# trip content the begin ```html and trip the end ```
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

    date_str = "Feb 13, 2025 – 6.25pm"
    print(afr_convert_to_datetime(date_str))

    # parse_content()
