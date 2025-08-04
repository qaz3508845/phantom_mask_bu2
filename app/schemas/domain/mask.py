"""
口罩相關 Schema 模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from ..base import BaseResponse


class MaskBase(BaseModel):
    """口罩基礎模型"""
    name: str = Field(..., description="口罩名稱", examples=["True Barrier (green) (3 per pack)"])
    price: Decimal = Field(..., gt=0, description="價格", examples=[15.50])
    stock_quantity: int = Field(..., ge=0, description="庫存數量", examples=[100])


class MaskCreate(MaskBase):
    """建立口罩請求模型"""
    pharmacy_id: int = Field(..., description="藥局ID", examples=[1])


class MaskUpdate(BaseModel):
    """更新口罩請求模型"""
    name: Optional[str] = Field(None, description="口罩名稱", examples=["True Barrier (green) (3 per pack)"])
    price: Optional[Decimal] = Field(None, gt=0, description="價格", examples=[15.50])
    stock_quantity: Optional[int] = Field(None, ge=0, description="庫存數量", examples=[100])


class MaskResponse(MaskBase, BaseResponse):
    """口罩回應模型"""
    id: int = Field(..., description="口罩ID", examples=[1])
    pharmacy_id: int = Field(..., description="藥局ID", examples=[1])
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")


# 庫存管理相關模型
class StockUpdateRequest(BaseModel):
    """庫存更新請求模型"""
    quantity_change: int = Field(..., description="庫存變動數量（正數增加，負數減少）", examples=[10])
    reason: Optional[str] = Field(None, max_length=255, description="更新原因（選填）", examples=["補貨入庫"])


class StockUpdateResponse(BaseResponse):
    """庫存更新回應模型"""
    mask_id: int = Field(..., description="口罩ID")
    mask_name: str = Field(..., description="口罩名稱")
    old_quantity: int = Field(..., description="原庫存數量")
    quantity_change: int = Field(..., description="變動數量")
    new_quantity: int = Field(..., description="新庫存數量")
    updated_at: datetime = Field(..., description="更新時間")
    reason: Optional[str] = Field(None, description="更新原因")


# 批量管理相關模型
class BatchMaskItem(BaseModel):
    """批量口罩項目模型"""
    name: str = Field(..., max_length=255, description="口罩名稱", examples=["True Barrier (green) (3 per pack)"])
    price: Decimal = Field(..., gt=0, description="價格", examples=[15.50])
    stock_quantity: int = Field(..., ge=0, description="庫存數量", examples=[100])
    # 可選的 ID，如果提供則更新現有，否則建立新的
    mask_id: Optional[int] = Field(None, description="口罩ID（更新時提供）", examples=[1])


class BatchMaskRequest(BaseModel):
    """批量口罩管理請求模型"""
    pharmacy_id: int = Field(..., description="藥局ID", examples=[1])
    masks: List[BatchMaskItem] = Field(..., min_length=1, max_length=100, description="口罩項目列表")


class BatchMaskResponse(BaseResponse):
    """批量口罩管理回應模型"""
    pharmacy_id: int = Field(..., description="藥局ID")
    pharmacy_name: str = Field(..., description="藥局名稱")
    total_items: int = Field(..., description="總項目數")
    created_count: int = Field(..., description="建立數量")
    updated_count: int = Field(..., description="更新數量")
    created_masks: List[MaskResponse] = Field(default=[], description="建立的口罩列表")
    updated_masks: List[MaskResponse] = Field(default=[], description="更新的口罩列表")
    failed_items: List[str] = Field(default=[], description="失敗項目列表")