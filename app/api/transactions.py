"""
交易管理 API 路由
提供單筆交易和多藥局交易功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.services.transaction_service import TransactionService
from app.schemas.schemas import (
    TransactionCreate,
    TransactionResponse, 
    MultiPharmacyTransactionCreate,
    MultiPharmacyTransactionResponse
)
from app.models import Transaction

router = APIRouter()

@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    建立單筆交易 (輔助功能)
    
    建立用戶從單一藥局購買口罩的交易記錄，
    並自動更新庫存和餘額。
    
    註: 此為開發便利性功能，核心需求為多藥局交易。
    """
    service = TransactionService(db)
    return service.create_single_transaction(transaction_data)

@router.post("/transactions/multi-pharmacy", response_model=MultiPharmacyTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_multi_pharmacy_transaction(
    transaction_data: MultiPharmacyTransactionCreate,
    db: Session = Depends(get_db)
):
    """
    建立多藥局交易 (需求5.Process a purchase where a user buys masks from multiple pharmacies at once.)
    
    處理用戶同時從多個藥局購買口罩的交易，
    支援部分成功的交易結果回應。
    """
    service = TransactionService(db)
    return service.create_multi_pharmacy_transaction(transaction_data)

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: Optional[int] = None,
    pharmacy_id: Optional[int] = None,
    mask_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    查詢交易記錄 (管理功能)
    
    支援按用戶、藥局或口罩篩選交易記錄。
    
    註: 此為系統管理和除錯用途，非核心業務需求。
    """
    query = db.query(Transaction)
    
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if pharmacy_id:
        query = query.filter(Transaction.pharmacy_id == pharmacy_id)
    if mask_id:
        query = query.filter(Transaction.mask_id == mask_id)
    
    transactions = query.order_by(Transaction.transaction_datetime.desc()).offset(offset).limit(limit).all()
    
    return [TransactionResponse.model_validate(t) for t in transactions]

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    查詢單筆交易詳情 (管理功能)
    
    註: 此為系統管理和除錯用途，非核心業務需求。
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"交易 ID {transaction_id} 不存在"
        )
    
    return TransactionResponse.model_validate(transaction)