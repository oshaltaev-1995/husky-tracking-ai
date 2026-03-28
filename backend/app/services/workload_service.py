from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog
from app.schemas.workload import DogWorkloadSummary, RecentWorklogItem


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _estimate_age_years(birth_year: int | None, reference_date: date | None) -> int | None:
    if birth_year is None or reference_date is None:
        return None
    return reference_date.year - birth_year


def get_dog_workload_summary(
    db: Session,
    dog_id: int,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> DogWorkloadSummary | None:
    dog = db.execute(select(Dog).where(Dog.id == dog_id)).scalar_one_or_none()
    if dog is None:
        return None

    worklogs = list(
        db.execute(
            select(Worklog)
            .where(Worklog.dog_id == dog_id)
            .order_by(Worklog.work_date.asc(), Worklog.id.asc())
        ).scalars().all()
    )

    total_worklogs = len(worklogs)
    worked_logs = [w for w in worklogs if w.worked]
    worked_days = len(worked_logs)

    total_km = round(sum(_to_float(w.km) for w in worked_logs), 2)
    average_km_per_worked_day = round(total_km / worked_days, 2) if worked_days > 0 else 0.0

    last_worklog = worklogs[-1] if worklogs else None
    last_work_date = last_worklog.work_date if last_worklog else None
    last_day_km = round(_to_float(last_worklog.km), 2) if last_worklog else 0.0

    km_3d = 0.0
    km_7d = 0.0
    km_14d = 0.0
    worked_days_7d = 0
    worked_days_14d = 0
    days_since_last_run = None
    recent_avg_km_per_worked_day_7d = 0.0
    load_vs_own_average_ratio = 0.0
    last_day_vs_own_average_ratio = 0.0

    if last_work_date is not None:
        date_3d = last_work_date - timedelta(days=2)
        date_7d = last_work_date - timedelta(days=6)
        date_14d = last_work_date - timedelta(days=13)

        logs_3d = [w for w in worklogs if w.work_date >= date_3d]
        logs_7d = [w for w in worklogs if w.work_date >= date_7d]
        logs_14d = [w for w in worklogs if w.work_date >= date_14d]

        worked_logs_7d = [w for w in logs_7d if w.worked]
        worked_logs_14d = [w for w in logs_14d if w.worked]

        km_3d = round(sum(_to_float(w.km) for w in logs_3d), 2)
        km_7d = round(sum(_to_float(w.km) for w in logs_7d), 2)
        km_14d = round(sum(_to_float(w.km) for w in logs_14d), 2)

        worked_days_7d = len(worked_logs_7d)
        worked_days_14d = len(worked_logs_14d)

        if worked_days_7d > 0:
            recent_avg_km_per_worked_day_7d = round(
                km_7d / worked_days_7d,
                2,
            )

        if average_km_per_worked_day > 0:
            load_vs_own_average_ratio = round(
                recent_avg_km_per_worked_day_7d / average_km_per_worked_day,
                2,
            )
            last_day_vs_own_average_ratio = round(
                last_day_km / average_km_per_worked_day,
                2,
            )

        last_worked_log = worked_logs[-1] if worked_logs else None
        if last_worked_log is not None:
            days_since_last_run = (last_work_date - last_worked_log.work_date).days

    hard_days_count = sum(1 for w in worked_logs if _to_float(w.km) >= hard_day_km_threshold)

    current_hard_streak = 0
    for w in reversed(worklogs):
        if _to_float(w.km) >= hard_day_km_threshold:
            current_hard_streak += 1
        else:
            break

    recent_worklogs: list[RecentWorklogItem] = []
    if last_work_date is not None:
        recent_start = last_work_date - timedelta(days=recent_days - 1)
        recent_rows = [w for w in worklogs if w.work_date >= recent_start]

        recent_worklogs = [
            RecentWorklogItem(
                work_date=w.work_date,
                km=round(_to_float(w.km), 2),
                worked=w.worked,
                week_label=w.week_label,
                programs_10km=w.programs_10km,
                programs_3km=w.programs_3km,
                main_role=w.main_role,
                status=w.status,
                notes=w.notes,
            )
            for w in recent_rows
        ]

    return DogWorkloadSummary(
        dog_id=dog.id,
        dog_name=dog.name,
        total_worklogs=total_worklogs,
        worked_days=worked_days,
        total_km=total_km,
        average_km_per_worked_day=average_km_per_worked_day,
        last_work_date=last_work_date,
        last_day_km=last_day_km,
        days_since_last_run=days_since_last_run,
        worked_days_7d=worked_days_7d,
        worked_days_14d=worked_days_14d,
        km_3d=km_3d,
        km_7d=km_7d,
        km_14d=km_14d,
        recent_avg_km_per_worked_day_7d=recent_avg_km_per_worked_day_7d,
        load_vs_own_average_ratio=load_vs_own_average_ratio,
        last_day_vs_own_average_ratio=last_day_vs_own_average_ratio,
        hard_day_km_threshold=hard_day_km_threshold,
        hard_days_count=hard_days_count,
        current_hard_streak=current_hard_streak,
        recent_worklogs=recent_worklogs,
    )