"""会议转写模型定义。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MeetingTranscript(Base):
    """会议转写片段。"""

    __tablename__ = "meeting_transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False, index=True)
    speaker_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    speaker_id: Mapped[int | None] = mapped_column(nullable=True)
    speaker_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    segment_index: Mapped[int] = mapped_column(nullable=False)
    start_time_sec: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    end_time_sec: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="zh-CN", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="whisper", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
