"""
交易服務模組
處理交易相關的業務邏輯，包含單筆和多藥局交易
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.models import Transaction, User, Pharmacy, Mask
from app.schemas.schemas import (
    TransactionCreate, 
    TransactionResponse,
    MultiPharmacyTransactionCreate,
    MultiPharmacyTransactionItem,
    MultiPharmacyTransactionResponse
)

class TransactionService:
    """交易服務類"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_transaction_item(self, user_id: int, pharmacy_id: int, mask_id: int, quantity: int) -> Tuple[User, Pharmacy, Mask, Decimal]:
        """
        驗證交易項目的有效性
        返回: (user, pharmacy, mask, total_amount)
        """
        # 檢查用戶是否存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"用戶 ID {user_id} 不存在")
        
        # 檢查藥局是否存在
        pharmacy = self.db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(status_code=404, detail=f"藥局 ID {pharmacy_id} 不存在")
        
        # 檢查口罩是否存在且屬於該藥局
        mask = self.db.query(Mask).filter(
            Mask.id == mask_id,
            Mask.pharmacy_id == pharmacy_id
        ).first()
        if not mask:
            raise HTTPException(status_code=404, detail=f"藥局 {pharmacy_id} 沒有口罩 ID {mask_id}")
        
        # 檢查庫存是否足夠
        stock_qty = getattr(mask, 'stock_quantity')
        if stock_qty < quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"口罩 {mask.name} 庫存不足，現有庫存: {stock_qty}，需求: {quantity}"
            )
        
        # 計算總金額
        mask_price = getattr(mask, 'price')
        total_amount = mask_price * quantity
        
        # 檢查用戶餘額是否足夠
        user_balance = getattr(user, 'cash_balance')
        if user_balance < total_amount:
            raise HTTPException(
                status_code=400,
                detail=f"用戶餘額不足，現有餘額: {user.cash_balance}，需要: {total_amount}"
            )
        
        return user, pharmacy, mask, total_amount
    
    def create_single_transaction(self, transaction_data: TransactionCreate) -> TransactionResponse:
        """建立單筆交易"""
        try:
            # 驗證交易項目
            user, pharmacy, mask, total_amount = self.validate_transaction_item(
                transaction_data.user_id,
                transaction_data.pharmacy_id,
                transaction_data.mask_id,
                transaction_data.quantity
            )
            
            # 建立交易記錄
            transaction = Transaction(
                user_id=transaction_data.user_id,
                pharmacy_id=transaction_data.pharmacy_id,
                mask_id=transaction_data.mask_id,
                quantity=transaction_data.quantity,
                unit_price=mask.price,
                total_amount=total_amount,
                transaction_datetime=datetime.now()
            )
            
            # 更新庫存和餘額
            setattr(mask, 'stock_quantity', getattr(mask, 'stock_quantity') - transaction_data.quantity)
            setattr(user, 'cash_balance', getattr(user, 'cash_balance') - total_amount)
            setattr(pharmacy, 'cash_balance', getattr(pharmacy, 'cash_balance') + total_amount)
            
            # 儲存到資料庫
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            return TransactionResponse.model_validate(transaction)
        
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"資料庫操作失敗: {str(e)}")
    
    def create_multi_pharmacy_transaction(self, transaction_data: MultiPharmacyTransactionCreate) -> MultiPharmacyTransactionResponse:
        """建立多藥局交易"""
        transactions = []
        total_amount = Decimal('0.00')
        
        try:
            # 第一階段：驗證所有項目，如果任何項目無效則整筆取消
            validated_items = []
            user_obj: Optional[User] = None
            
            for i, item in enumerate(transaction_data.items):
                user, pharmacy, mask, item_total = self.validate_transaction_item(
                    transaction_data.user_id,
                    item.pharmacy_id,
                    item.mask_id,
                    item.quantity
                )
                validated_items.append((item, user, pharmacy, mask, item_total))
                total_amount += item_total
                if user_obj is None:
                    user_obj = user
            
            # 確保 user_obj 不為 None
            if user_obj is None:
                raise HTTPException(status_code=400, detail="無法取得用戶資訊")
            
            # 第二階段：檢查總餘額，如果不足則整筆取消
            user_balance = getattr(user_obj, 'cash_balance')
            if user_balance < total_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"用戶總餘額不足，現有餘額: {user_obj.cash_balance}，總需要: {total_amount}，整筆訂單已取消"
                )
            
            # 第三階段：執行所有交易
            for item, user, pharmacy, mask, item_total in validated_items:
                transaction = Transaction(
                    user_id=transaction_data.user_id,
                    pharmacy_id=item.pharmacy_id,
                    mask_id=item.mask_id,
                    quantity=item.quantity,
                    unit_price=mask.price,
                    total_amount=item_total,
                    transaction_datetime=datetime.now()
                )
                
                # 更新庫存和餘額
                setattr(mask, 'stock_quantity', getattr(mask, 'stock_quantity') - item.quantity)
                setattr(pharmacy, 'cash_balance', getattr(pharmacy, 'cash_balance') + item_total)
                
                self.db.add(transaction)
                transactions.append(transaction)
            
            # 更新用戶餘額（一次性扣除總金額）
            setattr(user_obj, 'cash_balance', getattr(user_obj, 'cash_balance') - total_amount)
            
            # 提交所有變更
            self.db.commit()
            
            # 刷新所有交易記錄
            for transaction in transactions:
                self.db.refresh(transaction)
            
            return MultiPharmacyTransactionResponse(
                user_id=transaction_data.user_id,
                total_amount=total_amount,
                total_items=len(transaction_data.items),
                transactions=[TransactionResponse.model_validate(t) for t in transactions],
                success_count=len(transactions),
                failed_items=[]
            )
        
        except HTTPException:
            # 驗證失敗，重新拋出錯誤
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"資料庫操作失敗: {str(e)}")