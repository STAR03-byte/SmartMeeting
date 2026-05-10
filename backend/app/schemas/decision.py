"""决策相关 Schema。"""

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class DecisionCreate(BaseModel):
    """创建决策请求。"""

    meeting_id: int
    content: str = Field(..., min_length=1, max_length=5000)
    proposer_name: str | None = None
    proposer_user_id: int | None = None
    context: str | None = None
    confidence: float = Field(default=0.7, ge=0, le=1)


class DecisionUpdate(BaseModel):
    """更新决策请求。"""

    content: str | None = Field(default=None, min_length=1, max_length=5000)
    proposer_name: str | None = None
    proposer_user_id: int | None = None
    context: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: str | None = None


class DecisionOut(BaseModel):
    """决策响应。"""

    id: int
    meeting_id: int
    content: str
    proposer_name: str | None
    proposer_user_id: int | None
    context: str | None
    confidence: float | None
    status: str
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class DecisionListOut(BaseModel):
    """决策列表响应。"""

    items: list[DecisionOut]
    total: int
