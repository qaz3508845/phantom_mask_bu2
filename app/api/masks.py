"""
口罩相關 API 端點
實作需求2: 列出指定藥局的所有口罩，支援按名稱或價格排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Literal
from datetime import datetime
from app.database.connection import get_db
from app.schemas.schemas import (
    MaskResponse, 
    StockUpdateRequest, 
    StockUpdateResponse,
    BatchMaskRequest,
    BatchMaskResponse
)
from app.models import Mask, Pharmacy

router = APIRouter()

@router.get("/", response_model=List[MaskResponse])
async def list_masks_by_pharmacy(
    pharmacy_id: int = Query(..., description="藥局ID"),
    sort_by: Optional[Literal["name", "price"]] = Query("name", description="排序方式 (name: 按名稱, price: 按價格)"),
    order: Optional[Literal["asc", "desc"]] = Query("asc", description="排序順序 (asc: 升序, desc: 降序)"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="取得筆數"),
    db: Session = Depends(get_db)
):
    """
    列出指定藥局銷售的所有口罩
    支援按名稱或價格排序
    
    需求2: List all masks sold by a given pharmacy with an option to sort by name or price
    
    使用範例：
    - ?pharmacy_id=1                           # 列出藥局1的所有口罩
    - ?pharmacy_id=1&sort_by=name&order=asc    # 按名稱升序排列
    - ?pharmacy_id=1&sort_by=price&order=desc  # 按價格降序排列
    - ?pharmacy_id=2&sort_by=name              # 按名稱排序 (預設升序)
    """
    
    # 驗證藥局是否存在
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail=f"藥局 ID {pharmacy_id} 不存在")
    
    # 查詢該藥局的所有口罩
    query = db.query(Mask).filter(Mask.pharmacy_id == pharmacy_id)
    
    # 根據排序條件排序
    if sort_by == "name":
        if order == "desc":
            query = query.order_by(Mask.name.desc())
        else:
            query = query.order_by(Mask.name.asc())
    elif sort_by == "price":
        if order == "desc":
            query = query.order_by(Mask.price.desc())
        else:
            query = query.order_by(Mask.price.asc())
    
    # 分頁
    masks = query.offset(skip).limit(limit).all()
    
    return masks

@router.patch("/{mask_id}/stock", response_model=StockUpdateResponse)
async def update_stock(
    mask_id: int,
    stock_update: StockUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新口罩產品的庫存數量 (需求6. Update the stock quantity of an existing mask product by increasing or decreasing it.)
    
    支援增加或減少庫存數量。
    quantity_change 為正數時增加庫存，為負數時減少庫存。
    
    使用範例：
    - quantity_change: 10   # 增加 10 個庫存
    - quantity_change: -5   # 減少 5 個庫存
    """
    try:
        # 查找口罩
        mask = db.query(Mask).filter(Mask.id == mask_id).first()
        if not mask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"口罩 ID {mask_id} 不存在"
            )
        
        # 記錄原庫存
        old_quantity = getattr(mask, 'stock_quantity')
        new_quantity = old_quantity + stock_update.quantity_change
        
        # 檢查庫存不能為負數
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"庫存不足，現有庫存: {old_quantity}，試圖減少: {abs(stock_update.quantity_change)}"
            )
        
        # 更新庫存
        setattr(mask, 'stock_quantity', new_quantity)
        setattr(mask, 'updated_at', datetime.now())
        
        db.commit()
        db.refresh(mask)
        
        return StockUpdateResponse(
            mask_id=getattr(mask, 'id'),
            mask_name=getattr(mask, 'name'),
            old_quantity=old_quantity,
            quantity_change=stock_update.quantity_change,
            new_quantity=new_quantity,
            updated_at=getattr(mask, 'updated_at'),
            reason=stock_update.reason
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"資料庫操作失敗: {str(e)}"
        )

@router.post("/batch", response_model=BatchMaskResponse, status_code=status.HTTP_201_CREATED)
async def batch_manage_masks(
    batch_request: BatchMaskRequest,
    db: Session = Depends(get_db)
):
    """
    批量建立或更新藥局的口罩產品 (需求7. Create or update multiple mask products for a pharmacy at once, including name, price, and stock quantity.)
    
    支援同時建立新的口罩產品或更新現有的產品。
    如果提供 mask_id 則更新現有產品，否則建立新產品。
    """
    try:
        # 驗證藥局是否存在
        pharmacy = db.query(Pharmacy).filter(Pharmacy.id == batch_request.pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"藥局 ID {batch_request.pharmacy_id} 不存在"
            )
        
        created_masks = []
        updated_masks = []
        failed_items = []
        
        for item in batch_request.masks:
            try:
                if item.mask_id:
                    # 更新現有口罩
                    mask = db.query(Mask).filter(
                        Mask.id == item.mask_id,
                        Mask.pharmacy_id == batch_request.pharmacy_id
                    ).first()
                    
                    if not mask:
                        failed_items.append(f"口罩 ID {item.mask_id} 不存在或不屬於指定藥局")
                        continue
                    
                    # 更新口罩資訊
                    setattr(mask, 'name', item.name)
                    setattr(mask, 'price', item.price)
                    setattr(mask, 'stock_quantity', item.stock_quantity)
                    setattr(mask, 'updated_at', datetime.now())
                    
                    updated_masks.append(mask)
                    
                else:
                    # 建立新口罩
                    mask = Mask(
                        name=item.name,
                        price=item.price,
                        stock_quantity=item.stock_quantity,
                        pharmacy_id=batch_request.pharmacy_id
                    )
                    db.add(mask)
                    created_masks.append(mask)
                    
            except Exception as e:
                failed_items.append(f"處理口罩 '{item.name}' 時發生錯誤: {str(e)}")
                continue
        
        # 提交所有變更
        db.commit()
        
        # 刷新所有建立的口罩
        for mask in created_masks:
            db.refresh(mask)
        
        return BatchMaskResponse(
            pharmacy_id=batch_request.pharmacy_id,
            pharmacy_name=getattr(pharmacy, 'name'),
            total_items=len(batch_request.masks),
            created_count=len(created_masks),
            updated_count=len(updated_masks),
            created_masks=[MaskResponse.model_validate(mask) for mask in created_masks],
            updated_masks=[MaskResponse.model_validate(mask) for mask in updated_masks],
            failed_items=failed_items
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"資料庫操作失敗: {str(e)}"
        )