"""
藥局資料表模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Pharmacy(Base):
    """藥局模型"""
    __tablename__ = "pharmacies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cash_balance = Column(Float, default=0.0)
    
    # 營業時間 (JSON 格式存儲)
    opening_hours = Column(Text)  # 存儲 JSON 字串
    
    # 建立時間和更新時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯關係
    masks = relationship("Mask", back_populates="pharmacy")
    transactions = relationship("Transaction", back_populates="pharmacy")