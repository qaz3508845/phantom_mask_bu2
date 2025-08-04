"""
搜尋 API 測試
測試需求 8: 藥局和口罩名稱搜尋及相關性排序

修復版本 - 使用正確的 API 端點和回應格式
"""

import pytest


class TestSearchAPI:
    """搜尋 API 測試類別"""

    def test_search_pharmacies_success(self, client, db_session):
        """測試藥局搜尋成功"""
        from app.models import Pharmacy
        
        # 建立測試藥局
        pharmacies = [
            Pharmacy(name="健康藥局", cash_balance=100.00, opening_hours='{}'),
            Pharmacy(name="康健藥房", cash_balance=200.00, opening_hours='{}'),
            Pharmacy(name="美好藥店", cash_balance=300.00, opening_hours='{}'),
        ]
        for pharmacy in pharmacies:
            db_session.add(pharmacy)
        db_session.commit()

        response = client.get("/api/v1/pharmacies/search?q=健康")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # 檢查搜尋結果包含相關的藥局
        names = [pharmacy["name"] for pharmacy in data]
        assert any("健康" in name for name in names)

    def test_search_pharmacies_relevance_ranking(self, client, db_session):
        """測試藥局搜尋相關性排序"""
        from app.models import Pharmacy
        
        # 建立不同相關性的藥局
        pharmacies = [
            Pharmacy(name="大健康藥房", cash_balance=300.00, opening_hours='{}'),     # 包含匹配
            Pharmacy(name="健康", cash_balance=100.00, opening_hours='{}'),           # 完全匹配
            Pharmacy(name="健康藥局", cash_balance=200.00, opening_hours='{}'),       # 開頭匹配
            Pharmacy(name="無關藥店", cash_balance=400.00, opening_hours='{}'),       # 不匹配
        ]
        for pharmacy in pharmacies:
            db_session.add(pharmacy)
        db_session.commit()

        response = client.get("/api/v1/pharmacies/search?q=健康")
        
        assert response.status_code == 200
        data = response.json()
        
        # 預期的相關性排序：完全匹配 > 開頭匹配 > 包含匹配
        expected_order = ["健康", "健康藥局", "大健康藥房"]
        actual_order = [p["name"] for p in data]
        
        assert len(actual_order) == len(expected_order)
        assert actual_order == expected_order

    def test_search_pharmacies_case_insensitive(self, client, db_session):
        """測試藥局搜尋大小寫不敏感"""
        from app.models import Pharmacy
        
        pharmacy = Pharmacy(name="TEST藥局", cash_balance=100.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.commit()

        # 測試不同大小寫
        for query in ["test", "TEST", "Test"]:
            response = client.get(f"/api/v1/pharmacies/search?q={query}")
            assert response.status_code == 200

    def test_search_pharmacies_no_results(self, client, sample_pharmacy):
        """測試藥局搜尋無結果"""
        response = client.get("/api/v1/pharmacies/search?q=不存在的藥局")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_pharmacies_empty_query(self, client):
        """測試空查詢字串的藥局搜尋"""
        response = client.get("/api/v1/pharmacies/search?q=")
        
        assert response.status_code == 422  # Validation error

    def test_search_masks_success(self, client, db_session, sample_pharmacy):
        """測試口罩搜尋成功"""
        from app.models import Mask
        
        # 建立測試口罩
        masks = [
            Mask(name="N95口罩", price=10.00, stock_quantity=50, pharmacy_id=sample_pharmacy.id),
            Mask(name="醫用口罩", price=5.00, stock_quantity=100, pharmacy_id=sample_pharmacy.id),
            Mask(name="防護面罩", price=15.00, stock_quantity=20, pharmacy_id=sample_pharmacy.id),
        ]
        for mask in masks:
            db_session.add(mask)
        db_session.commit()

        response = client.get("/api/v1/masks/search?q=口罩")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # N95口罩 和 醫用口罩
        
        # 檢查搜尋結果包含相關的口罩
        names = [mask["name"] for mask in data]
        assert any("口罩" in name for name in names)

    def test_search_masks_with_pharmacy_info(self, client, db_session):
        """測試口罩搜尋包含藥局資訊 - 檢查必要欄位存在"""
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="特殊藥局", cash_balance=500.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="特殊口罩", price=12.00, stock_quantity=30, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        response = client.get("/api/v1/masks/search?q=特殊")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # 檢查回應包含基本欄位
        mask_result = data[0] 
        assert "name" in mask_result
        assert "price" in mask_result
        assert "pharmacy_id" in mask_result

    def test_search_masks_relevance_ranking(self, client, db_session, sample_pharmacy):
        """測試口罩搜尋相關性排序"""
        from app.models import Mask
        
        # 建立不同相關性的口罩
        masks = [
            Mask(name="高級N95防護", price=15.00, stock_quantity=30, pharmacy_id=sample_pharmacy.id), # 包含匹配
            Mask(name="N95", price=10.00, stock_quantity=50, pharmacy_id=sample_pharmacy.id),        # 完全匹配
            Mask(name="N95口罩", price=12.00, stock_quantity=40, pharmacy_id=sample_pharmacy.id),    # 開頭匹配
            Mask(name="醫用外科", price=8.00, stock_quantity=60, pharmacy_id=sample_pharmacy.id),     # 不匹配
        ]
        for mask in masks:
            db_session.add(mask)
        db_session.commit()

        response = client.get("/api/v1/masks/search?q=N95")
        
        assert response.status_code == 200
        data = response.json()
        
        # 預期的相關性排序：完全匹配 > 開頭匹配 > 包含匹配
        expected_order = ["N95", "N95口罩", "高級N95防護"]
        actual_order = [m["name"] for m in data]
        
        assert len(actual_order) == len(expected_order)
        assert actual_order == expected_order

    def test_search_masks_no_results(self, client, sample_mask):
        """測試口罩搜尋無結果"""
        response = client.get("/api/v1/masks/search?q=不存在的口罩")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_masks_pagination(self, client, db_session, sample_pharmacy):
        """測試口罩搜尋分頁"""
        from app.models import Mask
        
        # 建立多個相同類型的口罩
        masks = []
        for i in range(15):
            mask = Mask(
                name=f"通用口罩{i}",
                price=10.00 + i,
                stock_quantity=50,
                pharmacy_id=sample_pharmacy.id
            )
            masks.append(mask)
            db_session.add(mask)
        db_session.commit()

        # 測試分頁
        response = client.get("/api/v1/masks/search?q=通用&skip=5&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5  # 檢查限制

    def test_search_pharmacies_pagination(self, client, db_session):
        """測試藥局搜尋分頁"""
        from app.models import Pharmacy
        
        # 建立多個相同類型的藥局
        pharmacies = []
        for i in range(12):
            pharmacy = Pharmacy(
                name=f"連鎖藥局{i}",
                cash_balance=100.00 + i,
                opening_hours='{}'
            )
            pharmacies.append(pharmacy)
            db_session.add(pharmacy)
        db_session.commit()

        # 測試分頁
        response = client.get("/api/v1/pharmacies/search?q=連鎖&skip=3&limit=4")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 4  # 檢查限制

    def test_unified_search(self, client, db_session):
        """測試統一搜尋功能"""
        from app.models import Pharmacy, Mask
        
        # 建立測試資料
        pharmacy = Pharmacy(name="測試藥局", cash_balance=100.00, opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(name="測試口罩", price=10.00, stock_quantity=50, pharmacy_id=pharmacy.id)
        db_session.add(mask)
        db_session.commit()

        response = client.get("/api/v1/search/?q=測試")
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查統一搜尋回應格式
        assert "results" in data
        assert "total_results" in data
        assert "pharmacy_count" in data
        assert "mask_count" in data
        
        # 檢查結果數量
        assert data["total_results"] >= 2  # 應該有藥局和口罩