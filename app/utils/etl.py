"""
ETL 腳本 - 處理和載入原始資料
Extract, Transform, Load 原始 JSON 資料到 PostgreSQL 資料庫
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import SessionLocal, engine
from app.models import Pharmacy, Mask, User, Transaction
from app.core.logging_config import get_logger

# 建立 ETL 專用 logger
logger = get_logger("etl")

def parse_opening_hours(opening_hours_str: str) -> Dict[str, Any]:
    """
    解析營業時間字串為結構化資料
    例如: "Mon 08:00 - 18:00, Tue 13:00 - 18:00"
    """
    if not opening_hours_str:
        return {}
    
    hours_dict = {}
    # 分割不同日期的營業時間
    day_schedules = opening_hours_str.split(', ')
    
    for schedule in day_schedules:
        schedule = schedule.strip()
        if not schedule:
            continue
            
        try:
            # 解析 "Mon 08:00 - 18:00" 格式
            parts = schedule.split(' ')
            if len(parts) >= 4:
                day = parts[0].lower()
                start_time = parts[1]
                end_time = parts[3]
                
                # 轉換星期縮寫
                day_mapping = {
                    'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
                    'thur': 'thursday', 'thu': 'thursday', 'fri': 'friday',
                    'sat': 'saturday', 'sun': 'sunday'
                }
                
                full_day = day_mapping.get(day, day)
                hours_dict[full_day] = {
                    'open': start_time,
                    'close': end_time
                }
        except (IndexError, ValueError) as e:
            logger.warning(f"無法解析營業時間: {schedule}, 錯誤: {e}")
            continue
    
    return hours_dict

def load_pharmacies_data(file_path: str, db: Session):
    """載入藥局資料"""
    logger.info(f"正在載入藥局資料從: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        pharmacies_data = json.load(f)
    
    pharmacy_name_to_id = {}
    
    for pharmacy_data in pharmacies_data:
        # 檢查藥局是否已存在
        existing_pharmacy = db.query(Pharmacy).filter(
            Pharmacy.name == pharmacy_data['name']
        ).first()
        
        if existing_pharmacy:
            logger.debug(f"藥局 '{pharmacy_data['name']}' 已存在，跳過")
            pharmacy_name_to_id[pharmacy_data['name']] = existing_pharmacy.id
            continue
        
        # 建立藥局記錄
        opening_hours_json = parse_opening_hours(pharmacy_data.get('openingHours', ''))
        
        pharmacy = Pharmacy(
            name=pharmacy_data['name'],
            cash_balance=pharmacy_data.get('cashBalance', 0.0),
            opening_hours=json.dumps(opening_hours_json, ensure_ascii=False)
        )
        
        db.add(pharmacy)
        db.flush()  # 取得 pharmacy.id
        
        pharmacy_name_to_id[pharmacy_data['name']] = pharmacy.id
        logger.info(f"已建立藥局: {pharmacy.name} (ID: {pharmacy.id})")
        
        # 建立口罩記錄
        for mask_data in pharmacy_data.get('masks', []):
            mask = Mask(
                name=mask_data['name'],
                price=mask_data['price'],
                stock_quantity=mask_data['stockQuantity'],
                pharmacy_id=pharmacy.id
            )
            db.add(mask)
        
        logger.info(f"已為藥局 '{pharmacy.name}' 建立 {len(pharmacy_data.get('masks', []))} 個口罩產品")
    
    db.commit()
    logger.info(f"藥局資料載入完成，共處理 {len(pharmacies_data)} 家藥局")
    return pharmacy_name_to_id

def load_users_data(file_path: str, db: Session, pharmacy_name_to_id: Dict[str, int]):
    """載入用戶資料和購買歷史"""
    logger.info(f"正在載入用戶資料從: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        users_data = json.load(f)
    
    for user_data in users_data:
        # 檢查用戶是否已存在
        existing_user = db.query(User).filter(
            User.name == user_data['name']
        ).first()
        
        if existing_user:
            logger.debug(f"用戶 '{user_data['name']}' 已存在，跳過")
            continue
        
        # 建立用戶記錄
        user = User(
            name=user_data['name'],
            cash_balance=user_data.get('cashBalance', 0.0)
        )
        
        db.add(user)
        db.flush()  # 取得 user.id
        
        logger.info(f"已建立用戶: {user.name} (ID: {user.id})")
        
        # 處理購買歷史 - 每個 purchaseHistory 項目建立一個 Transaction 記錄
        purchase_histories = user_data.get('purchaseHistories', [])
        transaction_count = 0
        
        for purchase_history in purchase_histories:
            transaction_datetime_str = purchase_history['transactionDatetime']
            transaction_datetime = datetime.strptime(transaction_datetime_str, '%Y-%m-%d %H:%M:%S')
            
            # 查找藥局和口罩
            pharmacy_name = purchase_history['pharmacyName']
            mask_name = purchase_history['maskName']
            
            pharmacy_id = pharmacy_name_to_id.get(pharmacy_name)
            if not pharmacy_id:
                logger.warning(f"找不到藥局 '{pharmacy_name}'，跳過此交易記錄")
                continue
            
            # 查找口罩
            mask = db.query(Mask).filter(
                Mask.name == mask_name,
                Mask.pharmacy_id == pharmacy_id
            ).first()
            
            if not mask:
                logger.warning(f"在藥局 '{pharmacy_name}' 找不到口罩 '{mask_name}'，跳過此交易記錄")
                continue
            
            # 計算金額
            unit_price = purchase_history['transactionAmount']
            quantity = purchase_history['transactionQuantity']
            total_amount = unit_price * quantity
            
            # 建立交易記錄 (直接對應 purchaseHistory)
            transaction = Transaction(
                user_id=user.id,
                pharmacy_id=pharmacy_id,
                mask_id=mask.id,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
                transaction_datetime=transaction_datetime
            )
            db.add(transaction)
            transaction_count += 1
        
        logger.info(f"已為用戶 '{user.name}' 建立 {transaction_count} 筆交易記錄")
    
    db.commit()
    logger.info(f"用戶資料載入完成，共處理 {len(users_data)} 名用戶")

def clear_all_data(db: Session):
    """清空所有資料 (開發測試用)"""
    logger.warning("正在清空所有資料...")
    
    # 按照外鍵依賴順序刪除
    db.execute(text("DELETE FROM transactions"))
    db.execute(text("DELETE FROM masks"))
    db.execute(text("DELETE FROM users"))
    db.execute(text("DELETE FROM pharmacies"))
    
    # 重置序列
    db.execute(text("ALTER SEQUENCE pharmacies_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE masks_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE transactions_id_seq RESTART WITH 1"))
    
    db.commit()
    logger.info("所有資料已清空")

def run_etl(clear_existing_data: bool = False):
    """執行完整的 ETL 流程"""
    logger.info("開始執行 ETL 流程...")
    
    # 取得資料檔案路徑
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    pharmacies_file = os.path.join(current_dir, 'data', 'pharmacies.json')
    users_file = os.path.join(current_dir, 'data', 'users.json')
    
    # 檢查檔案是否存在
    if not os.path.exists(pharmacies_file):
        raise FileNotFoundError(f"找不到藥局資料檔案: {pharmacies_file}")
    
    if not os.path.exists(users_file):
        raise FileNotFoundError(f"找不到用戶資料檔案: {users_file}")
    
    # 建立資料庫會話
    db = SessionLocal()
    
    try:
        # 清空現有資料 (如果指定)
        if clear_existing_data:
            clear_all_data(db)
        
        # 載入藥局資料
        pharmacy_name_to_id = load_pharmacies_data(pharmacies_file, db)
        
        # 載入用戶資料
        load_users_data(users_file, db, pharmacy_name_to_id)
        
        logger.info("ETL 流程執行完成！")
        
        # 顯示統計資訊
        pharmacy_count = db.query(Pharmacy).count()
        mask_count = db.query(Mask).count()
        user_count = db.query(User).count()
        transaction_count = db.query(Transaction).count()
        
        logger.info("=== 資料載入統計 ===")
        logger.info(f"藥局數量: {pharmacy_count}")
        logger.info(f"口罩產品數量: {mask_count}")
        logger.info(f"用戶數量: {user_count}")
        logger.info(f"交易記錄數量: {transaction_count}")
        
    except Exception as e:
        logger.error(f"ETL 執行錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # 執行 ETL 流程
    run_etl(clear_existing_data=True)