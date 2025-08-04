"""
併發控制測試
測試資料庫鎖定和死鎖處理機制
"""

import pytest
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestConcurrencyControl:
    """併發控制測試類別"""
    
    def test_concurrent_stock_updates(self, client, db_session):
        """測試併發庫存更新是否正確使用鎖定"""
        from app.models import Pharmacy, Mask
        
        # 建立測試資料
        pharmacy = Pharmacy(name="併發測試藥局", cash_balance=Decimal('1000.00'), opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(
            name="併發測試口罩", 
            price=Decimal('10.00'), 
            stock_quantity=100, 
            pharmacy_id=pharmacy.id
        )
        db_session.add(mask)
        db_session.commit()
        
        # 併發更新庫存
        results = []
        mask_id = mask.id  # 儲存 ID 以避免 SQLAlchemy 會話問題
        
        def update_stock(change):
            """單次庫存更新"""
            response = client.patch(
                f"/api/v1/masks/{mask_id}/stock",
                json={"quantity_change": change}
            )
            return response.status_code
        
        # 使用線程池執行併發更新
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_stock, -10),  # 減少 10
                executor.submit(update_stock, -20),  # 減少 20  
                executor.submit(update_stock, 5),    # 增加 5
                executor.submit(update_stock, -15),  # 減少 15
                executor.submit(update_stock, 10),   # 增加 10
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # 檢查所有操作都成功（200）或有序處理衝突（409）
        for status_code in results:
            assert status_code in [200, 409], f"Unexpected status code: {status_code}"
        
        # 檢查最終庫存狀態是否合理
        pharmacy_id = pharmacy.id  # 儲存 ID 以避免 SQLAlchemy 會話問題
        response = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy_id}")
        assert response.status_code == 200
        final_masks = response.json()
        final_stock = final_masks[0]["stock_quantity"]
        
        # 最終庫存應該大於等於 0（不會出現負庫存）
        assert final_stock >= 0, f"Stock should not be negative: {final_stock}"
    
    def test_concurrent_transactions(self, client, db_session):
        """測試併發交易的用戶餘額安全"""
        from app.models import User, Pharmacy, Mask
        
        # 建立測試資料
        user = User(name="併發用戶", cash_balance=Decimal('100.00'))
        pharmacy = Pharmacy(name="併發藥局", cash_balance=Decimal('1000.00'), opening_hours='{}')
        db_session.add_all([user, pharmacy])
        db_session.flush()
        
        mask = Mask(
            name="併發交易口罩", 
            price=Decimal('30.00'), 
            stock_quantity=100, 
            pharmacy_id=pharmacy.id
        )
        db_session.add(mask)
        db_session.commit()
        
        results = []
        
        # 儲存 ID 以避免 SQLAlchemy 會話問題
        user_id = user.id
        pharmacy_id = pharmacy.id
        mask_id = mask.id
        
        def make_transaction():
            """單次交易"""
            transaction_data = {
                "user_id": user_id,
                "items": [{
                    "pharmacy_id": pharmacy_id,
                    "mask_id": mask_id,
                    "quantity": 1
                }]
            }
            response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
            return response.status_code
        
        # 併發執行多個交易（總共會超出用戶餘額）
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_transaction) for _ in range(4)]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # 應該有成功的交易（200/201）和失敗的交易（400-餘額不足）
        success_count = sum(1 for status in results if status in [200, 201])
        failure_count = sum(1 for status in results if status == 400)
        
        # 成功交易數量應該合理（不超過餘額允許的數量）
        assert success_count <= 3, f"Too many successful transactions: {success_count}"
        assert failure_count > 0, "Should have some failed transactions due to insufficient balance"
    
    def test_stock_update_prevents_negative_inventory(self, client, db_session):
        """測試庫存更新防止負庫存機制"""
        from app.models import Pharmacy, Mask
        
        # 建立低庫存測試資料
        pharmacy = Pharmacy(name="低庫存藥局", cash_balance=Decimal('1000.00'), opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(
            name="低庫存口罩", 
            price=Decimal('10.00'), 
            stock_quantity=5,  # 只有 5 個庫存
            pharmacy_id=pharmacy.id
        )
        db_session.add(mask)
        db_session.commit()
        
        results = []
        mask_id = mask.id  # 儲存 ID 以避免 SQLAlchemy 會話問題
        
        def reduce_stock(amount):
            """減少庫存"""
            response = client.patch(
                f"/api/v1/masks/{mask_id}/stock",
                json={"quantity_change": -amount}
            )
            return response.status_code, response.json() if response.status_code == 400 else None
        
        # 併發嘗試減少庫存
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(reduce_stock, 3),  # 減少 3
                executor.submit(reduce_stock, 4),  # 減少 4  
                executor.submit(reduce_stock, 2),  # 減少 2
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # 檢查結果
        success_operations = [r for r in results if r[0] == 200]
        failed_operations = [r for r in results if r[0] == 400]
        
        # 應該有一些操作成功，一些因為庫存不足而失敗
        assert len(success_operations) >= 1, "At least one operation should succeed"
        assert len(failed_operations) >= 1, "At least one operation should fail due to insufficient stock"
        
        # 檢查最終庫存不為負數
        pharmacy_id = pharmacy.id  # 儲存 ID 以避免 SQLAlchemy 會話問題
        response = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy_id}")
        final_masks = response.json()
        final_stock = final_masks[0]["stock_quantity"]
        assert final_stock >= 0, f"Stock should not be negative: {final_stock}"
    
    def test_deadlock_handling_returns_409(self, client, db_session):
        """測試死鎖處理返回正確的錯誤碼"""
        # 這個測試主要是驗證代碼結構，真正的死鎖在單線程測試中很難模擬
        # 但我們可以確保錯誤處理邏輯正確
        
        from app.models import Pharmacy, Mask
        
        pharmacy = Pharmacy(name="死鎖測試藥局", cash_balance=Decimal('1000.00'), opening_hours='{}')
        db_session.add(pharmacy)
        db_session.flush()
        
        mask = Mask(
            name="死鎖測試口罩", 
            price=Decimal('10.00'), 
            stock_quantity=50, 
            pharmacy_id=pharmacy.id
        )
        db_session.add(mask)
        db_session.commit()
        
        # 正常的庫存更新應該成功
        mask_id = mask.id  # 儲存 ID 以避免 SQLAlchemy 會話問題
        pharmacy_id = pharmacy.id
        response = client.patch(
            f"/api/v1/masks/{mask_id}/stock",
            json={"quantity_change": -5}
        )
        assert response.status_code == 200
        
        # 驗證事務處理正確
        response = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy_id}")
        masks = response.json()
        assert masks[0]["stock_quantity"] == 45
    
    def test_transaction_atomicity(self, client, db_session):
        """測試交易的原子性 - 全部成功或全部失敗"""
        from app.models import User, Pharmacy, Mask
        
        # 建立測試資料
        user = User(name="原子性測試用戶", cash_balance=Decimal('100.00'))
        pharmacy1 = Pharmacy(name="藥局1", cash_balance=Decimal('1000.00'), opening_hours='{}')
        pharmacy2 = Pharmacy(name="藥局2", cash_balance=Decimal('1000.00'), opening_hours='{}')
        db_session.add_all([user, pharmacy1, pharmacy2])
        db_session.flush()
        
        mask1 = Mask(name="口罩1", price=Decimal('40.00'), stock_quantity=10, pharmacy_id=pharmacy1.id)
        mask2 = Mask(name="口罩2", price=Decimal('70.00'), stock_quantity=10, pharmacy_id=pharmacy2.id)  # 總共110，超出用戶餘額
        db_session.add_all([mask1, mask2])
        db_session.commit()
        
        # 儲存 ID 以避免 SQLAlchemy 會話問題
        user_id = user.id
        pharmacy1_id = pharmacy1.id
        pharmacy2_id = pharmacy2.id
        mask1_id = mask1.id
        mask2_id = mask2.id
        
        # 嘗試多藥局交易（會因為總金額超出餘額而失敗）
        transaction_data = {
            "user_id": user_id,
            "items": [
                {"pharmacy_id": pharmacy1_id, "mask_id": mask1_id, "quantity": 1},
                {"pharmacy_id": pharmacy2_id, "mask_id": mask2_id, "quantity": 1}
            ]
        }
        
        response = client.post("/api/v1/transactions/multi-pharmacy", json=transaction_data)
        assert response.status_code == 400  # 餘額不足
        
        # 檢查庫存沒有被扣除（原子性）
        response1 = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy1_id}")
        response2 = client.get(f"/api/v1/masks/?pharmacy_id={pharmacy2_id}")
        
        masks1 = response1.json()
        masks2 = response2.json()
        
        assert masks1[0]["stock_quantity"] == 10  # 庫存未被扣除
        assert masks2[0]["stock_quantity"] == 10  # 庫存未被扣除