"""会议模型定义。"""

# pyright: reportImportCycles=false

from datetime import datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.database import Base  # pyright: ignore[reportAny]

if TYPE_CHECKING:
    from app.models.meeting_participant import MeetingParticipant
    from app.models.team import Team
    from app.models.user import User


TypedBase = cast(type[DeclarativeBase], Base)


class Meeting(TypedBase):
    """会议主表。"""

    __tablename__: str = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    scheduled_start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned", nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    shared_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    postprocessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    postprocess_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organizer: Mapped["User"] = relationship("User", foreign_keys=[organizer_id])
    team: Mapped["Team | None"] = relationship("Team")
    participants: Mapped[list["MeetingParticipant"]] = relationship("MeetingParticipant")
