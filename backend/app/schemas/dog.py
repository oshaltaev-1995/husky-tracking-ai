from pydantic import BaseModel


class DogBase(BaseModel):
    name: str
    primary_role: str | None = None
    can_lead: bool = False
    can_team: bool = True
    can_wheel: bool = False
    birth_year: int | None = None
    sex: str | None = None
    kennel_side: str | None = None
    home_row: str | None = None
    home_slot: str | None = None
    notes: str | None = None


class DogCreate(DogBase):
    external_id: int | None = None


class DogRead(DogBase):
    id: int
    external_id: int | None = None

    model_config = {"from_attributes": True}
