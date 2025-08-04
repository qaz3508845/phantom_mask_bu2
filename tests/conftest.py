"""
pytest 配置文件
提供測試共用的 fixtures 和設定
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db, Base
from app.models import Pharmacy, Mask, User, Transaction

# 測試用資料庫 URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# 建立測試資料庫引擎
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """覆寫資料庫依賴注入，使用測試資料庫"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 覆寫應用程式的資料庫依賴
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """為每個測試提供乾淨的資料庫會話"""
    # 建立所有表格
    Base.metadata.create_all(bind=engine)
    
    # 建立會話
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理所有表格
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """提供 FastAPI 測試客戶端"""
    # 確保測試表格存在
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 清理表格
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def sample_pharmacy(db_session):
    """建立範例藥局資料"""
    pharmacy = Pharmacy(
        name="測試藥局",
        cash_balance=1000.00,
        opening_hours='{"monday": {"open": "08:00", "close": "18:00"}}'
    )
    db_session.add(pharmacy)
    db_session.commit()
    db_session.refresh(pharmacy)
    return pharmacy

@pytest.fixture(scope="function")
def sample_mask(db_session, sample_pharmacy):
    """建立範例口罩資料"""
    mask = Mask(
        name="測試口罩",
        price=10.50,
        stock_quantity=100,
        pharmacy_id=sample_pharmacy.id
    )
    db_session.add(mask)
    db_session.commit()
    db_session.refresh(mask)
    return mask

@pytest.fixture(scope="function")
def sample_user(db_session):
    """建立範例用戶資料"""
    user = User(
        name="測試用戶",
        cash_balance=500.00
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def sample_transaction(db_session, sample_user, sample_pharmacy, sample_mask):
    """建立範例交易資料"""
    from datetime import datetime
    
    transaction = Transaction(
        user_id=sample_user.id,
        pharmacy_id=sample_pharmacy.id,
        mask_id=sample_mask.id,
        quantity=2,
        unit_price=10.50,
        total_amount=21.00,
        transaction_datetime=datetime.now()
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction