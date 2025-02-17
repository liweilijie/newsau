"""Declare models and relationships."""
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT, VARCHAR, TEXT, BIGINT,DATETIME
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from typing_extensions import Annotated

from newsau.db import engin

Base = declarative_base()

# big_pk = Annotated[bigint, mapped_column(primary_key=True, autoincrement="auto")]
vch255_notnull = Annotated[str, mapped_column(String(255), nullable=False)]


class WPScrapyNews(Base):
    """WordPress scrapy news url and content."""

    __tablename__ = "wp_scrapy_news"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement="auto")
    name: Mapped[vch255_notnull]
    origin_title = Column(TEXT, nullable=False)
    title = Column(TEXT, nullable=False)
    category = Column(VARCHAR(255))
    topic = Column(VARCHAR(512))
    url = Column(VARCHAR(512), nullable=False, unique=True)
    url_object_id = Column(VARCHAR(64), nullable=False, unique=True)
    front_image_url = Column(LONGTEXT)
    front_image_path = Column(LONGTEXT)
    origin_content = Column(LONGTEXT, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    post_id = Column(BIGINT(unsigned=True), unique=True)
    post_date = Column(DATETIME)
    scrapy_date = Column(DATETIME, server_default=func.now())

    def __repr__(self):
        return (f"<wp_scrapy_news name={self.name}, "
                f"origin_title={self.origin_title}, "
                f"title={self.title}, "
                f"category={self.category}, "
                f"topic={self.topic}, "
                f"url={self.url}, "
                f"url_object_id={self.url_object_id}, "
                f"front_image_url={self.front_image_url}, "
                f"front_image_path={self.front_image_path}, "
                f"origin_content={self.origin_content}, "
                f"content={self.content}, "
                f"post_id={self.post_id}, "
                f"post_date={self.post_date}, "
                f"scrapy_date={self.scrapy_date}>")


class WPScrapyCategory(Base):
    """WordPress scrapy category for content"""

    __tablename__ = "wp_scrapy_category"

    # id: Mapped[big_pk]
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement="auto")
    news_category: Mapped[vch255_notnull]
    scrapy_category: Mapped[vch255_notnull]
    source_website: Mapped[vch255_notnull]

    def __repr__(self):
        return f'<wp_scrapy_category news_category:{self.news_category}, scrapy_category:{self.scrapy_category}, website:{self.source_website}>'

Base.metadata.create_all(engin)