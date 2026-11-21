from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Satellite(Base):
    __tablename__ = "satellites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    norad_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    line1: Mapped[str] = mapped_column(String(100), nullable=False)
    line2: Mapped[str] = mapped_column(String(100), nullable=False)
    epoch: Mapped[str | None] = mapped_column(String(32), nullable=True)
    object_type: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="CelesTrak", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
