"""
Domain Schema 模型匯出
"""

# 藥局相關
from .pharmacy import (
    PharmacyBase,
    PharmacyResponse,
    PharmacyWithMaskCountResponse
)

# 口罩相關
from .mask import (
    MaskBase,
    MaskCreate,
    MaskUpdate,
    MaskResponse,
    StockUpdateRequest,
    StockUpdateResponse,
    BatchMaskItem,
    BatchMaskRequest,
    BatchMaskResponse
)

# 用戶相關
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRankingResponse
)

# 交易相關
from .transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    TransactionDetailResponse,
    MultiPharmacyTransactionItem,
    MultiPharmacyTransactionCreate,
    MultiPharmacyTransactionResponse
)

# 搜尋相關
from .search import (
    SearchResultItem,
    UnifiedSearchResponse
)

__all__ = [
    # 藥局相關
    "PharmacyBase",
    "PharmacyResponse", 
    "PharmacyWithMaskCountResponse",
    
    # 口罩相關
    "MaskBase",
    "MaskCreate",
    "MaskUpdate", 
    "MaskResponse",
    "StockUpdateRequest",
    "StockUpdateResponse",
    "BatchMaskItem",
    "BatchMaskRequest",
    "BatchMaskResponse",
    
    # 用戶相關
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserRankingResponse",
    
    # 交易相關
    "TransactionBase",
    "TransactionCreate",
    "TransactionResponse",
    "TransactionDetailResponse",
    "MultiPharmacyTransactionItem", 
    "MultiPharmacyTransactionCreate",
    "MultiPharmacyTransactionResponse",
    
    # 搜尋相關
    "SearchResultItem",
    "UnifiedSearchResponse"
]