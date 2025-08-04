"""
交易記錄資料表模型
直接對應 users.json 中的 purchaseHistory 記錄
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Transaction(Base):
    """
    交易記錄模型
    對應 users.json 中每個 purchaseHistory 項目
    
    每筆記錄代表：用戶在某個時間從某個藥局購買某個口罩的交易
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外鍵關聯
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False, index=True)
    mask_id = Column(Integer, ForeignKey("masks.id"), nullable=False, index=True)
    
    # 交易資料 (對應 JSON 欄位)
    quantity = Column(Integer, nullable=False)  # transactionQuantity
    unit_price = Column(DECIMAL(10, 2), nullable=False)  # transactionAmount
    total_amount = Column(DECIMAL(10, 2), nullable=False)  # unit_price * quantity
    
    # 時間欄位
    transaction_datetime = Column(DateTime(timezone=True), nullable=False, index=True)  # transactionDatetime
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯關係
    user = relationship("User", back_populates="transactions")
    pharmacy = relationship("Pharmacy", back_populates="transactions")
    mask = relationship("Mask", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, pharmacy_id={self.pharmacy_id}, mask_id={self.mask_id}, total={self.total_amount})>" 
        