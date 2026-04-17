from datetime import date
from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    as_of_date: date | None = None
    total_dogs: int
    active_dogs: int
    eligible_dogs: int
    high_risk_dogs: int
    moderate_risk_dogs: int
    underused_dogs: int
    worked_today_dogs: int
    total_km_today: float


class TodayDogStat(BaseModel):
    dog_id: int
    dog_name: str
    kennel_row: str | None = None
    kennel_block: int | None = None
    home_slot: int | None = None
    primary_role: str | None = None
    worked_today: bool
    km_today: float
    runs_today: int
    risk_level: str
    usage_level: str


class DashboardTodayResponse(BaseModel):
    as_of_date: date | None = None
    total_km_today: float
    worked_today_dogs: int
    items: list[TodayDogStat]


class HeatmapCell(BaseModel):
    dog_id: int
    dog_name: str
    kennel_row: str | None = None
    kennel_block: int | None = None
    home_slot: int | None = None
    worked_today: bool
    km_today: float
    risk_level: str
    availability_status: str
    lifecycle_status: str


class DashboardHeatmapResponse(BaseModel):
    as_of_date: date | None = None
    items: list[HeatmapCell]