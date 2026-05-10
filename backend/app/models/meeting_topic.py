"""会议主题模型定义。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class MeetingTopic(Base):
    """会议主题。"""

    __tablename__ = "meeting_topics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="topics", lazy="selectin")
