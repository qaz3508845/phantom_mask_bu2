#!/usr/bin/env python3
"""
資料庫初始化腳本
確保在應用程式啟動前創建所有必要的表
"""

import sys
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.database.connection import engine, Base
from app.models import Pharmacy, Mask, User, Transaction

def wait_for_db(max_retries=30, delay=1):
    """等待資料庫連線可用"""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("資料庫連線成功")
            return True
        except OperationalError as e:
            print(f"等待資料庫連線... ({i+1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            print(f"等待資料庫連線... ({i+1}/{max_retries}) - {e}")
            time.sleep(delay)
    
    print("無法連接到資料庫")
    return False

def create_tables():
    """創建所有資料庫表"""
    try:
        Base.metadata.create_all(bind=engine)
        print("資料庫表創建成功")
        return True
    except Exception as e:
        print(f"創建資料庫表時發生錯誤: {e}")
        return False

if __name__ == "__main__":
    print("開始初始化資料庫...")
    
    if not wait_for_db():
        sys.exit(1)
    
    if not create_tables():
        sys.exit(1)
    
    print("資料庫初始化完成")