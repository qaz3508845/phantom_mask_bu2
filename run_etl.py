#!/usr/bin/env python3
"""
ETL 執行腳本
用於執行資料載入作業
"""

import sys
import os

# 將專案根目錄加入 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.etl import run_etl
from app.core.logging_config import setup_etl_logging

# 設定 ETL 專用日誌
logger = setup_etl_logging()

if __name__ == "__main__":
    logger.info("=== Phantom Mask ETL 資料載入工具 ===")
    logger.info("此工具將載入 pharmacies.json 和 users.json 資料到資料庫")
    
    # 檢查是否有自動模式參數
    auto_mode = len(sys.argv) > 1 and sys.argv[1] == '--auto'
    
    if auto_mode:
        logger.info("自動模式：將清空現有資料並重新載入")
        clear_data = True
    else:
        # 詢問是否清空現有資料
        response = input("是否要清空現有資料？(y/N): ").strip().lower()
        clear_data = response in ['y', 'yes', '是']
        
        if clear_data:
            logger.warning("將清空所有現有資料並重新載入")
        else:
            logger.info("將在現有資料基礎上載入新資料")
        
        confirm = input("確定要繼續嗎？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            logger.info("操作已取消")
            sys.exit(0)
    
    try:
        run_etl(clear_existing_data=clear_data)
        logger.info("ETL 執行成功！")
    except Exception as e:
        logger.error(f"ETL 執行失敗: {e}")
        sys.exit(1)