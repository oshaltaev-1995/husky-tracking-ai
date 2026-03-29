from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import AvailabilityStatus, LifecycleStatus

if TYPE_CHECKING:
    from app.models.worklog import Worklog


class Dog(Base):
    __tablename__ = "dogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    external_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)

    kennel_row: Mapped[str | None] = mapped_column(String(50), nullable=True)
    kennel_block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    primary_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    can_lead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_wheel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LifecycleStatus.active,
    )
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        String(30),
        nullable=False,
        default=AvailabilityStatus.available,
    )
    exclude_from_team_builder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exclude_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    worklogs: Mapped[list[Worklog]] = relationship(
        "Worklog",
        back_populates="dog",
        cascade="all, delete-orphan",
    )