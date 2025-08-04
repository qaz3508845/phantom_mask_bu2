"""
基礎 Schema 模型
"""

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """基礎回應模型"""
    model_config = ConfigDict(from_attributes=True)