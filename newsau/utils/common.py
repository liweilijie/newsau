from datetime import datetime
import pytz
import hashlib
from newsau.settings import NEWS_ACCOUNTS


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
    return f"{NEWS_ACCOUNTS[name]['image_cdn_domain']}{get_image_url_full_path(name, url_object_id, url)}"

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

        print(mysql_datetime)

        return mysql_datetime
    except Exception as e:
        print(f'convert {date_str} to datetime error: {e}')
        return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    print(get_md5("https://news.china.com.au"))
    print(convert_to_datetime("2025-02-10T04:55:05.000Z"))
    print(convert_to_datetime(None))
