from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog
from app.schemas.dashboard import (
    DashboardHeatmapResponse,
    DashboardOverviewResponse,
    DashboardTodayResponse,
    HeatmapCell,
    TodayDogStat,
)
from app.services.eligibility_service import (
    get_team_builder_eligibility,
    is_operationally_available,
)
from app.services.risk_service import get_dog_risk_summary


def _as_str(value) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _get_latest_work_date(db: Session) -> date | None:
    worklogs = list(db.execute(select(Worklog).order_by(Worklog.work_date.desc())).scalars().all())
    if not worklogs:
        return None
    return worklogs[0].work_date


def _get_today_logs_map(db: Session, as_of_date: date) -> dict[int, list[Worklog]]:
    rows = list(
        db.execute(
            select(Worklog).where(Worklog.work_date == as_of_date).order_by(Worklog.dog_id.asc())
        ).scalars().all()
    )
    result: dict[int, list[Worklog]] = defaultdict(list)
    for row in rows:
        result[row.dog_id].append(row)
    return result


def _is_operational_dog(dog: Dog) -> bool:
    lifecycle = _as_str(dog.lifecycle_status).lower()
    return lifecycle not in {"archived", "deceased"}


def get_dashboard_overview(db: Session, as_of_date: date | None = None) -> DashboardOverviewResponse:
    if as_of_date is None:
        as_of_date = _get_latest_work_date(db)

    all_dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())
    dogs = [dog for dog in all_dogs if _is_operational_dog(dog)]

    today_logs_map = _get_today_logs_map(db, as_of_date) if as_of_date else {}

    active_dogs = 0
    eligible_dogs = 0
    high_risk_dogs = 0
    moderate_risk_dogs = 0
    underused_dogs = 0
    worked_today_dogs = 0
    total_km_today = 0.0

    for dog in dogs:
        if _as_str(dog.lifecycle_status).lower() == "active":
            active_dogs += 1

        eligibility = get_team_builder_eligibility(dog, as_of_date)
        operationally_available = is_operationally_available(dog, as_of_date)

        if eligibility.eligible_for_team_builder:
            eligible_dogs += 1

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=15.0,
            recent_days=14,
            as_of_date=as_of_date,
        )
        if risk and operationally_available and eligibility.eligible_for_team_builder:
            if risk.risk_level == "high":
                high_risk_dogs += 1
            elif risk.risk_level == "moderate":
                moderate_risk_dogs += 1

            if risk.usage_level == "underused":
                underused_dogs += 1

        today_logs = today_logs_map.get(dog.id, [])
        km_today = sum(float(w.km or 0) for w in today_logs)
        worked_today = any(w.worked for w in today_logs)

        if worked_today:
            worked_today_dogs += 1
        total_km_today += km_today

    return DashboardOverviewResponse(
        as_of_date=as_of_date,
        total_dogs=len(dogs),
        active_dogs=active_dogs,
        eligible_dogs=eligible_dogs,
        high_risk_dogs=high_risk_dogs,
        moderate_risk_dogs=moderate_risk_dogs,
        underused_dogs=underused_dogs,
        worked_today_dogs=worked_today_dogs,
        total_km_today=round(total_km_today, 2),
    )


def get_dashboard_today(db: Session, as_of_date: date | None = None) -> DashboardTodayResponse:
    if as_of_date is None:
        as_of_date = _get_latest_work_date(db)

    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())
    today_logs_map = _get_today_logs_map(db, as_of_date) if as_of_date else {}

    items: list[TodayDogStat] = []
    total_km_today = 0.0
    worked_today_dogs = 0

    for dog in dogs:
        logs = today_logs_map.get(dog.id, [])
        km_today = round(sum(float(w.km or 0) for w in logs), 2)
        runs_today = sum(int(w.programs_10km or 0) + int(w.programs_3km or 0) for w in logs)
        worked_today = any(w.worked for w in logs)

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=15.0,
            recent_days=14,
            as_of_date=as_of_date,
        )

        if worked_today:
            worked_today_dogs += 1
        total_km_today += km_today

        items.append(
            TodayDogStat(
                dog_id=dog.id,
                dog_name=dog.name,
                kennel_row=dog.kennel_row,
                kennel_block=dog.kennel_block,
                home_slot=dog.home_slot,
                primary_role=dog.primary_role,
                worked_today=worked_today,
                km_today=km_today,
                runs_today=runs_today,
                risk_level=risk.risk_level if risk else "unknown",
                usage_level=risk.usage_level if risk else "unknown",
            )
        )

    items.sort(key=lambda x: (-x.km_today, x.dog_name))

    return DashboardTodayResponse(
        as_of_date=as_of_date,
        total_km_today=round(total_km_today, 2),
        worked_today_dogs=worked_today_dogs,
        items=items,
    )


def get_dashboard_heatmap(db: Session, as_of_date: date | None = None) -> DashboardHeatmapResponse:
    if as_of_date is None:
        as_of_date = _get_latest_work_date(db)

    dogs = list(
        db.execute(
            select(Dog).order_by(Dog.kennel_row.asc(), Dog.home_slot.asc(), Dog.name.asc())
        ).scalars().all()
    )
    today_logs_map = _get_today_logs_map(db, as_of_date) if as_of_date else {}

    items: list[HeatmapCell] = []

    for dog in dogs:
        logs = today_logs_map.get(dog.id, [])
        km_today = round(sum(float(w.km or 0) for w in logs), 2)
        worked_today = any(w.worked for w in logs)

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=15.0,
            recent_days=14,
            as_of_date=as_of_date,
        )

        items.append(
            HeatmapCell(
                dog_id=dog.id,
                dog_name=dog.name,
                kennel_row=dog.kennel_row,
                kennel_block=dog.kennel_block,
                home_slot=dog.home_slot,
                worked_today=worked_today,
                km_today=km_today,
                risk_level=risk.risk_level if risk else "unknown",
                availability_status=_as_str(dog.availability_status),
                lifecycle_status=_as_str(dog.lifecycle_status),
            )
        )

    return DashboardHeatmapResponse(
        as_of_date=as_of_date,
        items=items,
    )