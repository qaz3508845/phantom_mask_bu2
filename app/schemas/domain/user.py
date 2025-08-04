"""
用戶相關 Schema 模型
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from ..base import BaseResponse


class UserBase(BaseModel):
    """用戶基礎模型"""
    name: str = Field(..., description="用戶名稱", examples=["Yvonne Guerrero"])
    cash_balance: Decimal = Field(..., ge=0, description="現金餘額", examples=[5000.00])


class UserCreate(UserBase):
    """建立用戶請求模型"""
    pass


class UserUpdate(BaseModel):
    """更新用戶請求模型"""
    name: Optional[str] = Field(None, description="用戶名稱", examples=["Yvonne Guerrero"])
    cash_balance: Optional[Decimal] = Field(None, ge=0, description="現金餘額", examples=[5000.00])


class UserResponse(UserBase, BaseResponse):
    """用戶回應模型"""
    id: int = Field(..., description="用戶ID", examples=[1])
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")


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