"""会议承诺模型定义。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.task import Task
    from app.models.user import User


class Commitment(Base):
    """会议承诺。"""

    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    assignee_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assignee_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    due_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="candidate", nullable=False)
    linked_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="commitments", lazy="selectin")
    assignee_user: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_user_id], lazy="selectin")
    linked_task: Mapped["Task | None"] = relationship("Task", lazy="selectin")
