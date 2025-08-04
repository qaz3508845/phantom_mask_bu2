"""
交易相關 Schema 模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from ..base import BaseResponse
from .pharmacy import PharmacyResponse
from .mask import MaskResponse
from .user import UserResponse


class TransactionBase(BaseModel):
    """交易基礎模型"""
    quantity: int = Field(..., gt=0, description="購買數量", examples=[2])


class TransactionCreate(TransactionBase):
    """建立交易請求模型"""
    user_id: int = Field(..., description="用戶ID", examples=[1])
    pharmacy_id: int = Field(..., description="藥局ID", examples=[1])
    mask_id: int = Field(..., description="口罩ID", examples=[1])


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


# 多藥局交易相關模型
class MultiPharmacyTransactionItem(BaseModel):
    """多藥局交易項目"""
    pharmacy_id: int = Field(..., description="藥局ID", examples=[1])
    mask_id: int = Field(..., description="口罩ID", examples=[1])
    quantity: int = Field(..., gt=0, description="購買數量", examples=[2])


class MultiPharmacyTransactionCreate(BaseModel):
    """多藥局交易請求模型"""
    user_id: int = Field(..., description="用戶ID", examples=[1])
    items: List[MultiPharmacyTransactionItem] = Field(..., min_length=1, description="交易項目列表")


class MultiPharmacyTransactionResponse(BaseResponse):
    """多藥局交易回應模型"""
    user_id: int = Field(..., description="用戶ID")
    total_amount: Decimal = Field(..., description="總交易金額")
    total_items: int = Field(..., description="總項目數")
    transactions: List[TransactionResponse] = Field(..., description="交易記錄列表")
    success_count: int = Field(..., description="成功交易數")
    failed_items: List[str] = Field(default=[], description="失敗項目列表")