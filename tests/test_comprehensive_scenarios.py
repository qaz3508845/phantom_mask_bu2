"""
綜合場景測試
補充缺少的重要成功和失敗場景，確保達到「大部分」覆蓋
"""

import pytest
from datetime import datetime, date


class TestComprehensiveScenarios:
    """綜合場景測試類別"""

    # ========== 需求1: 藥局列表與過濾 ==========
    
    def test_pharmacy_list_day_filter_success(self, client, db_session):
        """測試星期過濾成功場景"""
        from app.models import Pharmacy
        
        pharmacy = Pharmacy(
            name="星期測試藥局",
            cash_balance=1000.00,
            opening_hours='{"monday": {"open": "08:00", "close": "18:00"}}'
        )
        db_session.add(pharmacy)
        db_session.commit()

        response = client.get("/api/v1/pharmacies/?day=monday")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_pharmacy_list_invalid_day_filter(self, client, db_session):
        """測試無效星期過濾失敗場景"""
        response = client.get("/api/v1/pharmacies/?day=invalid_day")
        assert response.status_code == 422

    def test_pharmacy_list_invalid_time_format(self, client, db_session):
        """測試無效時間格式失敗場景"""
        response = client.get("/api/v1/pharmacies/?time=25:00")
        assert response.status_code == 422

    # ========== 需求2: 藥局口罩列表與排序 ==========
    
    def test_pharmacy_masks_sort_by_name(self, client, db_session):
        """測試按名稱排序成功場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="排序測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        masks = [
            Mask(name="Z口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id),
            Mask(name="A口罩", price=20.00, stock_quantity=30, pharmacy_id=pharmacy.id),
        ]
        for mask in masks:
            db_session.add(mask)
        db_session.commit()

        response = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy.id}&sort_by=name&order=asc")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert data[0]["name"] < data[1]["name"]  # 按名稱升序

    def test_pharmacy_masks_invalid_pharmacy(self, client, db_session):
        """測試無效藥局ID失敗場景"""
        response = client.get("/api/v1/masks/?pharmacy_id=99999")
        assert response.status_code == 404

    def test_pharmacy_masks_empty_result(self, client, db_session):
        """測試空結果成功場景"""
        from app.models import Pharmacy
        
        pharmacy = Pharmacy(name="空口罩藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.commit()

        response = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    # ========== 需求3: 價格範圍過濾 ==========
    
    def test_price_range_invalid_parameters(self, client, db_session):
        """測試無效價格範圍參數失敗場景"""
        # 最小價格大於最大價格
        response = client.get("/api/v1/pharmacies/filter/masks?min_price=100&max_price=50")
        assert response.status_code == 422
        
        # 負數價格
        response = client.get("/api/v1/pharmacies/filter/masks?min_price=-10")
        assert response.status_code == 422

    def test_count_threshold_boundary(self, client, db_session):
        """測試數量門檻邊界條件"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="門檻測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="邊界口罩", price=10.00, stock_quantity=10, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 測試等於門檻值
        response = client.get("/api/v1/pharmacies/filter/masks?min_price=10&max_price=10&count=1")
        assert response.status_code == 200

    # ========== 需求5: 多藥局交易 ==========
    
    def test_transaction_mask_not_found(self, client, db_session):
        """測試口罩不存在的交易失敗場景"""
        from app.models import User, Pharmacy
        
        user = User(name="測試用戶", cash_balance=1000.00)
        pharmacy = Pharmacy(name="測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.commit()

        transaction_data = {
            "user_id": user.id,
            "items": [
                {
                    "pharmacy_id": pharmacy.id,
                    "mask_id": 99999,  # 不存在的口罩
                    "quantity": 1
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 404 # 口罩不存在應回傳 404 Not Found

    def test_transaction_pharmacy_not_found(self, client, db_session):
        """測試藥局不存在的交易失敗場景"""
        from app.models import User, Pharmacy, Mask
        
        user = User(name="測試用戶", cash_balance=1000.00)
        pharmacy = Pharmacy(name="測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.flush()
        
        mask = Mask(name="測試口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        transaction_data = {
            "user_id": user.id,
            "items": [
                {
                    "pharmacy_id": 99999,  # 不存在的藥局
                    "mask_id": mask.id,
                    "quantity": 1
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 404 # 藥局不存在應回傳 404 Not Found

    def test_transaction_invalid_quantity(self, client, db_session, sample_user, sample_pharmacy, sample_mask):
        """測試無效數量的交易失敗場景"""
        transaction_data = {
            "user_id": sample_user.id,
            "items": [
                {
                    "pharmacy_id": sample_pharmacy.id,
                    "mask_id": sample_mask.id,
                    "quantity": 0  # 無效數量
                }
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 422  # Pydantic 驗證錯誤

    # ========== 需求6: 庫存更新 ==========
    
    def test_mask_stock_zero_change(self, client, db_session, sample_mask):
        """測試零變更的庫存更新"""
        update_data = {"quantity_change": 0}
        response = client.patch(f"/api/v1/masks/{sample_mask.id}/stock", json=update_data)
        assert response.status_code == 200 # 零變更應視為成功，但不做事

    def test_mask_stock_extreme_quantity(self, client, db_session, sample_mask):
        """測試極大數量的庫存更新"""
        update_data = {"quantity_change": 1000000}
        response = client.patch(f"/api/v1/masks/{sample_mask.id}/stock", json=update_data)
        assert response.status_code == 200

    def test_mask_stock_result_negative(self, client, db_session):
        """測試結果為負數的庫存更新失敗場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="負庫存測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="少量庫存口罩", price=10.00, stock_quantity=5, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        update_data = {"quantity_change": -10}  # 會導致負庫存
        response = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        assert response.status_code == 400

    # ========== 需求7: 批量口罩管理 ==========
    
    def test_batch_masks_update_existing(self, client, db_session):
        """測試批量更新現有口罩成功場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="批量更新藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        existing_mask = Mask(name="現有口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(existing_mask)
        db_session.commit()

        masks_data = {
            "pharmacy_id": pharmacy.id,
            "masks": [
                # 這裡的邏輯是，如果 mask_id 不存在，則為建立
                # 如果要更新， batch_manage_masks 需要支援 id
                {"name": "更新後口罩", "price": 15.00, "stock_quantity": 60, "mask_id": existing_mask.id}
            ]
        }
        
        response = client.post("/api/v1/masks/batch", json=masks_data)
        assert response.status_code == 201
        data = response.json()
        assert data["updated_count"] == 1
        assert data["created_count"] == 0

    def test_batch_masks_duplicate_names_in_request(self, client, db_session, sample_pharmacy):
        """測試在批量建立時，如果口罩名稱與藥局內現有的名稱重複，應失敗"""
        from app.models import Mask

        # 1. 先在藥局中建立一個口罩
        existing_mask_name = "已存在的口罩"
        existing_mask = Mask(
            name=existing_mask_name, 
            price=10.00, 
            stock_quantity=50, 
            pharmacy_id=sample_pharmacy.id
        )
        db_session.add(existing_mask)
        db_session.commit()

        # 2. 準備批量請求，其中包含一個與現有口罩同名的項目
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {"name": "新口罩A", "price": 12.00, "stock_quantity": 20},
                {"name": existing_mask_name, "price": 15.00, "stock_quantity": 30} # 名稱重複
            ]
        }
        
        # 3. 發送請求，預期會收到 409 Conflict 錯誤
        response = client.post("/api/v1/masks/batch", json=masks_data)
        assert response.status_code == 409
        
        # 4. 驗證錯誤訊息是否符合預期
        error_detail = response.json()["detail"]
        assert existing_mask_name in error_detail
        assert "已存在" in error_detail

    def test_batch_masks_empty_list(self, client, db_session, sample_pharmacy):
        """測試空批量列表失敗場景"""
        masks_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": []
        }
        
        response = client.post("/api/v1/masks/batch", json=masks_data)
        assert response.status_code == 422 # Pydantic 驗證應要求 list 不為空

    # ========== 需求8: 搜尋功能 ==========
    
    def test_search_special_characters(self, client, db_session):
        """測試特殊字符搜尋成功場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="特殊@字符#藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="特殊$字符%口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 測試會被 URL 編碼的特殊字符
        response = client.get("/api/v1/pharmacies/search?q=%40") # @
        assert response.status_code == 200
        
        response = client.get("/api/v1/masks/search?q=%24") # $
        assert response.status_code == 200

    def test_search_fuzzy_matching_boundary(self, client, db_session):
        """測試模糊匹配邊界條件"""
        from app.models import Pharmacy
        
        pharmacy = Pharmacy(name="測試模糊匹配藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.commit()

        # 部分匹配
        response = client.get("/api/v1/pharmacies/search?q=模糊")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_search_very_long_query(self, client, db_session):
        """測試極長搜尋查詢"""
        long_query = "a" * 250
        response = client.get(f"/api/v1/pharmacies/search?q={long_query}")
        assert response.status_code == 200 # 應能處理長查詢，返回空列表
        assert response.json() == []

    # ========== 綜合錯誤處理 ==========
    
    def test_malformed_json_requests(self, client):
        """測試格式錯誤的JSON請求失敗場景"""
        # 測試交易API
        response = client.post("/api/v1/transactions/multi-pharmacy", 
                              data="invalid json", 
                              headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_missing_required_fields(self, client, db_session, sample_pharmacy):
        """測試缺少必要欄位的請求失敗場景"""
        # 缺少必要欄位的批量口罩請求
        incomplete_data = {
            "pharmacy_id": sample_pharmacy.id,
            "masks": [
                {"name": "不完整口罩"}  # 缺少 price 和 stock_quantity
            ]
        }
        
        response = client.post("/api/v1/masks/batch", json=incomplete_data)
        assert response.status_code == 422

    def test_sql_injection_prevention(self, client, db_session):
        """測試SQL注入防護"""
        malicious_query = "' OR 1=1 --"
        response = client.get(f"/api/v1/pharmacies/search?q={malicious_query}")
        assert response.status_code == 200 # 不應引發錯誤，應回傳空列表
        assert response.json() == []

    def test_concurrent_stock_updates(self, client, db_session):
        """測試併發庫存更新場景"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="併發測試藥局", cash_balance=1000.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="併發測試口罩", price=10.00, stock_quantity=100, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        # 這個測試在單線程的 sqlite 上意義不大，但在支援並發的資料庫上很重要
        # 這裡僅為示意
        update_data = {"quantity_change": -1}
        response1 = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        response2 = client.patch(f"/api/v1/masks/{mask.id}/stock", json=update_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200 # 在測試環境下，請求是序列的
        
        db_session.refresh(mask)
        assert mask.stock_quantity == 98
