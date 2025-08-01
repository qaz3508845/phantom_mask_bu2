"""
Phantom Mask API 主應用程式
FastAPI 應用程式的進入點
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import engine, Base
from app.models import Pharmacy, Mask, User, Transaction
from app.api import pharmacies

# 建立資料庫表
Base.metadata.create_all(bind=engine)

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="Phantom Mask API",
    description="藥局口罩平台後端 API 服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中間件設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊 API 路由
app.include_router(pharmacies.router, prefix="/api/v1/pharmacies", tags=["藥局"])

@app.get("/")
async def root():
    """根路由 - API 健康檢查"""
    return {
        "message": "Phantom Mask API 服務正常運行",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": "development" if settings.debug else "production"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "phantom_mask_api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)