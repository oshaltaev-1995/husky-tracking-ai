from pydantic import BaseModel


class RiskMetrics(BaseModel):
    last_day_km: float
    km_3d: float
    km_7d: float
    km_14d: float
    worked_days_7d: int
    worked_days_14d: int
    days_since_last_run: int | None = None
    average_km_per_worked_day: float
    recent_avg_km_per_worked_day_7d: float
    load_vs_own_average_ratio: float
    last_day_vs_own_average_ratio: float
    current_hard_streak: int
    hard_days_count: int
    age_years_estimate: int | None = None
    age_group: str | None = None
    is_prime_age: bool
    is_aging: bool
    is_senior: bool


class DogRiskSummary(BaseModel):
    dog_id: int
    dog_name: str
    risk_level: str
    usage_level: str
    flags: list[str]
    explanations: list[str]
    metrics: RiskMetrics