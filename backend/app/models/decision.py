"""会议决策模型定义。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.user import User


class Decision(Base):
    """会议决策。"""

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    proposer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proposer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="candidate", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="decisions", lazy="selectin")
    proposer_user: Mapped["User | None"] = relationship("User", foreign_keys=[proposer_user_id], lazy="selectin")
