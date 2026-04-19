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


class HarnessDog(BaseModel):
    dog_id: int
    dog_name: str
    primary_role: str | None = None
    assigned_role: str
    risk_level: str
    usage_level: str


class HarnessRow(BaseModel):
    row_role: str
    row_type: str  # "pair" | "single"
    relation: str | None = None  # forced_pair | home_pair | preferred_pair | allowed_pair | single_fallback
    dogs: list[HarnessDog]
    warnings: list[str] = []


class HarnessLayout(BaseModel):
    lead_rows: list[HarnessRow]
    team_rows: list[HarnessRow]
    wheel_rows: list[HarnessRow]


class SuggestedTeam(BaseModel):
    team_number: int
    dogs: list[TeamDogAssignment]
    layout: HarnessLayout
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