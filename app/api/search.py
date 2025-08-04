"""
統一搜尋 API 端點
實作需求8: 統一搜尋藥局和口罩，按相關性排序
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.schemas import UnifiedSearchResponse, SearchResultItem
from app.models import Pharmacy, Mask

router = APIRouter()

def _calculate_relevance(name_column, search_term: str):
    """計算相關性分數的 SQL 表達式"""
    return case(
        # 完全匹配（最高優先級）
        (func.lower(name_column) == func.lower(search_term), 3),
        # 開頭匹配
        (func.lower(name_column).startswith(func.lower(search_term)), 2),
        # 包含匹配
        (func.lower(name_column).contains(func.lower(search_term)), 1),
        else_=0
    )

@router.get("/", response_model=UnifiedSearchResponse)
async def unified_search(
    q: str = Query(..., description="搜尋關鍵字"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="取得筆數"),
    db: Session = Depends(get_db)
):
    """
    統一搜尋藥局和口罩
    
    需求8: Search for pharmacies or masks by name and rank the results by relevance to the search term
    
    同時搜尋藥局和口罩，按相關性排序並合併結果。
    相關性排序：完全匹配 > 開頭匹配 > 包含匹配
    
    使用範例：
    - ?q=大樹                      # 搜尋名稱包含「大樹」的藥局和口罩
    - ?q=N95                       # 搜尋名稱包含「N95」的藥局和口罩
    - ?q=健康                      # 搜尋名稱包含「健康」的藥局和口罩
    - ?q=test&skip=10&limit=20     # 分頁搜尋
    """
    search_term = q.strip()
    if not search_term:
        raise HTTPException(status_code=422, detail="搜尋關鍵字不能為空")
    
    # 搜尋藥局
    pharmacy_relevance = _calculate_relevance(Pharmacy.name, search_term).label('relevance')
    pharmacy_query = (
        db.query(Pharmacy, pharmacy_relevance)
        .filter(Pharmacy.name.ilike(f"%{search_term}%"))
        .order_by(desc('relevance'), Pharmacy.name.asc())
    )
    
    # 搜尋口罩
    mask_relevance = _calculate_relevance(Mask.name, search_term).label('relevance')
    mask_query = (
        db.query(Mask, mask_relevance)
        .filter(Mask.name.ilike(f"%{search_term}%"))
        .order_by(desc('relevance'), Mask.name.asc(), Mask.price.asc())
    )
    
    # 執行查詢（暫時不分頁，後面會整體排序後分頁）
    pharmacy_results = pharmacy_query.all()
    mask_results = mask_query.all()
    
    # 轉換為統一格式
    all_results = []
    
    # 處理藥局結果
    for pharmacy, relevance in pharmacy_results:
        result_item = SearchResultItem(
            id=pharmacy.id,
            name=pharmacy.name,
            type="pharmacy",
            relevance_score=relevance,
            cash_balance=pharmacy.cash_balance,
            opening_hours=pharmacy.opening_hours,
            price=None,
            stock_quantity=None,
            pharmacy_id=None,
            created_at=pharmacy.created_at,
            updated_at=pharmacy.updated_at
        )
        all_results.append(result_item)
    
    # 處理口罩結果
    for mask, relevance in mask_results:
        result_item = SearchResultItem(
            id=mask.id,
            name=mask.name,
            type="mask",
            relevance_score=relevance,
            cash_balance=None,
            opening_hours=None,
            price=mask.price,
            stock_quantity=mask.stock_quantity,
            pharmacy_id=mask.pharmacy_id,
            created_at=mask.created_at,
            updated_at=mask.updated_at
        )
        all_results.append(result_item)
    
    # 按相關性排序，然後按名稱排序
    all_results.sort(key=lambda x: (-x.relevance_score, x.name.lower()))
    
    # 統計
    total_results = len(all_results)
    pharmacy_count = len(pharmacy_results)
    mask_count = len(mask_results)
    
    # 分頁
    paginated_results = all_results[skip:skip + limit]
    
    return UnifiedSearchResponse(
        query=search_term,
        total_results=total_results,
        pharmacy_count=pharmacy_count,
        mask_count=mask_count,
        results=paginated_results,
        pagination={
            "skip": skip,
            "limit": limit,
            "total": total_results,
            "has_more": skip + limit < total_results
        }
    )