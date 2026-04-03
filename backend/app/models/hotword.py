from datetime import datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Hotword(Base):
    __tablename__: ClassVar[str] = "hotwords"
    __table_args__: ClassVar[tuple[UniqueConstraint, ...]] = (
        UniqueConstraint("user_id", "word", name="uq_hotwords_user_word"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
