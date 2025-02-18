import logging
from sqlalchemy.exc import SQLAlchemyError

from newsau.db import session
from newsau.db.models import WPScrapyNews, WPScrapyCategory
from sqlalchemy import and_
from sqlalchemy import func

from newsau.cache.rsync_status import accounts_store

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
        if existing_url is None:
            return False
        else:
            return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}, url_object_id:{url_object_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when query_object_id name:{name}, url_object_id:{url_object_id}: {e}")

    return False

def count_urls_today(name: str):
    try:
        today_count = session.query(WPScrapyNews).filter(
            and_(
                WPScrapyNews.name == name,
                func.DATE(WPScrapyNews.post_date) == func.current_date()
            )
        ).count()

        logger.info(f'today_count:{today_count}')
        if today_count is not None:
            return today_count
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}: {e}")
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

        logger.info(f'category:{category}')
        if category is not None:
            return category[0]
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when query_object_id name:{name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when query_object_id name:{name}: {e}")

    return None



# check if exceed
def check_if_exceed_num(name):
    current_count = count_urls_today(name)

    if current_count >= accounts_store.get()[name]["count_everyday"]:
        logger.info(
            f"afr we had {current_count} >= {accounts_store.get()[name]["count_everyday"]} and exceed the count limit and do nothing.")
        return True
    return False

def create_post(post: WPScrapyNews) -> bool:
    if not post.title or not post.content:
        return False

    try:
        session.add(post)
        session.commit()
        logger.info(f'create post successful:{post}')
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError error when create post:{post}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when create post:{post}: {e}")

    return False




if __name__ == "__main__":
    # print(query_object_id("abc", "788196c1c93a20b969791cc0afdedb0a"))
    # print(count_urls_today('abc'))
    print(get_category("abc", "War"))


