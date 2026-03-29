from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog


@dataclass
class RiskEvaluation:
    risk_level: str
    usage_level: str
    flags: list[str]


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _estimate_age(reference_date: date | None, birth_year: int | None) -> int | None:
    if reference_date is None or birth_year is None:
        return None
    return reference_date.year - birth_year


def _get_age_group(age_years: int | None) -> str | None:
    if age_years is None:
        return None
    if age_years <= 1:
        return "young"
    if 2 <= age_years <= 8:
        return "prime"
    if 9 <= age_years <= 11:
        return "aging"
    return "senior"


def _safe_ratio(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return round(a / b, 2)


def _build_features_for_dog_day(
    dog: Dog,
    dog_worklogs: list[Worklog],
    as_of_date: date,
    hard_day_km_threshold: float = 10.0,
) -> dict[str, Any]:
    logs_upto = [w for w in dog_worklogs if w.work_date <= as_of_date]
    logs_upto.sort(key=lambda x: (x.work_date, x.id))

    worked_logs = [w for w in logs_upto if w.worked]

    total_worklogs = len(logs_upto)
    worked_days_total = len(worked_logs)
    total_km = round(sum(_to_float(w.km) for w in worked_logs), 2)
    average_km_per_worked_day = round(total_km / worked_days_total, 2) if worked_days_total > 0 else 0.0

    current_day_logs = [w for w in logs_upto if w.work_date == as_of_date]
    current_day_worked = any(w.worked for w in current_day_logs)
    current_day_km = round(sum(_to_float(w.km) for w in current_day_logs), 2)

    date_3d = as_of_date - timedelta(days=2)
    date_7d = as_of_date - timedelta(days=6)
    date_14d = as_of_date - timedelta(days=13)

    logs_3d = [w for w in logs_upto if w.work_date >= date_3d]
    logs_7d = [w for w in logs_upto if w.work_date >= date_7d]
    logs_14d = [w for w in logs_upto if w.work_date >= date_14d]

    worked_logs_3d = [w for w in logs_3d if w.worked]
    worked_logs_7d = [w for w in logs_7d if w.worked]
    worked_logs_14d = [w for w in logs_14d if w.worked]

    km_3d = round(sum(_to_float(w.km) for w in logs_3d), 2)
    km_7d = round(sum(_to_float(w.km) for w in logs_7d), 2)
    km_14d = round(sum(_to_float(w.km) for w in logs_14d), 2)

    worked_days_3d = len(worked_logs_3d)
    worked_days_7d = len(worked_logs_7d)
    worked_days_14d = len(worked_logs_14d)

    recent_avg_km_per_worked_day_7d = round(km_7d / worked_days_7d, 2) if worked_days_7d > 0 else 0.0
    load_vs_own_average_ratio = _safe_ratio(recent_avg_km_per_worked_day_7d, average_km_per_worked_day)
    last_day_vs_own_average_ratio = _safe_ratio(current_day_km, average_km_per_worked_day)

    hard_days_count_total = sum(1 for w in worked_logs if _to_float(w.km) >= hard_day_km_threshold)

    current_hard_streak = 0
    for w in reversed(logs_upto):
        if _to_float(w.km) >= hard_day_km_threshold:
            current_hard_streak += 1
        else:
            break

    last_worked_log = worked_logs[-1] if worked_logs else None
    days_since_last_run = None
    if last_worked_log is not None:
        days_since_last_run = (as_of_date - last_worked_log.work_date).days

    age_years_estimate = _estimate_age(as_of_date, dog.birth_year)
    age_group = _get_age_group(age_years_estimate)

    return {
        "date": as_of_date,
        "dog_id": dog.id,
        "dog_name": dog.name,
        "external_id": dog.external_id,
        "birth_year": dog.birth_year,
        "age_years_estimate": age_years_estimate,
        "age_group": age_group,
        "is_prime_age": age_group == "prime",
        "is_aging": age_group == "aging",
        "is_senior": age_group == "senior",
        "sex": dog.sex,
        "kennel_row": dog.kennel_row,
        "kennel_block": dog.kennel_block,
        "home_slot": dog.home_slot,
        "primary_role": dog.primary_role,
        "can_lead": dog.can_lead,
        "can_team": dog.can_team,
        "can_wheel": dog.can_wheel,
        "status": dog.status,
        "is_active": dog.is_active,
        "current_day_worked": current_day_worked,
        "current_day_km": current_day_km,
        "total_worklogs_so_far": total_worklogs,
        "worked_days_total": worked_days_total,
        "total_km_so_far": total_km,
        "average_km_per_worked_day": average_km_per_worked_day,
        "km_3d": km_3d,
        "km_7d": km_7d,
        "km_14d": km_14d,
        "worked_days_3d": worked_days_3d,
        "worked_days_7d": worked_days_7d,
        "worked_days_14d": worked_days_14d,
        "recent_avg_km_per_worked_day_7d": recent_avg_km_per_worked_day_7d,
        "load_vs_own_average_ratio": load_vs_own_average_ratio,
        "last_day_vs_own_average_ratio": last_day_vs_own_average_ratio,
        "current_hard_streak": current_hard_streak,
        "hard_days_count_total": hard_days_count_total,
        "days_since_last_run": days_since_last_run,
        "hard_day_km_threshold": hard_day_km_threshold,
    }


def _evaluate_risk_from_features(features: dict[str, Any]) -> RiskEvaluation:
    flags: list[str] = []
    risk_score = 0

    current_day_km = float(features["current_day_km"])
    km_7d = float(features["km_7d"])
    km_14d = float(features["km_14d"])
    worked_days_7d = int(features["worked_days_7d"])
    worked_days_14d = int(features["worked_days_14d"])
    load_vs_avg = float(features["load_vs_own_average_ratio"])
    last_day_vs_avg = float(features["last_day_vs_own_average_ratio"])
    current_hard_streak = int(features["current_hard_streak"])
    days_since_last_run = features["days_since_last_run"]
    hard_day_km_threshold = float(features["hard_day_km_threshold"])

    is_aging = bool(features["is_aging"])
    is_senior = bool(features["is_senior"])
    age_group = features["age_group"]

    if current_day_km >= hard_day_km_threshold:
        flags.append("hard_last_day")
        risk_score += 1

    if current_hard_streak >= 3:
        flags.append("hard_streak")
        risk_score += 2
    elif current_hard_streak == 2:
        flags.append("two_hard_days_in_a_row")
        risk_score += 1

    if km_7d >= 60:
        flags.append("high_7d_load")
        risk_score += 2
    elif km_7d >= 45:
        flags.append("elevated_7d_load")
        risk_score += 1

    if km_14d >= 140:
        flags.append("high_14d_load")
        risk_score += 1

    if load_vs_avg >= 1.5:
        flags.append("above_own_average_load")
        risk_score += 2
    elif load_vs_avg >= 1.25:
        flags.append("moderately_above_own_average")
        risk_score += 1

    if last_day_vs_avg >= 1.75:
        flags.append("very_heavy_last_day_for_this_dog")
        risk_score += 2
    elif last_day_vs_avg >= 1.4:
        flags.append("heavy_last_day_for_this_dog")
        risk_score += 1

    if worked_days_7d >= 6:
        flags.append("dense_working_week")
        risk_score += 1

    if current_day_km == 0 and km_7d >= 50:
        flags.append("recent_heavy_block_despite_rest_day")
        risk_score += 1

    if is_aging:
        if current_day_km >= 23:
            flags.append("aging_dog_high_single_day_load")
            risk_score += 2
        elif current_day_km >= 20:
            flags.append("aging_dog_elevated_single_day_load")
            risk_score += 1

        if km_7d >= 50:
            flags.append("aging_dog_high_recent_load")
            risk_score += 2
        elif km_7d >= 40:
            flags.append("aging_dog_moderate_recent_load")
            risk_score += 1

        if worked_days_7d >= 5:
            flags.append("aging_dog_dense_schedule")
            risk_score += 1

    if is_senior:
        if current_day_km >= 20:
            flags.append("senior_dog_high_single_day_load")
            risk_score += 2
        elif current_day_km >= 17:
            flags.append("senior_dog_elevated_single_day_load")
            risk_score += 1

        if km_7d >= 40:
            flags.append("senior_dog_high_recent_load")
            risk_score += 2
        elif km_7d >= 30:
            flags.append("senior_dog_moderate_recent_load")
            risk_score += 1

        if worked_days_7d >= 4:
            flags.append("senior_dog_dense_schedule")
            risk_score += 1

    usage_level = "normal"

    if days_since_last_run is not None and days_since_last_run >= 5:
        flags.append("long_idle_period")
        usage_level = "underused"

    if worked_days_14d <= 2:
        flags.append("very_low_recent_usage")
        usage_level = "underused"

    if age_group == "young" and worked_days_14d <= 2:
        flags.append("young_dog_low_usage_context")

    if risk_score >= 6:
        risk_level = "high"
    elif risk_score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    aging_or_senior_warning = any(
        flag in flags
        for flag in {
            "aging_dog_high_single_day_load",
            "aging_dog_elevated_single_day_load",
            "aging_dog_high_recent_load",
            "aging_dog_moderate_recent_load",
            "aging_dog_dense_schedule",
            "senior_dog_high_single_day_load",
            "senior_dog_elevated_single_day_load",
            "senior_dog_high_recent_load",
            "senior_dog_moderate_recent_load",
            "senior_dog_dense_schedule",
        }
    )
    if risk_level == "low" and aging_or_senior_warning:
        risk_level = "moderate"

    return RiskEvaluation(
        risk_level=risk_level,
        usage_level=usage_level,
        flags=flags,
    )


def build_next_day_ml_dataset(
    db: Session,
    output_path: Path,
    hard_day_km_threshold: float = 10.0,
) -> pd.DataFrame:
    dogs = list(db.execute(select(Dog).order_by(Dog.id.asc())).scalars().all())
    all_worklogs = list(
        db.execute(
            select(Worklog).order_by(Worklog.dog_id.asc(), Worklog.work_date.asc(), Worklog.id.asc())
        ).scalars().all()
    )

    worklogs_by_dog: dict[int, list[Worklog]] = {}
    for w in all_worklogs:
        worklogs_by_dog.setdefault(w.dog_id, []).append(w)

    rows: list[dict[str, Any]] = []

    for dog in dogs:
        dog_worklogs = worklogs_by_dog.get(dog.id, [])
        if len(dog_worklogs) < 2:
            continue

        unique_dates = sorted({w.work_date for w in dog_worklogs})
        if len(unique_dates) < 2:
            continue

        # features from day t, target from day t+1
        for idx in range(len(unique_dates) - 1):
            current_date = unique_dates[idx]
            next_date = unique_dates[idx + 1]

            features = _build_features_for_dog_day(
                dog=dog,
                dog_worklogs=dog_worklogs,
                as_of_date=current_date,
                hard_day_km_threshold=hard_day_km_threshold,
            )

            next_day_features = _build_features_for_dog_day(
                dog=dog,
                dog_worklogs=dog_worklogs,
                as_of_date=next_date,
                hard_day_km_threshold=hard_day_km_threshold,
            )

            next_day_risk = _evaluate_risk_from_features(next_day_features)

            features["target_date"] = next_date
            features["target_next_day_risk_level"] = next_day_risk.risk_level
            features["target_next_day_usage_level"] = next_day_risk.usage_level
            features["target_next_day_flag_count"] = len(next_day_risk.flags)
            features["target_next_day_flags"] = "|".join(next_day_risk.flags)

            rows.append(features)

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df