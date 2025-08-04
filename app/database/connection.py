"""
資料庫連線設定
管理 SQLAlchemy 引擎和工作階段
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """如果資料庫不存在則建立它"""
    # 建立到 postgres 預設資料庫的連線來建立新資料庫
    admin_url = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/postgres"
    
    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            # 檢查資料庫是否存在
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.postgres_db}'"))
            if not result.fetchone():
                # 資料庫不存在，建立它
                conn.execute(text(f"CREATE DATABASE {settings.postgres_db}"))
                logger.info(f"資料庫 '{settings.postgres_db}' 已成功建立")
            else:
                logger.info(f"資料庫 '{settings.postgres_db}' 已存在")
        admin_engine.dispose()
    except Exception as e:
        logger.error(f"建立資料庫時發生錯誤: {e}")
        raise

# 先嘗試建立資料庫
create_database_if_not_exists()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,  
    pool_pre_ping=True,   
    pool_recycle=300      
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def supports_for_update(db_session):
    """檢查資料庫是否支援 SELECT FOR UPDATE"""
    engine_name = db_session.bind.dialect.name.lower()
    # SQLite 不支援 FOR UPDATE
    return engine_name != 'sqlite'