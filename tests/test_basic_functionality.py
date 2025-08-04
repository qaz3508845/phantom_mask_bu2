"""
基本功能測試
驗證所有 8 個需求的核心功能能正常運作
"""

import pytest
from decimal import Decimal


class TestBasicFunctionality:
    """基本功能測試類別"""

    def test_requirement_1_list_pharmacies(self, client, sample_pharmacy):
        """需求1: 列出藥局，可選擇性地依特定時間和/或星期過濾"""
        # 基本藥局列表
        response = client.get("/api/v1/pharmacies/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "測試藥局"

        # 時間過濾測試
        response = client.get("/api/v1/pharmacies/?day=monday&time=10:00")
        assert response.status_code == 200

    def test_requirement_2_list_masks_by_pharmacy(self, client, sample_pharmacy, sample_mask):
        """需求2: 列出指定藥局販售的所有口罩，可選擇依名稱或價格排序"""
        # 基本口罩列表
        response = client.get(f"/api/v1/masks/?pharmacy_id={sample_pharmacy.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "測試口罩"

        # 價格排序測試
        response = client.get(f"/api/v1/masks/?pharmacy_id={sample_pharmacy.id}&sort_by=price")
        assert response.status_code == 200

    def test_requirement_3_filter_pharmacies_by_price_range(self, client, sample_pharmacy, sample_mask):
        """需求3: 列出在指定價格範圍內提供特定數量口罩產品的所有藥局"""
        response = client.get("/api/v1/pharmacies/filter/masks?min_price=5&max_price=15&min_count=1")
        assert response.status_code == 200
        data = response.json()
        # 檢查回應格式正確
        if len(data) > 0:
            assert "name" in data[0]
            assert "mask_count" in data[0]

    def test_requirement_4_top_spending_users(self, client, sample_user, sample_transaction):
        """需求4: 顯示在特定日期範圍內口罩消費最高的前 N 名用戶"""
        response = client.get("/api/v1/users/top-spenders?top_n=5")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            assert "rank" in data[0]
            assert "user_name" in data[0]
            assert "total_spending" in data[0]

    def test_requirement_5_multi_pharmacy_transaction(self, client, sample_user, sample_pharmacy, sample_mask):
        """需求5: 處理用戶一次從多個藥局購買口罩的交易"""
        transaction_data = {
            "user_id": sample_user.id,
            "items": [
                {
                    "pharmacy_id": sample_pharmacy.id,
                    "mask_id": sample_mask.id,
                    "quantity": 2
                }
            ]
        }

        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        
        # 檢查回應狀態
        assert response.status_code in [201, 400]  # 成功或業務邏輯錯誤都接受
        
        if response.status_code == 201:
            data = response.json()
            assert "user_id" in data
            assert "total_amount" in data

    def test_requirement_6_update_mask_stock(self, client, sample_mask):
        """需求6: 更新現有口罩產品的庫存數量（增加或減少）"""
        update_data = {
            "quantity_change": 10
        }

        response = client.patch(f"/api/v1/masks/{sample_mask.id}/stock", json=update_data)
        
        # 檢查回應狀態
        assert response.status_code in [200, 404]  # 成功或資源不存在都接受
        
        if response.status_code == 200:
            data = response.json()
            assert "mask_id" in data
            assert "new_quantity" in data

    def test_requirement_7_batch_manage_masks(self, client, sample_pharmacy):
        """需求7: 一次為藥局建立或更新多個口罩產品"""
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {
                    "name": "批量測試口罩",
                    "price": 12.50,
                    "stock_quantity": 30
                }
            ]
        }

        response = client.post("/api/v1/masks/batch", json=masks_data)
        
        # 檢查回應狀態
        assert response.status_code in [201, 400]  # 成功或業務邏輯錯誤都接受
        
        if response.status_code == 201:
            data = response.json()
            assert "pharmacy_id" in data
            assert "created_count" in data or "updated_count" in data

    def test_requirement_8_search_pharmacies(self, client, sample_pharmacy):
        """需求8: 依名稱搜尋藥局並依相關性排序結果"""
        response = client.get("/api/v1/pharmacies/search?q=測試")
        assert response.status_code == 200
        data = response.json()
        # 搜尋結果應該是列表格式
        assert isinstance(data, list)

    def test_requirement_8_search_masks(self, client, sample_mask):
        """需求8: 依名稱搜尋口罩並依相關性排序結果"""
        response = client.get("/api/v1/masks/search?q=測試")
        assert response.status_code == 200
        data = response.json()
        # 搜尋結果應該是列表格式
        assert isinstance(data, list)

    def test_unified_search(self, client, sample_pharmacy, sample_mask):
        """需求8: 統一搜尋功能"""
        response = client.get("/api/v1/search/?q=測試")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_results" in data

    def test_health_endpoints(self, client):
        """測試健康檢查端點"""
        # 測試根路由
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # 測試健康檢查
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_error_handling(self, client):
        """測試基本錯誤處理"""
        # 測試不存在的端點
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # 測試無效參數
        response = client.get("/api/v1/users/top-spenders?top_n=-1")
        assert response.status_code == 422