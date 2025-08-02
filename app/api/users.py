"""
用戶 API 端點
實作需求4: 顯示在特定日期範圍內口罩消費最多的前N名用戶
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.schemas import UserRankingResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["用戶統計"])

@router.get("/top-spenders", response_model=List[UserRankingResponse])
async def get_top_spending_users(
    top_n: int = Query(10, ge=1, le=100, description="返回前N名用戶"),
    start_date: Optional[date] = Query(None, description="開始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="結束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    需求4: Show the top N users who spent the most on masks during a specific date range
    
    顯示在特定日期範圍內口罩消費最多的前N名用戶
    
    使用範例：
    - ?top_n=5                                    # 前5名消費用戶 (所有時間)
    - ?top_n=10&start_date=2024-01-01             # 2024年1月1日起前10名
    - ?top_n=3&start_date=2024-01-01&end_date=2024-12-31  # 2024年前3名
    """
    try:
        # 建立基本查詢
        query = db.query(
            User.id,
            User.name,
            User.cash_balance,
            func.sum(Transaction.total_amount).label('total_spending'),
            func.count(Transaction.id).label('total_transactions'),
            func.sum(Transaction.quantity).label('total_quantity')
        ).join(Transaction, User.id == Transaction.user_id)
        
        # 日期範圍過濾
        if start_date:
            query = query.filter(Transaction.transaction_datetime >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Transaction.transaction_datetime <= end_datetime)
        
        # 按用戶分組，按消費金額降序排列
        results = query.group_by(User.id, User.name, User.cash_balance)\
                      .order_by(desc('total_spending'))\
                      .limit(top_n).all()
        
        # 組織回應資料
        rankings = []
        for rank, result in enumerate(results, 1):
            rankings.append({
                "rank": rank,
                "user_id": result.id,
                "user_name": result.name,
                "cash_balance": result.cash_balance,
                "total_spending": float(result.total_spending or 0),
                "total_quantity": result.total_quantity or 0,
                "total_transactions": result.total_transactions or 0,
                "ranking_type": "spending",
                "start_date": start_date,
                "end_date": end_date
            })
        
        logger.info(f"Generated top {top_n} spending users ranking for {len(rankings)} users")
        return rankings
    except Exception as e:
        logger.error(f"Error generating top spending users: {e}")
        raise HTTPException(status_code=500, detail="獲取消費排行榜失敗")