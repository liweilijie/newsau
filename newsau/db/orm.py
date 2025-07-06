import logging

from newsau.db import session
from newsau.db.models import WPScrapyNews, WPScrapyCategory, WPScrapyAiRecord

from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from typing import Optional
from sqlalchemy.future import select



logger = logging.getLogger("mysql")

def query_object_id(name: str, url_object_id: str) -> bool:
    """
    query if contain the object_id use url
    :param name: spider name
    :param url_object_id: md5(url)
    :return: if exist and return true, otherwise false
    """
    try:
        existing_url = session.query(WPScrapyNews).filter(
            and_(
                WPScrapyNews.url_object_id == url_object_id,
                WPScrapyNews.name == name
            )
        ).first()
        session.commit()
        if existing_url is None:
            return False
        else:
            return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}, url_object_id:{url_object_id}: {e}")
        raise RuntimeError("database connection error.")
    except Exception as e:
        logger.error(f"Unexpected error when query_object_id name:{name}, url_object_id:{url_object_id}: {e}")

    return False


def count_urls_today_and_yesterday(name: str):
    try:
        # 统计今天和昨天的数量
        count = session.query(WPScrapyNews).filter(
            and_(
                WPScrapyNews.name == name,
                func.DATE(WPScrapyNews.post_date).in_([func.current_date(), func.current_date() - 1])
            )
        ).count()
        session.commit()

        logger.info(f'Today and Yesterday count: {count}')
        return count if count is not None else 0

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError when querying object_id name:{name}: {e}")
        raise RuntimeError("database connection error.")
    except Exception as e:
        logger.error(f"Unexpected error when querying object_id name:{name}: {e}")

    return 0


def count_urls_today(name: str):
    try:
        today_count = session.query(WPScrapyNews).filter(
            and_(
                WPScrapyNews.name == name,
                func.DATE(WPScrapyNews.post_date) == func.current_date()
            )
        ).count()
        session.commit()

        logger.info(f'today_count:{today_count}')
        if today_count is not None:
            return today_count
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}: {e}")
        raise RuntimeError("database connection error.")
    except Exception as e:
        logger.error(f"Unexpected error when query_object_id name:{name}: {e}")

    return 0


def get_category(name, topic):

    if topic is None:
        return None

    try:
        search = f"%{topic}%"
        category = session.query(WPScrapyCategory.news_category).filter(
            and_(
                WPScrapyCategory.source_website == name,
                WPScrapyCategory.scrapy_category.like(search)
            )
        ).first()
        session.commit()

        logger.info(f'category:{category}')
        if category is not None:
            return category[0]
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}: {e}")
        raise RuntimeError("database connection error.")
    except Exception as e:
        logger.error(f"Unexpected error when query_object_id name:{name}: {e}")

    return None


def check_if_exceed_num_today_and_yesterday(name, max_value):
    current_count = count_urls_today_and_yesterday(name)

    if current_count >= max_value:
        logger.info(
            f"afr we had {current_count} >= {max_value} and exceed the count limit and do nothing.")
        return True
    return False


# check if exceed
def check_if_exceed_num(name, max_value):
    current_count = count_urls_today(name)

    if current_count >= max_value:
        logger.info(
            f"{name} we had {current_count} >= {max_value} and exceed the count limit and do nothing.")
        return True
    return False

def create_post(post: WPScrapyNews) -> bool:
    if not post.title or not post.content:
        return False

    try:
        session.add(post)
        session.commit()
        # logger.info(f'create post successful:{post}')
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when create post:{post}: {e}")
        raise RuntimeError("database connection error.")
    except Exception as e:
        logger.error(f"Unexpected error when create post:{post}: {e}")

    return False

def add_scrapy_record(llm: str, name: str, url: str, url_object_id: str, category: Optional[list] = None, tag: Optional[list] = None, title: str = "", content: str = "") -> bool:
    try:
        record = WPScrapyAiRecord(
            llm=llm,
            name=name,
            url=url,
            url_object_id=url_object_id,
            category=category or [],
            tag=tag or [],
            title=title,
            content=content
        )
        session.add(record)
        session.commit()
        return True
    except IntegrityError:  # 捕获唯一性约束错误
        session.rollback()
        return False
    except Exception as e:
        session.rollback()
        raise RuntimeError("database connection error.")


def get_scrapy_record_if_exist(url_object_id: str) -> Optional[WPScrapyAiRecord]:
    stmt = select(WPScrapyAiRecord).where(WPScrapyAiRecord.url_object_id == url_object_id)
    result = session.execute(stmt).scalar_one_or_none()
    return result



if __name__ == "__main__":
    # print(query_object_id("abc", "788196c1c93a20b969791cc0afdedb0a"))
    # print(count_urls_today('abc'))
    print(get_category("abc", "War"))


