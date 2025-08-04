"""
搜尋相關 Schema 模型
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

from ..base import BaseResponse


class SearchResultItem(BaseModel):
    """搜尋結果項目模型"""
    id: int = Field(..., description="項目ID")
    name: str = Field(..., description="項目名稱")
    type: str = Field(..., description="項目類型: pharmacy 或 mask")
    relevance_score: int = Field(..., description="相關性分數 (3=完全匹配, 2=開頭匹配, 1=包含匹配)")
    
    # 藥局特有字段
    cash_balance: Optional[Decimal] = Field(None, description="現金餘額（藥局專用）")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="營業時間（藥局專用）")
    
    # 口罩特有字段  
    price: Optional[Decimal] = Field(None, description="價格（口罩專用）")
    stock_quantity: Optional[int] = Field(None, description="庫存數量（口罩專用）")
    pharmacy_id: Optional[int] = Field(None, description="藥局ID（口罩專用）")
    
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


class UnifiedSearchResponse(BaseResponse):
    """統一搜尋回應模型"""
    query: str = Field(..., description="搜尋關鍵字")
    total_results: int = Field(..., description="總結果數")
    pharmacy_count: int = Field(..., description="藥局結果數")
    mask_count: int = Field(..., description="口罩結果數")
    results: List[SearchResultItem] = Field(..., description="搜尋結果列表（按相關性排序）")
    pagination: Dict[str, int] = Field(..., description="分頁資訊")