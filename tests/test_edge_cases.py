"""
邊界條件和錯誤處理測試
提高測試覆蓋率
"""

import pytest
from decimal import Decimal


class TestEdgeCases:
    """邊界條件測試類別"""

    def test_transaction_service_error_handling(self, client, db_session):
        """測試交易服務錯誤處理 - 餘額不足"""
        from app.models import User, Pharmacy, Mask
        
        # 建立測試數據
        user = User(name="低餘額用戶", cash_balance=5.00)
        pharmacy = Pharmacy(name="測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.flush()
        
        mask = Mask(name="昂貴口罩", price=100.00, stock_quantity=1, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 測試餘額不足
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
        # 餘額不足，應返回 400 Bad Request
        assert response.status_code == 400

    def test_mask_stock_boundary_conditions(self, client, db_session, sample_pharmacy):
        """測試口罩庫存邊界條件"""
        from app.models import Mask
        
        mask = Mask(name="庫存邊界測試口罩", price=10.0, stock_quantity=10, pharmacy_id=sample_pharmacy.id)
        db_session.add(mask)
        db_session.commit()
        
        # 測試減少到零庫存
        update_data = {
            "quantity_change": -10
        }
        response = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        assert response.status_code == 200
        assert response.json()["new_quantity"] == 0
        
        # 測試負數庫存變更（超出庫存）
        update_data = {
            "quantity_change": -1 # 目前庫存為 0，再減 1
        }
        response = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        assert response.status_code == 400

    def test_pharmacy_complex_filtering(self, client, db_session):
        """測試藥局複雜過濾條件"""
        from app.models import Pharmacy, Mask
        
        # 建立複雜的測試數據
        pharmacy = Pharmacy(
            name="複雜測試藥局",
            cash_balance=1000.00,
            opening_hours='{"monday": {"open": "08:00", "close": "18:00"}, "tuesday": {"open": "10:00", "close": "20:00"}}'
        )
        db_session.add(pharmacy)
        db_session.flush()
        
        # 建立不同價格範圍的口罩
        masks = [
            Mask(name=f"口罩{i}", price=i*10.0, stock_quantity=i*5, pharmacy_id=pharmacy.id)
            for i in range(1, 6)
        ]
        for mask in masks:
            db_session.add(mask)
        db_session.commit()

        # 測試複雜的價格範圍查詢
        test_cases = [
            "?min_price=10&max_price=30&min_count=3", # 應找到
            "?max_price=50&min_count=1", # 應找到
            "?min_count=100", # 應找不到
            "?min_price=5&max_price=100&min_count=1&max_count=5" # 應找到
        ]
        
        for params in test_cases:
            response = client.get(f"/api/v1/pharmacies/filter/masks{params}")
            assert response.status_code == 200

    def test_search_edge_cases(self, client, db_session):
        """測試搜尋邊界條件"""
        from app.models import Pharmacy, Mask
        
        # 建立測試數據
        pharmacy = Pharmacy(name="特殊字符#$%藥局", cash_balance=100.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="特殊@字符口罩", price=10.00, stock_quantity=10, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 測試特殊字符搜尋
        special_queries = ["#", "$", "%", "@", "特殊", "字符"]
        
        for query in ["特殊", "字符"]:
            # 藥局搜尋
            response = client.get(f"/api/v1/pharmacies/search?q={query}")
            assert response.status_code == 200 # 假設 URL 編碼後可正常搜尋
            
            # 口罩搜尋
            response = client.get(f"/api/v1/masks/search?q={query}")
            assert response.status_code == 200 # 假設 URL 編碼後可正常搜尋
            
            # 統一搜尋
            response = client.get(f"/api/v1/search/?q={query}")
            assert response.status_code == 200 # 假設 URL 編碼後可正常搜尋

        # 測試特殊字符搜尋
        # '#' 字符在URL中有特殊意義，會被FastAPI處理為422
        response = client.get("/api/v1/pharmacies/search?q=#")
        assert response.status_code == 422  # '#' 字符會導致URL解析問題
        
        response = client.get("/api/v1/masks/search?q=#")
        assert response.status_code == 422
        
        response = client.get("/api/v1/search/?q=#")
        assert response.status_code == 422
        
        # 其他特殊字符能正常處理
        for query in ["$", "%", "@"]:
            # 藥局搜尋
            response = client.get(f"/api/v1/pharmacies/search?q={query}")
            assert response.status_code == 200  # 這些字符API能正常處理
            
            # 口罩搜尋
            response = client.get(f"/api/v1/masks/search?q={query}")
            assert response.status_code == 200
            
            # 統一搜尋
            response = client.get(f"/api/v1/search/?q={query}")
            assert response.status_code == 200

    def test_batch_mask_error_scenarios(self, client, sample_pharmacy):
        """測試批量口罩操作錯誤場景"""
        # 測試在同一個請求中包含重複名稱，應引發衝突錯誤
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {
                    "name": "內部重複口罩",
                    "price": 10.00,
                    "stock_quantity": 20
                },
                {
                    "name": "內部重複口罩",
                    "price": 15.00,
                    "stock_quantity": 30
                }
            ]
        }
        response = client.post("/api/v1/masks/batch", json=masks_data)
        assert response.status_code == 409  # 應回報名稱衝突
        assert "內部重複口罩" in response.json()["detail"]

        # 測試極端價格 (在 Decimal/Float 範圍內，應為有效)
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {
                    "name": "極端價格口罩",
                    "price": 999999.99,
                    "stock_quantity": 1
                }
            ]
        }
        response = client.post("/api/v1/masks/batch", json=masks_data)
        assert response.status_code == 201

    def test_user_ranking_edge_cases(self, client, db_session):
        """測試用戶排行榜邊界條件"""
        from app.models import User
        
        # 建立無交易記錄的用戶
        user = User(name="無交易用戶", cash_balance=100.00)
        db_session.add(user)
        db_session.commit()

        # 測試未來日期範圍，應返回空列表
        response = client.get("/api/v1/users/top-spenders?top_n=10&start_date=2030-01-01&end_date=2030-12-31")
        assert response.status_code == 200
        data = response.json()
        assert data == []

        # 測試無效日期範圍 (開始 > 結束)，應回報驗證錯誤
        response = client.get("/api/v1/users/top-spenders?start_date=2024-01-01&end_date=2023-01-01")
        assert response.status_code == 422
        assert "開始日期不能晚於結束日期" in response.json()["detail"]

    def test_pharmacy_time_filtering_edge_cases(self, client, db_session):
        """測試藥局時間過濾邊界條件"""
        from app.models import Pharmacy
        
        # 建立 24 小時營業的藥局
        pharmacy = Pharmacy(
            name="24小時藥局",
            cash_balance=100.00,
            opening_hours='{"monday": {"open": "00:00", "close": "23:59"}}'
        )
        db_session.add(pharmacy)
        db_session.commit()

        # 測試有效的邊界時間
        for time_str in ["00:00", "23:59", "12:00"]:
            response = client.get(f"/api/v1/pharmacies/?time={time_str}&day=monday")
            assert response.status_code == 200
            assert len(response.json()) >= 1
        
        # 測試無效的時間格式
        response = client.get("/api/v1/pharmacies/?time=24:00")
        assert response.status_code == 422

        # 測試無效的星期
        response = client.get("/api/v1/pharmacies/?day=invalid_day")
        assert response.status_code == 422

    def test_transaction_extreme_quantities(self, client, db_session, sample_user):
        """測試交易極端數量"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="大量庫存藥局", cash_balance=10000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="大量庫存口罩", price=0.01, stock_quantity=10000, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 假設 sample_user 有 500 元, 購買 1000 * 0.01 = 10 元的口罩，應成功
        sample_user.cash_balance = 500
        db_session.commit()
        
        # 測試極大數量交易 (應成功)
        transaction_data = {
            "user_id": sample_user.id,
            "items": [
                {
                    "pharmacy_id": pharmacy.id,
                    "mask_id": mask.id,
                    "quantity": 1000
                }
            ]
        }
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 201

        # 測試購買數量為 0
        transaction_data["items"][0]["quantity"] = 0
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 422 # 購買數量為0應視為無效請求, 由 Pydantic 驗證

    def test_logging_functions(self):
        """測試日誌配置函數"""
        from app.core.logging_config import get_logger, setup_logging
        
        # 測試 get_logger 函數
        logger = get_logger("test")
        assert logger is not None
        
        # 測試 setup_logging 函數
        logger = setup_logging("DEBUG", None, True)
        assert logger is not None