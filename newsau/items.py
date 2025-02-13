# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from newsau.utils import common


class NewsauItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class AbcDataItem(scrapy.Item):
    name = scrapy.Field()
    origin_title = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    topic = scrapy.Field()
    category = scrapy.Field()
    front_image_url = scrapy.Field()
    front_image_path = scrapy.Field()
    origin_content = scrapy.Field()
    content = scrapy.Field()
    post_date = scrapy.Field()
    scrapy_date = scrapy.Field()

    def get_insert_sql(self):

        # if title and content had not values and do nothing
        if self.get("title", "") == "" or self.get("content", "") == "":
            print(f"nothing to do insert {self}")
            return "", ()

        # insert_sql = """
        # insert into wp_scrapy_news(title, topic, url, url_object_id, front_image_url, front_image_path, content, create_date)
        #  values (%s, %s, %s, %s, %s, %s, %s, %s)
        #  ON DUPLICATE KEY UPDATE content=values(content)"""
        insert_sql = """insert into wp_scrapy_news(name, origin_title, title, topic, category, url, url_object_id, front_image_url, front_image_path, origin_content, content, post_date, scrapy_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        params = list()
        params.append(self.get("name", ""))
        params.append(self.get("origin_title", ""))
        params.append(self.get("title", ""))
        params.append(self.get("topic", ""))
        params.append(self.get("category", ""))
        params.append(self.get("url", ""))
        params.append(self.get("url_object_id", ""))
        params.append(",".join(self.get("front_image_url", ["empty"])))
        params.append(",".join(self.get("front_image_path", ["empty"])))
        params.append(self.get("origin_content", ""))
        params.append(self.get("content", ""))
        params.append(self.get("post_date", common.convert_to_datetime(None)))
        params.append(self.get("scrapy_date", common.convert_to_datetime(None)))

        return insert_sql, tuple(params)

    def get_post_category(self):
        return self.get("category", "澳洲新闻")

    def get_post_date(self):
        return self.get("post_date", common.convert_to_datetime(None))

    def get_title(self):
        return self.get("title", "")

    def get_content(self):
        return self.get("content", "")


class AfrDataItem(scrapy.Item):
    name = scrapy.Field()
    origin_title = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    topic = scrapy.Field()
    author = scrapy.Field()
    category = scrapy.Field()
    front_image_url = scrapy.Field()
    front_image_path = scrapy.Field()
    origin_content = scrapy.Field()
    content = scrapy.Field()
    post_date = scrapy.Field()
    scrapy_date = scrapy.Field()

    def get_insert_sql(self):

        # if title and content had not values and do nothing
        if self.get("title", "") == "" or self.get("content", "") == "":
            print(f"nothing to do insert {self}")
            return "", ()

        # insert_sql = """
        # insert into wp_scrapy_news(title, topic, url, url_object_id, front_image_url, front_image_path, content, create_date)
        #  values (%s, %s, %s, %s, %s, %s, %s, %s)
        #  ON DUPLICATE KEY UPDATE content=values(content)"""
        insert_sql = """insert into wp_scrapy_news(name, origin_title, title, topic, category, url, url_object_id, front_image_url, front_image_path, origin_content, content, post_date, scrapy_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        params = list()
        params.append(self.get("name", ""))
        params.append(self.get("origin_title", ""))
        params.append(self.get("title", ""))
        params.append(self.get("topic", ""))
        params.append(self.get("category", ""))
        params.append(self.get("url", ""))
        params.append(self.get("url_object_id", ""))
        params.append(",".join(self.get("front_image_url", ["empty"])))
        params.append(",".join(self.get("front_image_path", ["empty"])))
        params.append(self.get("origin_content", ""))
        params.append(self.get("content", ""))
        params.append(self.get("post_date", common.convert_to_datetime(None)))
        params.append(self.get("scrapy_date", common.convert_to_datetime(None)))

        return insert_sql, tuple(params)

    def get_post_category(self):
        return self.get("category", "投资、理财")

    def get_post_date(self):
        return self.get("post_date", common.convert_to_datetime(None))

    def get_title(self):
        return self.get("title", "")

    def get_content(self):
        return self.get("content", "")

