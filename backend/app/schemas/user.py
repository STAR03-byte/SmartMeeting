"""用户 Schema 定义。"""

from datetime import datetime
from typing import ClassVar
from typing import Literal

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

UserRole = Literal["admin", "member"]


class UserCreate(BaseModel):
    """创建用户请求。"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = Field(default="member")


class UserUpdate(BaseModel):
    """更新用户请求。"""

    email: EmailStr | None = None
    password_hash: str | None = Field(default=None, min_length=8, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    """用户响应。"""

    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int
