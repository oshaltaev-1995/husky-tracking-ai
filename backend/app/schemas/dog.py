from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class DogCreate(DogBase):
    pass


class DogRead(DogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)