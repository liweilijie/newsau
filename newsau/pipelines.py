# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import hashlib
import json
import logging

from twisted.enterprise import adbapi
import MySQLdb
from scrapy.exporters import JsonItemExporter
# useful for handling different item types with a single interface
from scrapy.pipelines.images import ImagesPipeline
import codecs

from scrapy.utils.project import get_project_settings

from newsau.db import orm

from newsau.utils.common import get_image_url_full_path, trip_ai_mistake
import os
from newsau.ai import openaiplat
from newsau.ai import deepseek
from newsau.wp.xmlwpapi import WpApi

logger = logging.getLogger(__name__)
# logger.setLevel('DEBUG')

SETTING = get_project_settings()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=SETTING["GOOGLE_APPLICATION_CREDENTIALS"]

class NewsauPipeline:

    def process_item(self, item, spider):
        return item


class AbcContentTranslatePipeline(object):

    def __init__(self):
        # fist use deepseek to translate
        self.dp = deepseek.DeepSeekApi()
        self.op = openaiplat.OpenAiPlat()


    def process_item(self, item, spider):

        if orm.check_if_exceed_num(item["name"]):
            return item

        # # for test emacsvi.com
        # item["title"] = item["origin_title"]
        # item["content"] = item["origin_content"]
        # return item

        if item["origin_title"] != "":
            tr_title = self.op.retry_translate_title(item["origin_title"])
            if tr_title is None:
                tr_title = self.dp.retry_translate_title(item["origin_title"])

            if tr_title is not None:
                # tr_title remove newline
                tr_title = tr_title.replace("\n", "")
                # print origin_title translate to title
                logger.info(f"{item['origin_title']}=>{tr_title}")
                item["title"] = tr_title

        if item["origin_content"] != "":
            tr_content = self.op.retry_translate_content(item["origin_content"])
            if tr_content is None:
                tr_content = self.dp.retry_translate_content(item["origin_content"])

            logger.info(f'tr_content:{tr_content}')
            if tr_content is not None:
                item["content"] = trip_ai_mistake(tr_content) # for fix openai mistake

        # generate category
        category = self.op.retry_generate_category(item["origin_content"])
        if category is None:
            category = self.dp.retry_generate_category(item["origin_content"])

        if category is not None:
            logger.info(f"generate category:{category}")
            item["category"] = category

        return item



class AbcImagePipeline(ImagesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        url_object_id = item.get("url_object_id", "default")

        image_filename = get_image_url_full_path(item["name"], url_object_id, request.url)

        return image_filename

    def item_completed(self, results, item, info):

        # if item["front_image_path"] is none
        if "front_image_path" not in item:
            item["front_image_path"] = []

        logger.debug(f'abc Image item:{item}')
        if "front_image_url" in item:
            for ok, value in results:
                logger.debug(f'ok:{ok}, value:{value}')
                if isinstance(value, dict) and 'path' in value:
                    item["front_image_path"].append(f'{SETTING["NEWS_ACCOUNTS"][item["name"]]['image_cdn_domain']}{value["path"]}')

        return item


class SaveToMySqlPipeline(object):

    def __init__(self):
        self.wp = WpApi(SETTING['WP_XMLURL'], SETTING['WP_USER'], SETTING['WP_PASSWORD'])


    def process_item(self, item, spider):

        if orm.check_if_exceed_num(item["name"]):
            return item

        obj = item.convert_to_wp_news()
        if obj is not None:
            if orm.create_post(obj):
                self.wp.post(item.get_title(), item.get_content(), post_date=item.get_post_date(), categories=[item.get_post_category()], tags=[item["name"]])

        return item


class MySqlPipeline(object):

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
        self.wp = WpApi(SETTING['WP_XMLURL'], SETTING['WP_USER'], SETTING['WP_PASSWORD'])


    def process_item(self, item, spider):
        insert_sql, params = item.get_insert_sql()
        print(insert_sql)
        print(params)
        if insert_sql != "" and len(params) != 0:
            try:
                self.cursor.execute(insert_sql, params)
                self.conn.commit()
                print("insert affected rows = {}".format(self.cursor.rowcount))
                if self.cursor.rowcount > 0:
                    print(f"send to wp:{item.get_title()}")
                    self.wp.post(item.get_title(), item.get_content(), post_date=item.get_post_date(), categories=[item.get_post_category()], tags=[item["name"]])
                    # update_post(item.get_title(), item.get_content())

            except Exception as e:
                print(f"insert happened error:{e}")

        return item


class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open("news.json", "a+", encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False)+"\n"
        self.file.write(lines)
        return item

    def spider_closed(self):
        self.file.close()

class JsonExportPipeline(object):
    def __init__(self):
        self.file = open("news_exporter.json", "a+")
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def spider_closed(self):
        self.exporter.finish_exporting()
        self.file.close()


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.wp = WpApi(SETTING['WP_XMLURL'], SETTING['WP_USER'], SETTING['WP_PASSWORD'])

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        dbparams = dict(
            host=settings["DB_HOST"],
            db=settings["DB_DB"],
            user=settings["DB_USER"],
            passwd=settings["DB_PASSWD"],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True,
        )

        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparams)
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)
        return item

    def handle_error(self, failure, item, spider):
        print(failure)

    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        print(insert_sql)
        print(params)
        if insert_sql != "" and len(params) != 0:
            try:
                cursor.execute(insert_sql, params)
                print("insert affected rows = {}".format(cursor.rowcount))
                if cursor.rowcount > 0:
                    self.wp.post(item.get_title(), item.get_content(), tags=[item["name"]])
                    # update_post(item.get_title_and_content())

            except Exception as e:
                print(f"insert happened error:{e}")


class WpPostPipeline(object):
    def __init__(self):
        self.wp = WpApi(SETTING['WP_XMLURL'], SETTING['WP_USER'], SETTING['WP_PASSWORD'])

    def process_item(self, item, spider):
        title = item.get("title", "")
        content = item.get("content", "")
        if title == "" or content == "":
            print("title or content is empty and nothing to do.")
            return item

        self.wp.post(item.get_title(), item.get_content(), tags=[item["name"]])
        # update_post(title, content)
        return item