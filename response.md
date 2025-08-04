# Phantom Mask 後端 API 系統

本專案使用 FastAPI 和 PostgreSQL 實作完整的藥局與口罩管理系統。

## 系統架構

### 技術棧
- **後端框架**: FastAPI 0.104.1
- **資料庫**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.x
- **部署**: Docker + Docker Compose
- **測試**: pytest + pytest-cov

### 安全性設計
- **資料驗證**: Pydantic 模型驗證
- **SQL 注入防護**: SQLAlchemy ORM 參數化查詢
- **併發控制**: PostgreSQL 悲觀鎖
- **錯誤處理**: 統一 HTTP 狀態碼
- **CORS 設定**: 開發環境開放

## 需求完成狀態

所有 8 個功能需求已完成實作與測試

* [x] **需求 1**: List pharmacies, optionally filtered by specific time and/or day of the week.
  * 實作於 `GET /api/v1/pharmacies/` API，支援營業時間和星期的查詢參數過濾
* [x] **需求 2**: List all masks sold by a given pharmacy with an option to sort by name or price.
  * 實作於 `GET /api/v1/masks/?pharmacy_id={id}` API，支援排序參數
* [x] **需求 3**: List all pharmacies that offer a number of mask products within a given price range, where the count is above, below, or between given thresholds.
  * 實作於 `GET /api/v1/pharmacies/filter/masks` API，支援價格範圍和數量門檻參數  
* [x] **需求 4**: Show the top N users who spent the most on masks during a specific date range.
  * 實作於 `GET /api/v1/users/top-spenders` API，支援限制數量和日期範圍參數
* [x] **需求 5**: Process a purchase where a user buys masks from multiple pharmacies at once.
  * 實作於 `POST /api/v1/transactions/multi-pharmacy` API，支援多藥局交易處理
* [x] **需求 6**: Update the stock quantity of an existing mask product by increasing or decreasing it.
  * 實作於 `PATCH /api/v1/masks/{mask_id}/stock` API，支援庫存調整功能
* [x] **需求 7**: Create or update multiple mask products for a pharmacy at once, including name, price, and stock quantity.
  * 實作於 `POST /api/v1/masks/batch` API，支援批量操作
* [x] **需求 8**: Search for pharmacies or masks by name and rank the results by relevance to the search term.
  * 實作於 `GET /api/v1/pharmacies/search`、`GET /api/v1/masks/search` 和 `GET /api/v1/search/` API，支援相關性排序

## 快速開始

### 新環境部署指南

如果你是第一次部署這個系統，請按照以下步驟操作：

#### 前置需求
- Docker Desktop 或 Docker + Docker Compose
- Git（用於克隆專案）

#### 步驟 1: 獲取專案 
```bash
# 克隆專案（如果還沒有的話）
git clone <repository-url>
cd phantom_mask_bu2
```

#### 步驟 2: 環境配置
```bash
# 複製環境變數範例檔案（必要步驟）
# Linux/macOS:
cp .env.example .env

# Windows:
copy .env.example .env

# 預設配置已可直接使用，如需自訂請編輯 .env 檔案
# 包含資料庫連線、API 端口等設定
```

#### 步驟 3: 啟動完整系統
```bash
# 一鍵啟動：PostgreSQL + API 服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps

# 查看啟動日誌
docker-compose logs -f
```

#### 步驟 4: 載入測試資料
```bash
# 載入完整測試資料集
docker exec phantom_mask_api python run_etl.py --auto
```

#### 步驟 5: 驗證部署
```bash
# 健康檢查
curl http://localhost:8000/health

# 查看 API 文件
# 瀏覽器開啟: http://localhost:8000/docs
```

#### 步驟 6: 執行測試套件
```bash
# 進入容器執行測試
docker exec phantom_mask_api pytest

# 執行完整測試與覆蓋率報告
docker exec phantom_mask_api pytest --cov=app --cov-report=html --cov-report=term-missing

# 複製覆蓋率報告到本地
docker cp phantom_mask_api:/app/htmlcov ./htmlcov

# 查看測試覆蓋率報告
# Windows: start htmlcov/index.html
# macOS: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```


### 不使用 Docker 部署

#### 環境需求
- Python 3.11+
- PostgreSQL 14+
- pip 套件管理器

#### 建置步驟

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 設定環境變數
# 複製範例檔案並根據需要修改
# Linux/macOS: cp .env.example .env
# Windows: copy .env.example .env
# 或手動編輯 .env 檔案包含以下設定：
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=phantom_mask
# POSTGRES_USER=postgres  
# POSTGRES_PASSWORD=postgres
# API_HOST=0.0.0.0
# API_PORT=8000
# DEBUG=true
# LOG_LEVEL=DEBUG

