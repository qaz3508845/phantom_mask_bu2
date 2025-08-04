"""
口罩產品資料表模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Mask(Base):
    """口罩產品模型"""
    __tablename__ = "masks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    
    # 外鍵
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    
    # 建立時間和更新時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯關係
    pharmacy = relationship("Pharmacy", back_populates="masks")
    transactions = relationship("Transaction", back_populates="mask")