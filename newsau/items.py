# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


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
    front_image_url = scrapy.Field()
    front_image_path = scrapy.Field()
    origin_content = scrapy.Field()
    content = scrapy.Field()

    def get_insert_sql(self):

        # if title and content had not values and do nothing
        if self.get("title", "") == "" or self.get("content", "") == "":
            print(f"nothing to do insert {self}")
            return "", ()

        # insert_sql = """
        # insert into wp_scrapy_news(title, topic, url, url_object_id, front_image_url, front_image_path, content, create_date)
        #  values (%s, %s, %s, %s, %s, %s, %s, %s)
        #  ON DUPLICATE KEY UPDATE content=values(content)"""
        insert_sql = """insert into wp_scrapy_news(name, origin_title, title, topic, url, url_object_id, front_image_url, front_image_path, origin_content, content, create_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        params = list()
        params.append(self.get("name", ""))
        params.append(self.get("origin_title", ""))
        params.append(self.get("title", ""))
        params.append(self.get("topic", ""))
        params.append(self.get("url", ""))
        params.append(self.get("url_object_id", ""))
        params.append(",".join(self.get("front_image_url", ["empty"])))
        params.append(",".join(self.get("front_image_path", ["empty"])))
        params.append(self.get("origin_content", ""))
        params.append(self.get("content", ""))
        params.append(self.get("create_date", "1970-07-10"))

        return insert_sql, tuple(params)

    def get_title(self):
        return self.get("title", "")

    def get_content(self):
        return self.get("content", "")

