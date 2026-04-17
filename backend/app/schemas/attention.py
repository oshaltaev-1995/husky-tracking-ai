from pydantic import BaseModel


class DogAttentionItem(BaseModel):
    dog_id: int
    dog_name: str

    attention_level: str
    eligible_for_team_builder: bool

    risk_level: str
    usage_level: str

    lifecycle_status: str
    availability_status: str
    exclude_from_team_builder: bool
    exclude_reason: str | None = None

    reasons: list[str]
    suggested_action: str


class DogAttentionListResponse(BaseModel):
    total_items: int
    items: list[DogAttentionItem]