from datetime import date

from pydantic import BaseModel


class WorklogBase(BaseModel):
    dog_id: int
    work_date: date
    week: str | None = None
    weekday: str | None = None
    km: float = 0
    worked: bool = False
    programs_10km: int = 0
    programs_3km: int = 0
    main_role: str | None = None
    role_used: str | None = None
    notes: str | None = None


class WorklogCreate(WorklogBase):
    pass


class WorklogRead(WorklogBase):
    id: int

    model_config = {"from_attributes": True}
