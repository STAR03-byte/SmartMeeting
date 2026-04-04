from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.database import Base  # pyright: ignore[reportAny]

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.user import User

    class TeamMember: ...

TypedBase = cast(type[DeclarativeBase], Base)


class Team(TypedBase):
    __tablename__: str = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    members: Mapped[list["TeamMember"]] = relationship("TeamMember", overlaps="team")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    meetings: Mapped[list["Meeting"]] = relationship("Meeting", overlaps="team")
