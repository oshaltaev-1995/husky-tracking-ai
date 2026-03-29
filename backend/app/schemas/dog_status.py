from pydantic import BaseModel

from app.models.enums import AvailabilityStatus, LifecycleStatus


class DogStatusUpdate(BaseModel):
    lifecycle_status: LifecycleStatus | None = None
    availability_status: AvailabilityStatus | None = None
    exclude_from_team_builder: bool | None = None
    exclude_reason: str | None = None


class DogEligibilityRead(BaseModel):
    dog_id: int
    dog_name: str
    eligible_for_team_builder: bool
    reasons: list[str]