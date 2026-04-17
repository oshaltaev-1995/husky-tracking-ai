from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvailabilityStatus, LifecycleStatus


class DogBase(BaseModel):
    name: str
    external_id: int | None = None
    birth_year: int | None = None
    sex: str | None = None
    kennel_row: str | None = None
    kennel_block: int | None = None
    home_slot: int | None = None
    primary_role: str | None = None
    can_lead: bool = False
    can_team: bool = True
    can_wheel: bool = False
    status: str | None = None
    notes: str | None = None
    is_active: bool = True

    lifecycle_status: LifecycleStatus = LifecycleStatus.active
    availability_status: AvailabilityStatus = AvailabilityStatus.available
    exclude_from_team_builder: bool = False
    exclude_reason: str | None = None


class DogCreate(DogBase):
    pass


class DogUpdate(BaseModel):
    name: str | None = None
    external_id: int | None = None
    birth_year: int | None = None
    sex: str | None = None
    kennel_row: str | None = None
    kennel_block: int | None = None
    home_slot: int | None = None
    primary_role: str | None = None
    can_lead: bool | None = None
    can_team: bool | None = None
    can_wheel: bool | None = None
    status: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class DogRead(DogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)