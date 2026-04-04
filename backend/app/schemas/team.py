"""团队 Schema 定义。"""

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class TeamCreate(BaseModel):
    """创建团队请求。"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False


class TeamOut(BaseModel):
    """团队响应。"""

    id: int
    name: str
    description: str | None
    is_public: bool
    owner_id: int
    my_role: str  # 当前用户在该团队的角色
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class TeamMemberOut(BaseModel):
    """团队成员响应。"""

    user_id: int
    user_name: str
    full_name: str
    email: str
    role: str
    joined_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class AddTeamMember(BaseModel):
    """添加团队成员请求。"""

    user_id: int
    role: Literal["admin", "member"] = "member"


class UpdateMemberRole(BaseModel):
    """修改成员角色请求。"""

    role: Literal["admin", "member"]
