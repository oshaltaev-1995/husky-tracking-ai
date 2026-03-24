from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Worklog(Base):
    __tablename__ = "worklogs"
    __table_args__ = (
        UniqueConstraint("dog_id", "work_date", name="uq_worklog_dog_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    dog_id: Mapped[int] = mapped_column(
        ForeignKey("dogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    week_label: Mapped[str | None] = mapped_column(String(20), nullable=True)

    km: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    worked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    programs_10km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    programs_3km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    kennel_row: Mapped[str | None] = mapped_column(String(50), nullable=True)
    home_slot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    main_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    dog: Mapped["Dog"] = relationship("Dog", back_populates="worklogs")