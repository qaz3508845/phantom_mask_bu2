"""
口罩相關 API 端點
實作需求2: 列出指定藥局的所有口罩，支援按名稱或價格排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from app.database.connection import get_db
from app.schemas.schemas import MaskResponse
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