from datetime import date
from pydantic import BaseModel


class WeeklyAnalyticsItem(BaseModel):
    week_start: date
    week_end: date
    week_label: str
    total_km: float
    worked_dogs: int
    avg_km_per_worked_dog: float
    high_risk_dogs: int
    moderate_risk_dogs: int
    underused_dogs: int


class WeeklyAnalyticsResponse(BaseModel):
    date_from: date
    date_to: date
    items: list[WeeklyAnalyticsItem]


class AnalyticsSummaryLatestWeek(BaseModel):
    week_start: date
    week_end: date
    week_label: str
    total_km: float
    worked_dogs: int
    avg_km_per_worked_dog: float
    high_risk_dogs: int
    moderate_risk_dogs: int
    underused_dogs: int


class AnalyticsSummaryResponse(BaseModel):
    date_from: date
    date_to: date
    weeks_count: int
    total_km: float
    total_worked_dog_days: int
    unique_worked_dogs: int
    avg_km_per_worked_dog: float
    latest_week_snapshot: AnalyticsSummaryLatestWeek | None = None


class WeeklyCompareDelta(BaseModel):
    total_km: float
    worked_dogs: int
    avg_km_per_worked_dog: float
    high_risk_dogs: int
    moderate_risk_dogs: int
    underused_dogs: int


class WeeklyCompareResponse(BaseModel):
    week_a: WeeklyAnalyticsItem
    week_b: WeeklyAnalyticsItem
    delta: WeeklyCompareDelta