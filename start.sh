#!/bin/bash

echo "開始啟動 Phantom Mask API..."

# 初始化資料庫
echo "初始化資料庫..."
python init_db.py

# 檢查初始化是否成功
if [ $? -eq 0 ]; then
    echo "資料庫初始化成功，啟動 API 服務..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "資料庫初始化失敗，退出..."
    exit 1
fi