# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import hashlib
import json
import logging

from datetime import datetime, timedelta
import scrapy
from twisted.enterprise import adbapi
import MySQLdb
from scrapy.exporters import JsonItemExporter
# useful for handling different item types with a single interface
from scrapy.pipelines.images import ImagesPipeline
import codecs

from scrapy.utils.project import get_project_settings

from newsau.ai.translator import UnifiedTranslator
from newsau.db import orm

from newsau.utils.common import get_image_url_full_path, trip_ai_mistake,get_md5,clean_html,contains_keywords
import os
from newsau.ai import openaiplat
from newsau.ai import deepseek
from newsau.wp.xmlwpapi import WpApi
from newsau.cache import url_queue, rcount
from newsau.settings import REDIS_URL

logger = logging.getLogger(__name__)

# for sequential request every url
# from twisted.internet import defer

SETTING = get_project_settings()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=SETTING["GOOGLE_APPLICATION_CREDENTIALS"]

class NewsauPipeline:

    def process_item(self, item, spider):
        return item


class ContentTranslatePipeline:
    def __init__(self):
        self.translator = UnifiedTranslator()

    def process_item(self, item, spider):
        # 检查数据库缓存
        record = orm.get_scrapy_record_if_exist(item["url_object_id"])
        if record:
            logger.warning(f'Using cached translation from MySQL: {record}')
            item.update({
                "title": record.title,
                "content": record.content,
                "category": record.category[0] if record.category else None
            })
            return item

        if spider.name == "parknews":
            item["title"] = self.translator.retry_translate_c2c_title(item.get("origin_title", ""))
            item["content"] = self.translator.retry_translate_c2c_content(item.get("origin_content", ""))
            item["category"] = self.translator.retry_generate_c2c_tag(item.get("origin_content", ""))
        else:
            item["title"] = self.translator.retry_translate_title(item.get("origin_title", ""))
            item["content"] = self.translator.retry_translate_content(item.get("origin_content", ""))
            item["category"] = self.translator.retry_generate_category(item.get("origin_content", ""))
            if not item["category"]:
                item["category"] = self.translator.retry_generate_category(item.get("origin_content", ""))

        llm_source = self.translator.last_successful
        category_list = (item["category"] if isinstance(item["category"], list) else ([item["category"]] if item["category"] else []))
        orm.add_scrapy_record(
            llm=llm_source,
            name=item["name"],
            url=item["url"],
            url_object_id=item["url_object_id"],
            category=category_list,
            tag=None,
            title=item["title"],
            content=item["content"]
        )
        return item


class AbcContentTranslatePipeline3(object):
    def __init__(self):
        self.dp = deepseek.DeepSeekApi()
        self.op = openaiplat.OpenAiPlat()
        self.last_successful_method = "deepseek"
        self.last_deepseek_failure = None
        self.retry_interval = timedelta(hours=1)

    def translate(self, text, method, func_name):
        """通用翻译方法，支持 Deepseek 和 OpenAI"""
        try:
            if method == "deepseek":
                return getattr(self.dp, func_name)(text)
            else:
                return getattr(self.op, func_name)(text)
        except Exception:
            return None

    def should_retry_deepseek(self):
        """判断是否应该重试 Deepseek"""
        if self.last_successful_method == "openai" and self.last_deepseek_failure:
            return datetime.now() - self.last_deepseek_failure >= self.retry_interval
        return False

    def process_item(self, item, spider):
        record = orm.get_scrapy_record_if_exist(item["url_object_id"])
        if record:
            logger.warning(f'Using cached translation from MySQL: {record}')
            item.update({
                "title": record.title,
                "content": record.content,
                "category": record.category[0] if record.category else None
            })
            return item

        if self.should_retry_deepseek():
            self.last_successful_method = "deepseek"

        def translate_field(field, func_name):
            """通用字段翻译逻辑"""
            if not field:
                return None
            result = self.translate(field, self.last_successful_method, func_name)
            if result is None and self.last_successful_method == "deepseek":
                self.last_successful_method = "openai"
                self.last_deepseek_failure = datetime.now()
                result = self.translate(field, "openai", func_name)
            return result

        if spider.name == "parknews":
            item["title"] = translate_field(item["origin_title"], "retry_translate_c2c_title")
            item["content"] = translate_field(item["origin_content"], "retry_translate_c2c_content")
            item["category"] = translate_field(item["origin_content"], "retry_generate_c2c_tag")
        else:
            item["title"] = translate_field(item["origin_title"], "retry_translate_title")
            item["content"] = translate_field(item["origin_content"], "retry_translate_content")
            item["category"] = translate_field(item["origin_content"], "retry_generate_category")
            if item["category"] is None:
                item["category"] = translate_field(item["origin_content"], "retry_generate_category")

        # save record to mysql
        llm_source = self.last_successful_method
        orm.add_scrapy_record(
            llm=llm_source,
            name=item["name"],
            url=item["url"],
            url_object_id=item["url_object_id"],
            category=item["category"] if isinstance(item["category"], list) else [item["category"]] if item["category"] else [],
            tag=None,
            title=item["title"],
            content=item["content"]
        )

        return item


