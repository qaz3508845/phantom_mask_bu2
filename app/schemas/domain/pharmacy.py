"""
藥局相關 Schema 模型
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from ..base import BaseResponse


class PharmacyBase(BaseModel):
    """藥局基礎模型"""
    name: str = Field(..., description="藥局名稱", examples=["DFW Wellness"])
    cash_balance: Decimal = Field(..., description="現金餘額", examples=[10000.00])
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="營業時間", examples=[{"monday": "09:00-18:00", "tuesday": "09:00-18:00"}])


class PharmacyResponse(PharmacyBase, BaseResponse):
    """藥局回應模型"""
    id: int = Field(..., description="藥局ID", examples=[1])
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


class PharmacyWithMaskCountResponse(PharmacyResponse):
    """藥局回應模型（含口罩庫存數量）"""
    mask_count: int = Field(..., description="符合條件的口罩總庫存數量")