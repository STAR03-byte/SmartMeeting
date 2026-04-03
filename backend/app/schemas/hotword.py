from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class HotwordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)


class HotwordOut(BaseModel):
    id: int
    user_id: int
    word: str
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
