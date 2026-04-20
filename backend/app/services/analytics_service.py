from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog
from app.models.enums import LifecycleStatus
from app.schemas.analytics import (
    AnalyticsSummaryLatestWeek,
    AnalyticsSummaryResponse,
    WeeklyAnalyticsItem,
    WeeklyAnalyticsResponse,
    WeeklyCompareDelta,
    WeeklyCompareResponse,
)
from app.services.eligibility_service import (
    get_team_builder_eligibility,
    is_operationally_available,
)
from app.services.risk_service import get_dog_risk_summary


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _start_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _end_of_week(value: date) -> date:
    return _start_of_week(value) + timedelta(days=6)


def _week_label(week_start: date, week_end: date) -> str:
    return f"{week_start.isoformat()} → {week_end.isoformat()}"


def _iter_weeks(date_from: date, date_to: date) -> list[tuple[date, date]]:
    normalized_start = _start_of_week(date_from)
    normalized_end = _end_of_week(date_to)

    weeks: list[tuple[date, date]] = []
    cursor = normalized_start
    while cursor <= normalized_end:
        week_start = cursor
        week_end = cursor + timedelta(days=6)
        weeks.append((week_start, week_end))
        cursor += timedelta(days=7)

    return weeks


def _get_operational_dogs(db: Session) -> list[Dog]:
    rows = db.execute(
        select(Dog)
        .where(
            Dog.is_active.is_(True),
            Dog.lifecycle_status.notin_(
                [LifecycleStatus.archived.value, LifecycleStatus.deceased.value]
            ),
        )
        .order_by(Dog.name.asc())
    ).scalars().all()

    return list(rows)


def _get_worklogs_in_range(db: Session, date_from: date, date_to: date) -> list[Worklog]:
    rows = db.execute(
        select(Worklog)
        .where(
            Worklog.work_date >= date_from,
            Worklog.work_date <= date_to,
        )
        .order_by(Worklog.work_date.asc(), Worklog.dog_id.asc(), Worklog.id.asc())
    ).scalars().all()

    return list(rows)


def _compute_week_base_metrics(worklogs: list[Worklog]) -> tuple[float, int, float]:
    worked_logs = [row for row in worklogs if row.worked]

    total_km = round(sum(_to_float(row.km) for row in worked_logs), 2)
    worked_dog_ids = {row.dog_id for row in worked_logs}
    worked_dogs = len(worked_dog_ids)
    avg_km_per_worked_dog = round(total_km / worked_dogs, 2) if worked_dogs > 0 else 0.0

    return total_km, worked_dogs, avg_km_per_worked_dog


def _is_dashboard_snapshot_candidate(dog: Dog, week_end: date) -> bool:
    eligibility = get_team_builder_eligibility(dog, week_end)
    operationally_available = is_operationally_available(dog, week_end)
    return operationally_available and eligibility.eligible_for_team_builder


def _compute_week_snapshot_metrics(
    db: Session,
    dogs: list[Dog],
    week_end: date,
    hard_day_km_threshold: float,
    recent_days: int,
) -> tuple[int, int, int]:
    high_risk_dogs = 0
    moderate_risk_dogs = 0
    underused_dogs = 0

    for dog in dogs:
        if not _is_dashboard_snapshot_candidate(dog, week_end):
            continue

        summary = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
            as_of_date=week_end,
        )
        if summary is None:
            continue

        if summary.risk_level == "high":
            high_risk_dogs += 1
        elif summary.risk_level == "moderate":
            moderate_risk_dogs += 1

        if summary.usage_level == "underused":
            underused_dogs += 1

    return high_risk_dogs, moderate_risk_dogs, underused_dogs


