import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./finance_dashboard.db",
)

# Railway uses postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    source = Column(String(100), nullable=False)
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    keywords = Column(Text, nullable=True)  # comma-separated nouns

    __table_args__ = (UniqueConstraint("link", name="uq_article_link"),)


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    id = Column(Integer, primary_key=True, index=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    total_articles = Column(Integer, default=0)
    new_articles = Column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    region = Column(String(50))
    job_type = Column(String(50))
    url = Column(String(1000))
    posted_date = Column(String(50))
    collected_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("url", name="uq_job_url"),)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
