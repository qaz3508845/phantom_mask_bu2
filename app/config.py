"""
應用程式設定檔
管理環境變數和應用程式配置
"""

import os
from typing import Optional

class Settings:
    """應用程式設定類別 - 從環境變數讀取"""
    
    def __init__(self):
        # 資料庫設定 - 從環境變數讀取
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db: str = os.getenv("POSTGRES_DB", "phantom_mask")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        # API 設定
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        
        # 日誌設定
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

# 建立全域設定實例
settings = Settings()