def get_weekly_analytics(
    db: Session,
    date_from: date,
    date_to: date,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> WeeklyAnalyticsResponse:
    weeks = _iter_weeks(date_from=date_from, date_to=date_to)
    normalized_start = weeks[0][0]
    normalized_end = weeks[-1][1]

    worklogs = _get_worklogs_in_range(db=db, date_from=normalized_start, date_to=normalized_end)
    dogs = _get_operational_dogs(db=db)

    by_week: dict[date, list[Worklog]] = defaultdict(list)

    for row in worklogs:
        bucket_start = _start_of_week(row.work_date)
        by_week[bucket_start].append(row)

    items: list[WeeklyAnalyticsItem] = []

    for week_start, week_end in weeks:
        week_rows = by_week.get(week_start, [])

        total_km, worked_dogs, avg_km_per_worked_dog = _compute_week_base_metrics(week_rows)

        high_risk_dogs, moderate_risk_dogs, underused_dogs = _compute_week_snapshot_metrics(
            db=db,
            dogs=dogs,
            week_end=week_end,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
        )

        items.append(
            WeeklyAnalyticsItem(
                week_start=week_start,
                week_end=week_end,
                week_label=_week_label(week_start, week_end),
                total_km=total_km,
                worked_dogs=worked_dogs,
                avg_km_per_worked_dog=avg_km_per_worked_dog,
                high_risk_dogs=high_risk_dogs,
                moderate_risk_dogs=moderate_risk_dogs,
                underused_dogs=underused_dogs,
            )
        )

    return WeeklyAnalyticsResponse(
        date_from=normalized_start,
        date_to=normalized_end,
        items=items,
    )


def get_analytics_summary(
    db: Session,
    date_from: date,
    date_to: date,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> AnalyticsSummaryResponse:
    weekly = get_weekly_analytics(
        db=db,
        date_from=date_from,
        date_to=date_to,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )

    all_rows = _get_worklogs_in_range(
        db=db,
        date_from=weekly.date_from,
        date_to=weekly.date_to,
    )

    worked_rows = [row for row in all_rows if row.worked]
    total_km = round(sum(_to_float(row.km) for row in worked_rows), 2)
    total_worked_dog_days = len(worked_rows)
    unique_worked_dogs = len({row.dog_id for row in worked_rows})
    avg_km_per_worked_dog = round(total_km / unique_worked_dogs, 2) if unique_worked_dogs > 0 else 0.0

    latest_week_snapshot = None
    if weekly.items:
        latest = weekly.items[-1]
        latest_week_snapshot = AnalyticsSummaryLatestWeek(
            week_start=latest.week_start,
            week_end=latest.week_end,
            week_label=latest.week_label,
            total_km=latest.total_km,
            worked_dogs=latest.worked_dogs,
            avg_km_per_worked_dog=latest.avg_km_per_worked_dog,
            high_risk_dogs=latest.high_risk_dogs,
            moderate_risk_dogs=latest.moderate_risk_dogs,
            underused_dogs=latest.underused_dogs,
        )

    return AnalyticsSummaryResponse(
        date_from=weekly.date_from,
        date_to=weekly.date_to,
        weeks_count=len(weekly.items),
        total_km=total_km,
        total_worked_dog_days=total_worked_dog_days,
        unique_worked_dogs=unique_worked_dogs,
        avg_km_per_worked_dog=avg_km_per_worked_dog,
        latest_week_snapshot=latest_week_snapshot,
    )


def _get_single_week_item(
    db: Session,
    week_start: date,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> WeeklyAnalyticsItem:
    weekly = get_weekly_analytics(
        db=db,
        date_from=week_start,
        date_to=week_start,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )
    return weekly.items[0]


def get_weekly_compare(
    db: Session,
    week_a_start: date,
    week_b_start: date,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> WeeklyCompareResponse:
    week_a = _get_single_week_item(
        db=db,
        week_start=week_a_start,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )
    week_b = _get_single_week_item(
        db=db,
        week_start=week_b_start,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )

    delta = WeeklyCompareDelta(
        total_km=round(week_b.total_km - week_a.total_km, 2),
        worked_dogs=week_b.worked_dogs - week_a.worked_dogs,
        avg_km_per_worked_dog=round(
            week_b.avg_km_per_worked_dog - week_a.avg_km_per_worked_dog,
            2,
        ),
        high_risk_dogs=week_b.high_risk_dogs - week_a.high_risk_dogs,
        moderate_risk_dogs=week_b.moderate_risk_dogs - week_a.moderate_risk_dogs,
        underused_dogs=week_b.underused_dogs - week_a.underused_dogs,
    )

    return WeeklyCompareResponse(
        week_a=week_a,
        week_b=week_b,
        delta=delta,
    )