"""Create SQLAlchemy engine and session objects."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsau.settings import SQLALCHEMY_DATABASE_URI

# Create database engine
engin = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, pool_recycle=1800, pool_pre_ping=True)

# Create database session
Session = sessionmaker(bind=engin)
session = Session()
