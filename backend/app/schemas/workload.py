from datetime import date
from pydantic import BaseModel


class RecentWorklogItem(BaseModel):
    work_date: date
    km: float
    worked: bool
    week_label: str | None = None
    programs_10km: int
    programs_3km: int
    main_role: str | None = None
    status: str | None = None
    notes: str | None = None


class DogWorkloadSummary(BaseModel):
    dog_id: int
    dog_name: str

    total_worklogs: int
    worked_days: int
    total_km: float
    average_km_per_worked_day: float

    last_work_date: date | None = None
    last_day_km: float
    days_since_last_run: int | None = None

    worked_days_7d: int
    worked_days_14d: int

    km_3d: float
    km_7d: float
    km_14d: float

    recent_avg_km_per_worked_day_7d: float
    load_vs_own_average_ratio: float
    last_day_vs_own_average_ratio: float

    hard_day_km_threshold: float
    hard_days_count: int
    current_hard_streak: int

    recent_worklogs: list[RecentWorklogItem]