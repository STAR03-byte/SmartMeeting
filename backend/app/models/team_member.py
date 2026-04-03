from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.database import Base  # pyright: ignore[reportAny]

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User

TypedBase = cast(type[DeclarativeBase], Base)


class TeamMember(TypedBase):
    __tablename__: str = "team_members"
    __table_args__: tuple[UniqueConstraint] = (
        UniqueConstraint("team_id", "user_id", name="uk_team_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        Enum("owner", "admin", "member", name="team_member_role"),
        nullable=False,
        default="member",
        server_default="member",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    team: Mapped["Team"] = relationship("Team", overlaps="members")
    user: Mapped["User"] = relationship("User")
