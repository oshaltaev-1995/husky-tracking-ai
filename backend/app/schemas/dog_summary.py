from pydantic import BaseModel, ConfigDict

from app.schemas.dog import DogRead


class DogSummaryRead(BaseModel):
    dog: DogRead
    eligible_for_team_builder: bool
    eligibility_reasons: list[str]
    risk_level: str
    usage_level: str | None = None

    model_config = ConfigDict(from_attributes=True)