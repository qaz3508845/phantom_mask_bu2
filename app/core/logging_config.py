"""
統一的日誌配置系統
提供結構化日誌和不同級別的日誌輸出
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from app.config import settings

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    設定應用程式的日誌系統
    
    Args:
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌檔案路徑，None 表示不寫入檔案
        enable_console: 是否輸出到控制台
    
    Returns:
        配置好的 logger 實例
    """
    
    # 建立根 logger
    logger = logging.getLogger("phantom_mask")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除現有的 handlers（避免重複設定）
    logger.handlers.clear()
    
    # 定義日誌格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 詳細格式（用於檔案）
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台輸出
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 檔案輸出
    if log_file:
        # 確保日誌目錄存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    取得指定模組的 logger
    
    Args:
        name: logger 名稱，通常使用 __name__
    
    Returns:
        logger 實例
    """
    return logging.getLogger(f"phantom_mask.{name}")

# 建立全域 logger 實例
def init_app_logging():
    """初始化應用程式日誌系統"""
    log_level = settings.log_level
    log_file = "logs/phantom_mask.log" if not settings.debug else None
    
    return setup_logging(
        level=log_level,
        log_file=log_file,
        enable_console=True
    )

# ETL 專用的 logger 設定
def setup_etl_logging() -> logging.Logger:
    """
    設定 ETL 專用的日誌配置
    ETL 需要更詳細的進度信息輸出
    """
    return setup_logging(
        level="INFO",
        log_file="logs/etl.log",
        enable_console=True
    )

# 為了向後相容，保留簡單的使用方式
default_logger = get_logger("main")