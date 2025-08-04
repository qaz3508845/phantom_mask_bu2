"""
藥局相關 API 端點
實作需求1: 藥局列表查詢，支援時間/星期過濾/關鍵字搜尋
"""

from fastapi import APIRouter, Depends, HTTPException, Query
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from typing import List, Optional, Union
from datetime import time
from app.database.connection import get_db
from app.schemas.schemas import PharmacyResponse, PharmacyWithMaskCountResponse
from app.models import Pharmacy, Mask

router = APIRouter()

def _validate_day_format(day_input: str) -> str:
    """驗證並標準化星期格式，支援英文和數字"""
    if not day_input:
        return ""
    
    day_input = day_input.lower().strip()
    
    # 英文單字對照
    day_names = {
        "monday": "monday", "tuesday": "tuesday", "wednesday": "wednesday",
        "thursday": "thursday", "friday": "friday", "saturday": "saturday", "sunday": "sunday"
    }
    
    # 數字對照 (ISO 8601: 1=Monday, 7=Sunday)
    day_numbers = {
        "1": "monday", "2": "tuesday", "3": "wednesday",
        "4": "thursday", "5": "friday", "6": "saturday", "7": "sunday"
    }
    
    if day_input in day_names:
        return day_names[day_input]
    elif day_input in day_numbers:
        return day_numbers[day_input]
    else:
        raise HTTPException(
            status_code=422, 
            detail=f"無效的星期格式: {day_input}。請使用英文 (monday-sunday) 或數字 (1-7，1=星期一)"
        )

def _validate_time_format(time_str: str) -> str:
    """驗證時間格式 (HH:MM)"""
    if not re.match(r'^([01]\d|2[0-3]):[0-5]\d$', time_str):
        raise HTTPException(
            status_code=422, 
            detail=f"無效的時間格式: {time_str}。請使用 HH:MM 格式，例如: 09:30, 14:00, 23:59"
        )
    return time_str

def _parse_time(time_str: str):
    """解析時間字串 (HH:MM) 為 time 物件"""
    try:
        hour, minute = map(int, time_str.split(':'))
        from datetime import time as dt_time
        return dt_time(hour, minute)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"無效的時間格式: {time_str}，請使用 HH:MM 格式")

def check_pharmacy_open(opening_hours: dict, day_of_week: str, check_time=None) -> bool:
    """
    檢查藥局在指定日期和時間是否營業
    
    Args:
        opening_hours: 營業時間 JSON
        day_of_week: 星期 (monday, tuesday, ...)
        check_time: 檢查時間 (可選)
    """
    if not opening_hours or day_of_week not in opening_hours:
        return False
    
    day_schedule = opening_hours[day_of_week]
    if not day_schedule or 'open' not in day_schedule or 'close' not in day_schedule:
        return False
    
    # 如果沒有指定時間，只要該日有營業就符合
    if not check_time:
        return True
    
    try:
        shop_open = _parse_time(day_schedule['open'])  # type: ignore
        shop_close = _parse_time(day_schedule['close'])  # type: ignore
        time_obj = _parse_time(check_time)  # type: ignore
        return shop_open <= time_obj <= shop_close
    except Exception:
        return False



@router.get("/", response_model=List[PharmacyResponse])
async def list_pharmacies(
    day: Optional[str] = Query(None, description="星期過濾 (支援英文: monday-sunday 或數字: 1-7)"),
    time_filter: Optional[str] = Query(None, description="時間過濾 (HH:MM 格式)", alias="time"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="取得筆數"),
    db: Session = Depends(get_db)
):
    """
    列出藥局列表
    支援特定時間點和星期過濾
    
    需求1: List pharmacies, optionally filtered by specific time and/or day of the week
    
    使用範例：
    - ?day=wednesday&time=14:30        # 星期三下午2點30分營業的藥局
    - ?day=3&time=14:30                # 同上 (數字格式: 3=星期三)
    - ?day=saturday&time=22:00         # 星期六晚上10點營業的藥局  
    - ?day=6&time=22:00                # 同上 (數字格式: 6=星期六)
    - ?day=sunday                      # 星期日有營業的藥局
    - ?day=7                           # 同上 (數字格式: 7=星期日)
    - ?time=09:00                      # 早上9點有營業的藥局（任何一天）
    - ?search=大樹                     # 搜尋名稱包含「大樹」的藥局
    
    星期格式：英文 (monday-sunday) 或數字 (1-7，1=星期一)
    時間格式：HH:MM (例如: 09:30, 14:00, 23:59)
    """
    query = db.query(Pharmacy)
    if search:
        query = query.filter(Pharmacy.name.ilike(f"%{search}%"))
    
    pharmacies = query.offset(skip).limit(limit).all()
    
    # 驗證和標準化輸入參數
    normalized_day = None
    if day:
        normalized_day = _validate_day_format(day)
    
    if time_filter:
        _validate_time_format(time_filter)
    
    # 如果有時間或星期過濾，需要在 Python 中進一步過濾
    if normalized_day or time_filter:
        filtered_pharmacies = []
        
        for pharmacy in pharmacies:
            # 如果沒有營業時間資料，跳過
            if pharmacy.opening_hours is None:
                continue
            
            # 確保 opening_hours 是 dict 格式
            opening_hours = pharmacy.opening_hours
            if isinstance(opening_hours, str):
                try:
                    import json
                    opening_hours = json.loads(opening_hours)
                except json.JSONDecodeError:
                    continue
            
            if not isinstance(opening_hours, dict):
                continue
            
            # 根據過濾條件檢查
            if normalized_day and time_filter:
                # 有星期和時間條件
                if check_pharmacy_open(opening_hours, normalized_day, time_filter):
                    filtered_pharmacies.append(pharmacy)
            elif normalized_day:
                # 只有星期條件
                if check_pharmacy_open(opening_hours, normalized_day):
                    filtered_pharmacies.append(pharmacy)
            elif time_filter:
                # 只有時間條件，檢查所有營業日是否有符合的
                is_open_any_day = False
                for day_name in opening_hours.keys():
                    if check_pharmacy_open(opening_hours, day_name, time_filter):
                        is_open_any_day = True
                        break
                if is_open_any_day:
                    filtered_pharmacies.append(pharmacy)
        
        pharmacies = filtered_pharmacies
    
    return pharmacies

