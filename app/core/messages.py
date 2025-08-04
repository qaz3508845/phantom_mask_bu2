"""
錯誤訊息常數定義
統一管理所有錯誤訊息，方便維護和國際化
"""


class ErrorMessages:
    """錯誤訊息常數類"""
    
    # 通用錯誤
    INVALID_REQUEST = "請求格式不正確"
    INTERNAL_ERROR = "系統內部錯誤"
    DATABASE_ERROR = "資料庫操作失敗"
    
    # 藥局相關錯誤
    PHARMACY_NOT_FOUND = "藥局 ID {pharmacy_id} 不存在"
    PHARMACY_DUPLICATE_NAME = "藥局名稱已存在"
    
    # 口罩相關錯誤
    MASK_NOT_FOUND = "口罩 ID {mask_id} 不存在"
    MASK_INSUFFICIENT_STOCK = "庫存不足，現有庫存: {current_stock}，試圖減少: {requested_decrease}"
    MASK_DUPLICATE_NAME = "口罩名稱已存在於該藥局"
    MASK_BATCH_DUPLICATE_NAMES = "請求中包含重複的口罩名稱: {duplicate_names}"
    MASK_EXISTING_NAMES_IN_PHARMACY = "藥局 '{pharmacy_name}' 中已存在以下口罩名稱: {existing_names}"
    
    # 用戶相關錯誤
    USER_NOT_FOUND = "用戶 ID {user_id} 不存在"
    USER_INSUFFICIENT_BALANCE = "用戶餘額不足"
    USER_DUPLICATE_NAME = "用戶名稱已存在"
    
    # 交易相關錯誤
    TRANSACTION_NOT_FOUND = "交易 ID {transaction_id} 不存在"
    TRANSACTION_FAILED = "交易處理失敗"
    TRANSACTION_CONCURRENT_CONFLICT = "交易發生衝突，請稍後重試"
    
    # 搜尋相關錯誤
    SEARCH_EMPTY_QUERY = "搜尋關鍵字不能為空"
    SEARCH_NO_RESULTS = "未找到符合條件的結果"
    
    # 參數驗證錯誤
    INVALID_DATE_RANGE = "開始日期不能晚於結束日期"
    INVALID_PRICE_RANGE = "價格下限不能大於價格上限"
    INVALID_COUNT_RANGE = "數量下限不能大於數量上限"  
    INVALID_TIME_FORMAT = "無效的時間格式: {time_str}。請使用 HH:MM 格式，例如: 09:30, 14:00, 23:59"
    INVALID_DAY_FORMAT = "無效的星期格式: {day_input}。請使用英文 (monday-sunday) 或數字 (1-7，1=星期一)"
    
    # 併發控制錯誤
    STOCK_UPDATE_CONFLICT = "庫存更新發生衝突，請稍後重試"
    BATCH_OPERATION_CONFLICT = "批量操作發生衝突，請稍後重試"
    DEADLOCK_DETECTED = "操作發生衝突，請稍後重試"


class SuccessMessages:
    """成功訊息常數類"""
    
    # 通用成功
    OPERATION_SUCCESS = "操作成功"
    
    # 口罩相關成功
    STOCK_UPDATED = "庫存更新成功"
    BATCH_OPERATION_SUCCESS = "批量操作完成"
    
    # 交易相關成功
    TRANSACTION_CREATED = "交易建立成功"
    MULTI_PHARMACY_TRANSACTION_SUCCESS = "多藥局交易處理完成"


class ValidationMessages:
    """驗證訊息常數類"""
    
    # 欄位驗證
    FIELD_REQUIRED = "此欄位為必填"
    FIELD_TOO_SHORT = "欄位長度過短"
    FIELD_TOO_LONG = "欄位長度過長"
    FIELD_INVALID_FORMAT = "欄位格式不正確"
    
    # 數值驗證
    VALUE_TOO_SMALL = "數值過小"
    VALUE_TOO_LARGE = "數值過大"
    VALUE_NOT_POSITIVE = "數值必須為正數"
    VALUE_NOT_NEGATIVE = "數值不能為負數"


# 便利函數
def format_error(template: str, **kwargs) -> str:
    """格式化錯誤訊息"""
    return template.format(**kwargs)


# 常用的格式化錯誤訊息函數
def pharmacy_not_found(pharmacy_id: int) -> str:
    return format_error(ErrorMessages.PHARMACY_NOT_FOUND, pharmacy_id=pharmacy_id)


def mask_not_found(mask_id: int) -> str:
    return format_error(ErrorMessages.MASK_NOT_FOUND, mask_id=mask_id)


def user_not_found(user_id: int) -> str:
    return format_error(ErrorMessages.USER_NOT_FOUND, user_id=user_id)


def transaction_not_found(transaction_id: int) -> str:
    return format_error(ErrorMessages.TRANSACTION_NOT_FOUND, transaction_id=transaction_id)


def insufficient_stock(current_stock: int, requested_decrease: int) -> str:
    return format_error(
        ErrorMessages.MASK_INSUFFICIENT_STOCK, 
        current_stock=current_stock, 
        requested_decrease=requested_decrease
    )


def invalid_time_format(time_str: str) -> str:
    return format_error(ErrorMessages.INVALID_TIME_FORMAT, time_str=time_str)


def invalid_day_format(day_input: str) -> str:
    return format_error(ErrorMessages.INVALID_DAY_FORMAT, day_input=day_input)


def mask_batch_duplicate_names(duplicate_names: str) -> str:
    return format_error(ErrorMessages.MASK_BATCH_DUPLICATE_NAMES, duplicate_names=duplicate_names)


def mask_existing_names_in_pharmacy(pharmacy_name: str, existing_names: str) -> str:
    return format_error(
        ErrorMessages.MASK_EXISTING_NAMES_IN_PHARMACY, 
        pharmacy_name=pharmacy_name, 
        existing_names=existing_names
    )