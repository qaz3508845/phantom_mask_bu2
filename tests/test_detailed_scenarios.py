"""
詳細場景測試
補充明確的成功和失敗場景，確保符合 README.md 要求
"""

import pytest
from decimal import Decimal


class TestDetailedScenarios:
    """詳細的成功和失敗場景測試"""

    # ========== 成功場景測試 ==========
    
    def test_mask_stock_update_success(self, client, db_session):
        """測試口罩庫存更新成功場景"""
        from app.models import Pharmacy, Mask
        
        # 建立測試資料
        pharmacy = Pharmacy(name="庫存測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="庫存測試口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 成功增加庫存
        update_data = {"quantity_change": 10}
        response = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["mask_id"] == mask.id
        assert data["new_quantity"] == 60

    def test_multi_pharmacy_transaction_success(self, client, db_session):
        """測試多藥局交易成功場景"""
        from app.models import User, Pharmacy, Mask
        
        # 建立有足夠餘額的用戶
        user = User(name="富有用戶", cash_balance=1000.00)
        db_session.add(user)
        db_session.flush()
        
        # 建立藥局和口罩
        pharmacy = Pharmacy(name="交易測試藥局", cash_balance=100.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="便宜口罩", price=5.00, stock_quantity=100, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 成功交易
        transaction_data = {
            "user_id": user.id,
            "items": [
                {
                    "pharmacy_id": pharmacy.id,
                    "mask_id": mask.id,
                    "quantity": 2
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert float(data["total_amount"]) == 10.00

    def test_batch_masks_create_success(self, client, db_session):
        """測試批量建立口罩成功場景"""
        from app.models import Pharmacy
        
        pharmacy = Pharmacy(name="批量測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.commit()

        masks_data = {
            "pharmacy_id": pharmacy.id,
            "masks": [
                {"name": "新口罩A", "price": 10.00, "stock_quantity": 50},
                {"name": "新口罩B", "price": 15.00, "stock_quantity": 30}
            ]
        }
        
        response = client.post("/api/v1/masks/batch", json=masks_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["pharmacy_id"] == pharmacy.id
        assert data["created_count"] == 2

    def test_top_spenders_success(self, client, db_session):
        """測試消費排行榜成功場景"""
        from app.models import User, Pharmacy, Mask, Transaction
        from datetime import datetime
        
        # 建立測試資料
        user1 = User(name="高消費用戶", cash_balance=1000.00)
        user2 = User(name="低消費用戶", cash_balance=1000.00)
        pharmacy = Pharmacy(name="排行榜測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user1, user2, pharmacy])
        db_session.flush()
        
        mask = Mask(name="排行榜測試口罩", price=100.00, stock_quantity=100, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.flush()
        
        # 建立不同金額的交易
        transaction1 = Transaction(
            user_id=user1.id, pharmacy_id=pharmacy.id, mask_id=mask.id,
            quantity=5, unit_price=100.00, total_amount=500.00,
            transaction_datetime=datetime(2024, 6, 15)
        )
        transaction2 = Transaction(
            user_id=user2.id, pharmacy_id=pharmacy.id, mask_id=mask.id,
            quantity=2, unit_price=100.00, total_amount=200.00,
            transaction_datetime=datetime(2024, 6, 16)
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        response = client.get("/api/v1/users/top-spenders?top_n=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert float(data[0]["total_spending"]) == 500.00  # 最高消費者在前
        assert float(data[1]["total_spending"]) == 200.00

    def test_list_masks_sorting(self, client, db_session):
        """測試需求2: 口罩列表排序功能"""
        from app.models import Pharmacy, Mask

        # 1. 建立測試資料
        pharmacy = Pharmacy(name="排序測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.commit()

        mask_c = Mask(name="C罩", price=20.0, stock_quantity=10, pharmacy_id=pharmacy.id)
        mask_a = Mask(name="A罩", price=30.0, stock_quantity=10, pharmacy_id=pharmacy.id)
        mask_b = Mask(name="B罩", price=10.0, stock_quantity=10, pharmacy_id=pharmacy.id)
        db_session.add_all([mask_a, mask_b, mask_c])
        db_session.commit()

        base_url = f"/api/v1/masks/?pharmacy_id={pharmacy.id}"

        # 2. 測試按名稱排序
        # 升序 (A, B, C)
        response_name_asc = client.get(f"{base_url}&sort_by=name&order=asc")
        assert response_name_asc.status_code == 200
        names_asc = [item['name'] for item in response_name_asc.json()]
        assert names_asc == ["A罩", "B罩", "C罩"]

        # 降序 (C, B, A)
        response_name_desc = client.get(f"{base_url}&sort_by=name&order=desc")
        assert response_name_desc.status_code == 200
        names_desc = [item['name'] for item in response_name_desc.json()]
        assert names_desc == ["C罩", "B罩", "A罩"]

        # 3. 測試按價格排序
        # 升序 (B:10, C:20, A:30)
        response_price_asc = client.get(f"{base_url}&sort_by=price&order=asc")
        assert response_price_asc.status_code == 200
        prices_asc = [item['name'] for item in response_price_asc.json()]
        assert prices_asc == ["B罩", "C罩", "A罩"]
        
        # 降序 (A:30, C:20, B:10)
        response_price_desc = client.get(f"{base_url}&sort_by=price&order=desc")
        assert response_price_desc.status_code == 200
        prices_desc = [item['name'] for item in response_price_desc.json()]
        assert prices_desc == ["A罩", "C罩", "B罩"]

    # ========== 失敗場景測試 ==========
    
    def test_mask_stock_update_not_found(self, client):
        """測試更新不存在口罩的庫存 - 失敗場景"""
        update_data = {"quantity_change": 10}
        response = client.patch("/api/v1/masks/99999/stock", json=update_data)
        
        assert response.status_code == 404

    def test_mask_stock_update_insufficient_stock(self, client, db_session):
        """測試庫存不足時減少庫存 - 失敗場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="低庫存測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="低庫存口罩", price=10.00, stock_quantity=5, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 嘗試減少超過現有庫存的數量
        update_data = {"quantity_change": -10}
        response = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_transaction_insufficient_balance(self, client, db_session):
        """測試用戶餘額不足的交易 - 失敗場景"""
        from app.models import User, Pharmacy, Mask
        
        # 建立餘額不足的用戶
        user = User(name="貧窮用戶", cash_balance=5.00)
        pharmacy = Pharmacy(name="昂貴藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.flush()
        
        mask = Mask(name="昂貴口罩", price=100.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        transaction_data = {
            "user_id": user.id,
            "items": [
                {
                    "pharmacy_id": pharmacy.id,
                    "mask_id": mask.id,
                    "quantity": 1
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "insufficient" in data["detail"].lower() or "餘額不足" in data["detail"]

    def test_transaction_insufficient_stock(self, client, db_session):
        """測試口罩庫存不足的交易 - 失敗場景"""
        from app.models import User, Pharmacy, Mask
        
        user = User(name="庫存測試用戶", cash_balance=1000.00)
        pharmacy = Pharmacy(name="低庫存藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.flush()
        
        mask = Mask(name="稀少口罩", price=10.00, stock_quantity=2, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        transaction_data = {
            "user_id": user.id,
            "items": [
                {
                    "pharmacy_id": pharmacy.id,
                    "mask_id": mask.id,
                    "quantity": 5  # 超過庫存
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "stock" in data["detail"].lower() or "庫存" in data["detail"]

    def test_transaction_user_not_found(self, client, sample_pharmacy, sample_mask):
        """測試用戶不存在的交易 - 失敗場景"""
        transaction_data = {
            "user_id": 99999,  # 不存在的用戶
            "items": [
                {
                    "pharmacy_id": sample_pharmacy.id,
                    "mask_id": sample_mask.id,
                    "quantity": 1
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        
        assert response.status_code == 404

    def test_batch_masks_pharmacy_not_found(self, client):
        """測試為不存在藥局批量建立口罩 - 失敗場景"""
        masks_data = {
            "pharmacy_id": 99999,  # 不存在的藥局
            "masks": [
                {"name": "測試口罩", "price": 10.00, "stock_quantity": 50}
            ]
        }
        
        response = client.post("/api/v1/masks/batch", json=masks_data)
        
        assert response.status_code == 404

    def test_batch_masks_invalid_data(self, client, sample_pharmacy):
        """測試批量建立口罩時提供無效資料 - 失敗場景"""
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {"name": "", "price": -10.00, "stock_quantity": -5}  # 無效資料
            ]
        }
        
        response = client.post("/api/v1/masks/batch", json=masks_data)
        
        assert response.status_code == 422  # Validation error

    def test_search_empty_query_validation(self, client):
        """測試空搜尋查詢的驗證 - 失敗場景"""
        # 測試藥局搜尋
        response = client.get("/api/v1/pharmacies/search?q=")
        assert response.status_code == 422
        
        # 測試口罩搜尋
        response = client.get("/api/v1/masks/search?q=")
        assert response.status_code == 422
        
        # 測試統一搜尋
        response = client.get("/api/v1/search/?q=")
        assert response.status_code == 422

    def test_invalid_api_endpoints(self, client):
        """測試無效的 API 端點 - 失敗場景"""
        # 測試不存在的端點
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # 測試錯誤的 HTTP 方法
        response = client.delete("/api/v1/pharmacies/")
        assert response.status_code == 405  # Method not allowed

    def test_invalid_query_parameters(self, client):
        """測試無效的查詢參數 - 失敗場景"""
        # 測試負數的 top_n
        response = client.get("/api/v1/users/top-spenders?top_n=-1")
        assert response.status_code == 422
        
        # 測試無效的日期格式
        response = client.get("/api/v1/users/top-spenders?start_date=invalid-date")
        assert response.status_code == 422