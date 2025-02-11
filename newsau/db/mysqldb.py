import MySQLdb
from scrapy.utils.project import get_project_settings
import logging

SETTING = get_project_settings()

logger = logging.getLogger("mysqldb")


class MySqlObj(object):

    def __init__(self):
        # Instantiate DB
        self.conn = MySQLdb.connect(
      SETTING['DB_HOST'],
            SETTING['DB_USER'],
            SETTING['DB_PASSWD'],
            SETTING['DB_DB'],
            charset='utf8',
            use_unicode=True,
        )
        self.cursor = self.conn.cursor()
        self.default_category_name = 'default'

    def query_url_object_id(self, url_object_id):
        sql = f"SELECT url_object_id FROM wp_scrapy_news WHERE url_object_id = '{url_object_id}' limit 1"
        self.cursor.execute(sql)
        # return self.cursor.fetchall()
        return self.cursor.fetchone()


    # find the total count of post at today
    def count_urls_today(self, name):
        # SELECT COUNT(*) AS total_posts_today FROM your_table WHERE DATE(scrapy_date) = CURDATE();
        sql = f"SELECT count(*) FROM wp_scrapy_news WHERE name = '{name}' and DATE(scrapy_date) = CURDATE()"
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    # find the category of news
    def get_news_category(self, name, topic=None):
        if topic == '' or topic is None:
            logger.debug(f"name:{name} and empty topic get category:{self.default_category_name}")
            sql = f"select news_category from wp_scrapy_category where source_website = '{name}' and scrapy_category = '{self.default_category_name}'"
        else:
            sql = f"SELECT COALESCE( (SELECT news_category FROM wp_scrapy_category WHERE source_website = '{name}' AND scrapy_category LIKE '%{topic}%' LIMIT 1), (select news_category from wp_scrapy_category where source_website = '{name}' and scrapy_category = '{self.default_category_name}') ) AS news_category"

        self.cursor.execute(sql)
        category = self.cursor.fetchone()[0]
        logger.info(f"on the name:{name} topic:{topic} get category:{category} and sql:{sql}")
        return category


if __name__ == "__main__":
    mysqlObj = MySqlObj()
    # count = mysqlObj.count_urls_today('abc')
    # print(count)
    news_category = mysqlObj.get_news_category('abc', 'Unrest, Conflict and War')
    print(news_category)