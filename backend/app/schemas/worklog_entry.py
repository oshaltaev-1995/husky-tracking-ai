from datetime import date
from pydantic import BaseModel, Field


class WorklogEntryCreate(BaseModel):
    dog_id: int
    work_date: date
    km: float = Field(default=0, ge=0)
    worked: bool = False
    week_label: str | None = None
    programs_10km: int = Field(default=0, ge=0)
    programs_3km: int = Field(default=0, ge=0)
    main_role: str | None = None
    kennel_row: str | None = None
    home_slot: str | None = None
    status: str | None = None
    notes: str | None = None


class WorklogEntryRead(BaseModel):
    id: int
    dog_id: int
    work_date: date
    km: float
    worked: bool
    week_label: str | None = None
    programs_10km: int
    programs_3km: int
    main_role: str | None = None
    kennel_row: str | None = None
    home_slot: str | None = None
    status: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}