@router.get("/filter/masks", response_model=List[PharmacyWithMaskCountResponse])
async def filter_pharmacies_by_masks(
    min_price: Optional[Decimal] = Query(None, ge=0, description="價格下限（選填）"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="價格上限（選填）"),
    min_count: Optional[int] = Query(None, ge=0, description="口罩數量下限（選填）"),
    max_count: Optional[int] = Query(None, ge=0, description="口罩數量上限（選填）"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="取得筆數"),
    db: Session = Depends(get_db)
):
    """
    根據口罩數量和價格範圍篩選藥局
    
    需求3: List all pharmacies that offer a number of mask products within a given price range, 
           where the count is above, below, or between given thresholds
    
    使用範例：
    - ?min_price=10&max_price=50&min_count=100    # 在10-50元範圍內有100個以上口罩庫存的藥局
    - ?max_price=100&max_count=500                # 在100元以下有500個以下口罩庫存的藥局  
    - ?min_price=20&max_price=80&min_count=50&max_count=300  # 在20-80元範圍內有50-300個口罩庫存的藥局
    - ?min_count=100                              # 有100個以上口罩庫存的藥局（不限價格）
    - ?min_price=10&max_price=50                  # 在10-50元範圍內有口罩庫存的藥局（不限數量）
    """
    
    # 參數驗證
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="價格下限不能大於價格上限")
    
    if min_count is not None and max_count is not None and min_count > max_count:
        raise HTTPException(status_code=422, detail="數量下限不能大於數量上限")
    
    # 建立口罩子查詢：計算每家藥局符合價格條件的口罩總庫存數量
    mask_query = db.query(
        Mask.pharmacy_id.label("pharmacy_id"),
        func.sum(Mask.stock_quantity).label("mask_count")
    )
    
    # 動態加入價格過濾條件
    if min_price is not None:
        mask_query = mask_query.filter(Mask.price >= min_price)
    if max_price is not None:
        mask_query = mask_query.filter(Mask.price <= max_price)
    
    mask_subquery = mask_query.group_by(Mask.pharmacy_id).subquery()

    # 主查詢：聯接藥局和口罩數量
    query = (
        db.query(
            Pharmacy,
            mask_subquery.c.mask_count
        )
        .join(mask_subquery, Pharmacy.id == mask_subquery.c.pharmacy_id)
    )

    # 根據口罩數量條件過濾
    if min_count is not None:
        query = query.filter(mask_subquery.c.mask_count >= min_count)
    if max_count is not None:
        query = query.filter(mask_subquery.c.mask_count <= max_count)

    # 執行查詢並分頁
    results = query.offset(skip).limit(limit).all()
    
    # 組建回應
    filtered_pharmacies = []
    for pharmacy, mask_count in results:
        pharmacy_dict = {
            "id": pharmacy.id,
            "name": pharmacy.name,
            "cash_balance": pharmacy.cash_balance,
            "opening_hours": pharmacy.opening_hours,
            "created_at": pharmacy.created_at,
            "updated_at": pharmacy.updated_at,
            "mask_count": int(mask_count) if mask_count else 0  # 確保是整數，處理 NULL 值
        }
        filtered_pharmacies.append(pharmacy_dict)
    
    return filtered_pharmacies