class AbcContentTranslatePipeline2(object):

    def __init__(self):
        # fist use deepseek to translate
        self.dp = deepseek.DeepSeekApi()
        self.op = openaiplat.OpenAiPlat()
        self.last_successful_method = "deepseek"  # 记录上次成功的翻译方式
        self.last_deepseek_failure = None  # 记录Deepseek失败时间
        self.retry_interval = timedelta(hours=1)  # 1小时后再试Deepseek

    # @defer.inlineCallbacks
    def process_item(self, item, spider):

        # if not item["priority"]:
        #     if orm.check_if_exceed_num(item["name"]):
        #         return item

        # # for test emacsvi.com
        # item["title"] = item["origin_title"]
        # item["content"] = item["origin_content"]
        # return item

        record = orm.get_scrapy_record_if_exist(item["url_object_id"])
        if not record:
            logger.warning(f'get already ai result and fetch it in mysql:{record}')
            item["title"] = record.title
            item["content"] = record.content
            item["category"] = record.category[0] if record.category else None
            # item["tag"] = record.tag[0] if record.tag else None
            return item

        if spider.name == "parknews":
            if item["origin_title"] != "":
                tr_title = self.op.retry_translate_c2c_title(item["origin_title"])
                if tr_title:
                    logger.info(f"{item['origin_title']}=>{tr_title}")
                    item["title"] = tr_title

            if item["origin_content"] != "":
                tr_content = self.op.retry_translate_c2c_content(item["origin_content"])
                if tr_content:
                    item["content"] = trip_ai_mistake(tr_content) # for fix openai mistake

                category = self.op.retry_generate_c2c_tag(item["origin_content"])
                if category:
                    item["category"] = category

        else:
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

        # save the result of translate to mysql
        orm.add_scrapy_record(item["name"], item["url"], item["url_object_id"], [item["category"]], None, item["title"], item["content"])
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

        # logger.debug(f'abc Image item:{item}')
        if "front_image_url" in item:
            for ok, value in results:
                # logger.debug(f'ok:{ok}, value:{value}')
                if isinstance(value, dict) and 'path' in value:
                    item["front_image_path"].append(f'{SETTING["NEWS_ACCOUNTS"][item["name"]]["image_cdn_domain"]}{value["path"]}')

        return item


class SaveToMySqlPipeline(object):

    def __init__(self):
        self.queue = None
        self.count = None
        self.wp = WpApi(SETTING['WP_XMLURL'], SETTING['WP_USER'], SETTING['WP_PASSWORD'])

    def open_spider(self, spider):
        """Initialize the queue when the spider starts."""
        if self.queue is None:
            self.queue = url_queue.RedisUrlQueue(spider.name, REDIS_URL)
        if self.count is None:
            self.count = rcount.RedisCounter(spider.name, REDIS_URL)

    # @defer.inlineCallbacks
    def process_item(self, item, spider):
        if not item["priority"]:
            if spider.name == "parknews":
                if orm.check_if_exceed_num_today_and_yesterday(spider.name, self.count.get_value()):
                    return item
            else:
                if orm.check_if_exceed_num(spider.name, self.count.get_value()):
                    return item

        obj = item.convert_to_wp_news()
        if obj is not None:

            if orm.create_post(obj):
                if spider.name == "parknews":
                    if contains_keywords(item.get_title()):
                        logger.error(f"{item.get_title()} deepseek happened any error so use origin title:{item.get_origin_title()}")
                        self.wp.post(item.get_origin_title(), item.get_content(), post_date=item.get_post_date(),
                                     categories=[], tags=[item.get_post_category()], post_type="newsflashes")
                    else:
                        self.wp.post(item.get_title(), item.get_content(), post_date=item.get_post_date(), categories=[], tags=[item.get_post_category()], post_type="newsflashes")
                else:
                    cleaned_content = clean_html(item.get_content())
                    self.wp.post(item.get_title(), cleaned_content, post_date=item.get_post_date(), categories=[item.get_post_category()], tags=[item["name"]])

                if item["priority"]:
                    self.count.increment(1)

        if spider.name == "ft":
            return item

        task = self.queue.pop()
        if task:
            next_url = task.get("url")
            if next_url:
                logger.info(f'finished save mysql and process next_url:{next_url}')
                spider.crawler.engine.crawl(scrapy.Request(next_url, callback=spider.detail_parse))
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