from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel
from pydantic.config import ConfigDict


class TeamInvitationCreate(BaseModel):
    invitee_id: int


class TeamInvitationOut(BaseModel):
    id: int
    team_id: int
    inviter_id: int
    invitee_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