# 3. 啟動伺服器（資料庫表格會自動建立）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 載入測試資料
python run_etl.py
```

### 服務位置

部署完成後，服務將在以下位置提供：
- **API 服務**: `http://localhost:8000`
- **互動式 API 文件 (Swagger)**: `http://localhost:8000/docs`
- **API 文件 (ReDoc)**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`


## API 文件

API 使用 OpenAPI 3.0 規範，可透過以下互動式文件介面存取：
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`  
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### 主要 API 端點

#### 藥局相關
- `GET /api/v1/pharmacies/` - 列出藥局，可選擇時間/星期過濾
- `GET /api/v1/masks/?pharmacy_id={id}` - 列出特定藥局的口罩
- `GET /api/v1/pharmacies/filter/masks` - 依口罩價格範圍和數量尋找藥局

#### 用戶與交易
- `GET /api/v1/users/top-spenders` - 取得日期範圍內消費最高的用戶
- `POST /api/v1/transactions/multi-pharmacy` - 處理多藥局購買交易

#### 口罩管理
- `PATCH /api/v1/masks/{mask_id}/stock` - 更新口罩庫存數量
- `POST /api/v1/masks/batch` - 批量建立/更新口罩

#### 搜尋功能
- `GET /api/v1/pharmacies/search` - 依名稱搜尋藥局並按相關性排序
- `GET /api/v1/masks/search` - 依名稱搜尋口罩並按相關性排序
- `GET /api/v1/search/` - 統一搜尋藥局和口罩


## 測試覆蓋率報告

實作測試套件，涵蓋 8 個功能需求的主要成功和失敗場景：

### 測試覆蓋範圍
- **需求1**: 藥局列表與時間過濾
- **需求2**: 藥局口罩列表與排序
- **需求3**: 價格範圍與數量門檻查詢
- **需求4**: 用戶消費排行榜
- **需求5**: 多藥局交易處理
- **需求6**: 口罩庫存更新
- **需求7**: 批量口罩管理
- **需求8**: 搜尋功能與相關性排序

### 測試執行指令

#### Docker 環境
```bash
# 執行所有測試
docker exec phantom_mask_api pytest

# 執行測試並產生覆蓋率報告
docker exec phantom_mask_api pytest --cov=app --cov-report=html --cov-report=term-missing

# 複製覆蓋率報告到本地
docker cp phantom_mask_api:/app/htmlcov ./htmlcov
```

#### 本地環境
```bash
# 執行所有測試
pytest

# 執行測試並產生覆蓋率報告
pytest --cov=app --cov-report=html --cov-report=term-missing

# 查看 HTML 覆蓋率報告
# macOS: open htmlcov/index.html
# Windows: start htmlcov/index.html  
# Linux: xdg-open htmlcov/index.html
```

### 測試結果

- **測試數量**: 77 個測試
- **覆蓋率**: 83% (783 行程式碼中的 653 行)
- **測試狀態**: 全部通過
- **執行時間**: ~8 秒

### 詳細覆蓋率分析

| 模組 | 覆蓋率 | 說明 |
|------|--------|------|
| API 端點 | 55-100% | 8 個需求的端點已測試 |
| 業務邏輯 | 77-97% | 核心業務流程測試 |
| 資料模型 | 95-100% | 資料庫模型測試 |
| 搜尋功能 | 100% | 搜尋和排序邏輯測試 |
| 基礎設施 | 70-100% | 配置和連線管理 |

### 測試類型分布
- **基礎功能測試**: 12 個 - 核心功能驗證
- **綜合場景測試**: 16 個 - 複雜業務場景
- **詳細場景測試**: 21 個 - 成功/失敗場景
- **邊界條件測試**: 9 個 - 極端值與特殊情況
- **搜尋功能測試**: 14 個 - 搜尋與排序邏輯
- **併發控制測試**: 5 個 - 多線程環境下的業務邏輯驗證

測試涵蓋成功場景、錯誤處理、邊界條件。註：併發控制測試使用 SQLite，實際併發安全需在 PostgreSQL 環境驗證。

### 完整測試報告

詳細的測試實施與結果分析請參考：[TEST_REPORT.md](TEST_REPORT.md)


## 品質保證與達成標準

### 專案達成度

| 評審標準 | 狀態 | 說明 |
|----------|------|------|
| **功能需求** | 8/8 完成 | 所有需求已實作並測試 |
| **5xx 錯誤** | 無 | 測試中未發現 5xx 錯誤 |
| **測試覆蓋** | 83% | 程式碼測試覆蓋率（77個測試） |
| **部署能力** | Docker 支援 | 提供容器化部署 |
| **API 文件** | OpenAPI 3.0 | 互動式文檔 |
| **錯誤處理** | HTTP 標準 | 使用標準 HTTP 狀態碼 |



