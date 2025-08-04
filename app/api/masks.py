"""
口罩相關 API 端點
實作需求2: 列出指定藥局的所有口罩，支援按名稱或價格排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import func, case, desc
from typing import List, Optional, Literal, cast
from datetime import datetime
from app.database.connection import get_db, supports_for_update
from app.schemas import (
    MaskResponse, 
    StockUpdateRequest, 
    StockUpdateResponse,
    BatchMaskRequest,
    BatchMaskResponse
)
from app.models import Mask, Pharmacy
from app.core.messages import ErrorMessages, pharmacy_not_found, mask_not_found, insufficient_stock, mask_batch_duplicate_names, mask_existing_names_in_pharmacy

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
        raise HTTPException(status_code=404, detail=pharmacy_not_found(pharmacy_id))
    
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

@router.get("/search", response_model=List[MaskResponse])
async def search_masks(
    q: str = Query(..., description="搜尋關鍵字"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="取得筆數"),
    db: Session = Depends(get_db)
):
    """
    按口罩名稱搜尋並按相關性排序
    
    需求8: Search for pharmacies or masks by name and rank the results by relevance to the search term
    
    使用範例：
    - ?q=True                        # 搜尋名稱包含「True」的口罩
    - ?q=Barrier                     # 搜尋名稱包含「Barrier」的口罩
    - ?q=green                       # 搜尋名稱包含「green」的口罩
    """
    # 按相關性排序：完全匹配 > 開頭匹配 > 包含匹配
    search_term = q.strip()
    if not search_term:
        raise HTTPException(status_code=422, detail=ErrorMessages.SEARCH_EMPTY_QUERY)
    
    # 使用 CASE WHEN 來實現相關性排序
    relevance = case(
        # 完全匹配（最高優先級）
        (func.lower(Mask.name) == func.lower(search_term), 3),
        # 開頭匹配
        (func.lower(Mask.name).startswith(func.lower(search_term)), 2),
        # 包含匹配
        (func.lower(Mask.name).contains(func.lower(search_term)), 1),
        else_=0
    ).label('relevance')
    
    query = (
        db.query(Mask, relevance)
        .filter(Mask.name.ilike(f"%{search_term}%"))
        .order_by(desc('relevance'), Mask.name.asc(), Mask.price.asc())
        .offset(skip)
        .limit(limit)
    )
    
    results = query.all()
    masks = [mask for mask, relevance in results]
    
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
    # 查找口罩 (使用 SELECT FOR UPDATE 防止併發修改)
    if supports_for_update(db):
        mask = cast(Mask, db.query(Mask).filter(Mask.id == mask_id).with_for_update().first())
    else:
        mask = cast(Mask, db.query(Mask).filter(Mask.id == mask_id).first())
    if not mask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=mask_not_found(mask_id)
        )
    
    # 記錄原庫存 (此時已鎖定，資料一致)
    old_quantity = cast(int, mask.stock_quantity)
    new_quantity = old_quantity + stock_update.quantity_change
    
    # 檢查庫存不能為負數
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=insufficient_stock(old_quantity, abs(stock_update.quantity_change))
        )
    
    try:
        # 更新庫存
        setattr(mask, 'stock_quantity', new_quantity)
        setattr(mask, 'updated_at', datetime.now())
        
        db.commit()
        db.refresh(mask)
        
        return StockUpdateResponse(
            mask_id=cast(int, mask.id),
            mask_name=cast(str, mask.name),
            old_quantity=old_quantity,
            quantity_change=stock_update.quantity_change,
            new_quantity=new_quantity,
            updated_at=cast(datetime, mask.updated_at),
            reason=stock_update.reason
        )
        
    except OperationalError as e:
        db.rollback()
        # 檢查是否為死鎖錯誤
        if "deadlock" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="庫存更新發生衝突，請稍後重試"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"資料庫操作失敗: {str(e)}"
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
    # 驗證藥局是否存在
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == batch_request.pharmacy_id).first()
    if not pharmacy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"藥局 ID {batch_request.pharmacy_id} 不存在"
        )
    
    
    # 找出所有要建立的新口罩名稱
    names_to_create_list = [item.name for item in batch_request.masks if not item.mask_id]
    
    # 檢查請求內部是否有重複的名稱
    if len(names_to_create_list) != len(set(names_to_create_list)):
        seen = set()
        duplicates = {x for x in names_to_create_list if x in seen or seen.add(x)}
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=mask_batch_duplicate_names(', '.join(duplicates))
        )
    
    names_to_create_set = set(names_to_create_list)
    if names_to_create_set:
        # 檢查這些名稱是否已存在於該藥局
        existing_masks = db.query(Mask.name).filter(
            Mask.pharmacy_id == batch_request.pharmacy_id,
            Mask.name.in_(names_to_create_set)
        ).all()
        
        # 如果有任何一個名稱已存在，就回絕請求
        if existing_masks:
            duplicate_names = {name for name, in existing_masks}
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=mask_existing_names_in_pharmacy(pharmacy.name, ', '.join(duplicate_names))
            )
            

    try:
        created_masks = []
        updated_masks = []
        failed_items = []
        
        for item in batch_request.masks:
            try:
                if item.mask_id:
                    # 更新現有口罩 (使用 SELECT FOR UPDATE 防止併發修改)
                    if supports_for_update(db):
                        mask = db.query(Mask).filter(
                            Mask.id == item.mask_id,
                            Mask.pharmacy_id == batch_request.pharmacy_id
                        ).with_for_update().first()
                    else:
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
                    # 建立新口罩 (此時已知名稱不重複)
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
        
    except OperationalError as e:
        db.rollback()
        # 檢查是否為死鎖錯誤
        if "deadlock" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="批量操作發生衝突，請稍後重試"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"資料庫操作失敗: {str(e)}"
            )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"資料庫操作失敗: {str(e)}"
        )