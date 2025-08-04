"""
Pydantic 模型定義
用於 API 請求和回應的資料驗證
"""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

# 基礎回應模型
class BaseResponse(BaseModel):
    """基礎回應模型"""
    class Config:
        from_attributes = True

# 藥局相關模型
class PharmacyBase(BaseModel):
    """藥局基礎模型"""
    name: str = Field(..., description="藥局名稱")
    cash_balance: Decimal = Field(..., description="現金餘額")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="營業時間")



class PharmacyResponse(PharmacyBase, BaseResponse):
    """藥局回應模型"""
    id: int = Field(..., description="藥局ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    @field_validator('opening_hours', mode='before')
    @classmethod
    def parse_opening_hours(cls, v):
        """處理從資料庫讀取的 JSON 字串"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

# 口罩相關模型  
class MaskBase(BaseModel):
    """口罩基礎模型"""
    name: str = Field(..., description="口罩名稱")
    price: Decimal = Field(..., gt=0, description="價格")
    stock_quantity: int = Field(..., ge=0, description="庫存數量")

class MaskCreate(MaskBase):
    """建立口罩請求模型"""
    pharmacy_id: int = Field(..., description="藥局ID")

class MaskUpdate(BaseModel):
    """更新口罩請求模型"""
    name: Optional[str] = Field(None, description="口罩名稱")
    price: Optional[Decimal] = Field(None, gt=0, description="價格")
    stock_quantity: Optional[int] = Field(None, ge=0, description="庫存數量")

class MaskResponse(MaskBase, BaseResponse):
    """口罩回應模型"""
    id: int = Field(..., description="口罩ID")
    pharmacy_id: int = Field(..., description="藥局ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

class PharmacyWithMaskCountResponse(PharmacyResponse):
    """藥局回應模型（含口罩庫存數量）"""
    mask_count: int = Field(..., description="符合條件的口罩總庫存數量")

# 用戶相關模型
class UserBase(BaseModel):
    """用戶基礎模型"""
    name: str = Field(..., description="用戶名稱")
    cash_balance: float = Field(..., ge=0, description="現金餘額")

class UserCreate(UserBase):
    """建立用戶請求模型"""
    pass

class UserUpdate(BaseModel):
    """更新用戶請求模型"""
    name: Optional[str] = Field(None, description="用戶名稱")
    cash_balance: Optional[Decimal] = Field(None, ge=0, description="現金餘額")

class UserResponse(UserBase, BaseResponse):
    """用戶回應模型"""
    id: int = Field(..., description="用戶ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

# 交易相關模型
class TransactionBase(BaseModel):
    """交易基礎模型"""
    quantity: int = Field(..., gt=0, description="購買數量")

class TransactionCreate(TransactionBase):
    """建立交易請求模型"""
    user_id: int = Field(..., description="用戶ID")
    pharmacy_id: int = Field(..., description="藥局ID")
    mask_id: int = Field(..., description="口罩ID")

class TransactionResponse(TransactionBase, BaseResponse):
    """交易回應模型"""
    id: int = Field(..., description="交易ID")
    user_id: int = Field(..., description="用戶ID")
    pharmacy_id: int = Field(..., description="藥局ID")
    mask_id: int = Field(..., description="口罩ID")
    unit_price: Decimal = Field(..., description="單價")
    total_amount: Decimal = Field(..., description="總金額")
    transaction_datetime: datetime = Field(..., description="交易時間")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

class TransactionDetailResponse(TransactionBase, BaseResponse):
    """交易詳細回應模型（完整版）"""
    id: int = Field(..., description="交易ID")
    user_id: int = Field(..., description="用戶ID")
    pharmacy_id: int = Field(..., description="藥局ID")
    mask_id: int = Field(..., description="口罩ID")
    unit_price: Decimal = Field(..., description="單價")
    total_amount: Decimal = Field(..., description="總金額")
    transaction_datetime: datetime = Field(..., description="交易時間")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    # 完整的關聯資料
    user: Optional[UserResponse] = None
    pharmacy: Optional[PharmacyResponse] = None
    mask: Optional[MaskResponse] = None
    

# 多藥局交易相關模型 (需求5)
class MultiPharmacyTransactionItem(BaseModel):
    """多藥局交易項目"""
    pharmacy_id: int = Field(..., description="藥局ID")
    mask_id: int = Field(..., description="口罩ID")
    quantity: int = Field(..., gt=0, description="購買數量")

class MultiPharmacyTransactionCreate(BaseModel):
    """多藥局交易請求模型"""
    user_id: int = Field(..., description="用戶ID")
    items: List[MultiPharmacyTransactionItem] = Field(..., min_length=1, description="交易項目列表")

class MultiPharmacyTransactionResponse(BaseResponse):
    """多藥局交易回應模型"""
    user_id: int = Field(..., description="用戶ID")
    total_amount: Decimal = Field(..., description="總交易金額")
    total_items: int = Field(..., description="總項目數")
    transactions: List[TransactionResponse] = Field(..., description="交易記錄列表")
    success_count: int = Field(..., description="成功交易數")
    failed_items: List[str] = Field(default=[], description="失敗項目列表")
    

# 用戶統計相關模型
class UserRankingResponse(BaseResponse):
    """用戶排行榜回應模型"""
    rank: int = Field(..., description="排名")
    user_id: int = Field(..., description="用戶ID")
    user_name: str = Field(..., description="用戶名稱")
    cash_balance: Decimal = Field(..., description="現金餘額")
    total_spending: Decimal = Field(..., description="總消費金額")
    total_quantity: int = Field(..., description="總購買數量")
    total_transactions: int = Field(..., description="總交易次數")
    ranking_type: str = Field(..., description="排行榜類型")
    start_date: Optional[date] = Field(None, description="統計開始日期")
    end_date: Optional[date] = Field(None, description="統計結束日期")
    

