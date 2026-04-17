from pydantic import BaseModel, Field


class TeamBuilderRequest(BaseModel):
    program_type: str = Field(..., examples=["3km", "10km"])
    sled_type: str = Field(..., examples=["T6", "big_sled"])
    team_count: int = Field(..., ge=1, le=50)

    min_dogs_per_team: int = Field(..., ge=4, le=10)
    max_dogs_per_team: int = Field(..., ge=4, le=10)

    avoid_high_risk: bool = True
    prefer_underused: bool = True


class TeamDogAssignment(BaseModel):
    dog_id: int
    dog_name: str
    primary_role: str | None = None
    assigned_role: str
    risk_level: str
    usage_level: str


class SuggestedTeam(BaseModel):
    team_number: int
    dogs: list[TeamDogAssignment]
    warnings: list[str]


class ExcludedDog(BaseModel):
    dog_id: int
    dog_name: str
    reasons: list[str]


class TeamBuilderResponse(BaseModel):
    request: TeamBuilderRequest
    teams: list[SuggestedTeam]
    unassigned_dogs: list[TeamDogAssignment]
    excluded_dogs: list[ExcludedDog]
    global_warnings: list[str]