## 額外資料

### 資料庫結構

#### 主要資料表設計

**pharmacies (藥局資料表)**
- `id` (Serial): 主鍵
- `name` (VARCHAR 255): 藥局名稱 (索引)
- `cash_balance` (DECIMAL 10,2): 現金餘額
- `opening_hours` (TEXT): 營業時間 (JSON 格式)
- `created_at`, `updated_at` (TIMESTAMP): 時間戳記

**masks (口罩產品資料表)**
- `id` (Serial): 主鍵  
- `name` (VARCHAR 255): 產品名稱 (索引)
- `price` (DECIMAL 10,2): 價格
- `stock_quantity` (INTEGER): 庫存數量
- `pharmacy_id` (INTEGER): 外鍵關聯到 pharmacies
- `created_at`, `updated_at` (TIMESTAMP): 時間戳記

**users (用戶資料表)**
- `id` (Serial): 主鍵
- `name` (VARCHAR 255): 用戶名稱 (索引)
- `cash_balance` (DECIMAL 10,2): 現金餘額
- `created_at`, `updated_at` (TIMESTAMP): 時間戳記

**transactions (交易記錄資料表)**
- `id` (Serial): 主鍵
- `user_id` (INTEGER): 外鍵關聯到 users (索引)
- `pharmacy_id` (INTEGER): 外鍵關聯到 pharmacies (索引)
- `mask_id` (INTEGER): 外鍵關聯到 masks (索引)
- `quantity` (INTEGER): 購買數量
- `unit_price`, `total_amount` (DECIMAL 10,2): 單價和總額
- `transaction_datetime` (TIMESTAMP): 交易時間 (索引)
- `created_at`, `updated_at` (TIMESTAMP): 時間戳記

#### 關聯設計
- 一對多: Pharmacy → Masks
- 多對多: Users ↔ Pharmacies (透過 Transactions)
- 交易記錄保存完整的快照資料，支援歷史查詢

## 故障排除

### 常見問題

#### 0. 環境變數檔案不存在
```bash
# 錯誤訊息: "env file .env not found"
# 解決方法: 複製範例檔案

# Linux/macOS:
cp .env.example .env

# Windows:
copy .env.example .env

# 然後重新啟動
docker-compose up -d
```

#### 1. 容器啟動失敗
```bash
# 檢查容器狀態
docker-compose ps

# 查看錯誤日誌
docker-compose logs

# 重新構建
docker-compose down && docker-compose up --build -d
```

#### 2. 資料庫連線問題
```bash
# 檢查 PostgreSQL 狀態
docker logs phantom_mask_postgres

# 檢查資料庫連通性
docker exec phantom_mask_postgres pg_isready -U postgres -d phantom_mask

# 檢查資料庫表
docker exec phantom_mask_postgres psql -U postgres -d phantom_mask -c "\dt"
```

#### 3. API 服務無回應
```bash
# 檢查 API 容器日誌
docker logs phantom_mask_api

# 重啟 API 服務
docker-compose restart api

# 檢查端口占用
netstat -an | findstr :8000  # Windows
lsof -i :8000                # macOS/Linux
```

#### 4. 測試資料載入失敗
```bash
# 檢查 ETL 執行狀況
docker exec phantom_mask_api python run_etl.py --debug

# 檢查資料是否載入
docker exec phantom_mask_api python -c "
from app.database.connection import SessionLocal
from app.models import Pharmacy
db = SessionLocal()
print(f'藥局數量: {db.query(Pharmacy).count()}')
db.close()
"
```

### 清理與重置
```bash
# 完全清理（刪除所有資料）
docker-compose down -v

# 刪除資料庫檔案
# Linux/macOS:
rm -rf db_data/
# Windows:
rmdir /s /q db_data

docker-compose up -d

# 只重啟服務（保留資料）
docker-compose restart
```

## 資料持久化

### 資料庫檔案位置
- **本地路徑**: `./db_data/`
- **包含內容**: 完整的 PostgreSQL 資料檔案
- **版本控制**: 已加入 `.gitignore`，不會同步到 Git

### 備份與還原
```bash
# 備份資料庫
docker exec phantom_mask_postgres pg_dump -U postgres phantom_mask > backup.sql

# 還原資料庫
docker exec -i phantom_mask_postgres psql -U postgres phantom_mask < backup.sql

# 備份整個資料庫目錄
# Linux/macOS:
tar -czf db_backup.tar.gz db_data/
# Windows (PowerShell):
Compress-Archive -Path db_data -DestinationPath db_backup.zip
```

## 專案總結

系統實作 8 個功能需求，使用 FastAPI + PostgreSQL 架構。測試覆蓋率 83%，共 77 個測試案例。
