import MySQLdb
from scrapy.utils.project import get_project_settings

SETTING = get_project_settings()

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

    def query_url_object_id(self, url_object_id):
        sql = f"SELECT url_object_id FROM wp_scrapy_news WHERE url_object_id = '{url_object_id}' limit 1"
        self.cursor.execute(sql)
        # return self.cursor.fetchall()
        return self.cursor.fetchone()


    # find the total count of post at today
    def count_urls_today(self):
        # SELECT COUNT(*) AS total_posts_today FROM your_table WHERE DATE(scrapy_date) = CURDATE();
        sql = f"SELECT count(*) FROM wp_scrapy_news WHERE DATE(scrapy_date) = CURDATE()"
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

if __name__ == "__main__":
    mysqlObj = MySqlObj()
    count = mysqlObj.count_urls_today()
    print(count)