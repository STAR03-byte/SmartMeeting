"""会议参与人模型定义。"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MeetingParticipant(Base):
    """会议参与人关系。"""

    __tablename__ = "meeting_participants"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id", name="uk_meeting_participants_unique"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(
        Enum("organizer", "participant", name="meeting_participant_role"),
        nullable=True,
        default="participant",
    )
    participant_role: Mapped[str] = mapped_column(String(20), default="required", nullable=False)
    attendance_status: Mapped[str] = mapped_column(String(20), default="invited", nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
