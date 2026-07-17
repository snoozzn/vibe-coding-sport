# ============================================================
# VibeSport Backend - 数据库连接
# ============================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

engine = create_engine(
    settings.db_url,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False,  # 生产环境设为 False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖注入: 获取数据库会话."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
