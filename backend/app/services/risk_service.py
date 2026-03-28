from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.risk import DogRiskSummary, RiskMetrics
from app.services.workload_service import get_dog_workload_summary


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


def get_dog_risk_summary(
    db: Session,
    dog_id: int,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
) -> DogRiskSummary | None:
    dog = db.execute(select(Dog).where(Dog.id == dog_id)).scalar_one_or_none()
    if dog is None:
        return None

    workload = get_dog_workload_summary(
        db=db,
        dog_id=dog_id,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )
    if workload is None:
        return None

    age_years_estimate = _estimate_age(workload.last_work_date, dog.birth_year)
    age_group = _get_age_group(age_years_estimate)

    is_prime_age = age_group == "prime"
    is_aging = age_group == "aging"
    is_senior = age_group == "senior"

    flags: list[str] = []
    explanations: list[str] = []
    risk_score = 0

    # ---------------------------
    # Base load / fatigue-style rules
    # ---------------------------

    if workload.last_day_km >= hard_day_km_threshold:
        flags.append("hard_last_day")
        explanations.append("Last work day reached or exceeded the hard-day distance threshold.")
        risk_score += 1

    if workload.current_hard_streak >= 3:
        flags.append("hard_streak")
        explanations.append("The dog has three or more hard days in a row.")
        risk_score += 2
    elif workload.current_hard_streak == 2:
        flags.append("two_hard_days_in_a_row")
        explanations.append("The dog has two consecutive hard work days.")
        risk_score += 1

    if workload.km_7d >= 60:
        flags.append("high_7d_load")
        explanations.append("7-day workload is high in absolute terms.")
        risk_score += 2
    elif workload.km_7d >= 45:
        flags.append("elevated_7d_load")
        explanations.append("7-day workload is elevated.")
        risk_score += 1

    if workload.km_14d >= 140:
        flags.append("high_14d_load")
        explanations.append("14-day workload is high and may indicate cumulative strain.")
        risk_score += 1

    if workload.load_vs_own_average_ratio >= 1.5:
        flags.append("above_own_average_load")
        explanations.append("Recent workload is much higher than this dog's own historical average.")
        risk_score += 2
    elif workload.load_vs_own_average_ratio >= 1.25:
        flags.append("moderately_above_own_average")
        explanations.append("Recent workload is above this dog's usual average.")
        risk_score += 1

    if workload.last_day_vs_own_average_ratio >= 1.75:
        flags.append("very_heavy_last_day_for_this_dog")
        explanations.append("Last day load was much heavier than this dog's typical worked day.")
        risk_score += 2
    elif workload.last_day_vs_own_average_ratio >= 1.4:
        flags.append("heavy_last_day_for_this_dog")
        explanations.append("Last day load was heavier than usual for this dog.")
        risk_score += 1

    # Dense working pattern: a lot of active days in a short period
    if workload.worked_days_7d >= 6:
        flags.append("dense_working_week")
        explanations.append("The dog has worked on most days of the last 7-day period.")
        risk_score += 1

    # Recovery / cumulative load note:
    # a rest day does not erase a heavy recent block
    if workload.last_day_km == 0 and workload.km_7d >= 50:
        flags.append("recent_heavy_block_despite_rest_day")
        explanations.append("The latest day was a rest day, but the recent 7-day workload remains high.")
        risk_score += 1

    # ---------------------------
    # Age-sensitive adjustments
    # ---------------------------

    if is_aging:
        if workload.last_day_km >= 23:
            flags.append("aging_dog_high_single_day_load")
            explanations.append("Aging dog recorded a high single-day distance.")
            risk_score += 2
        elif workload.last_day_km >= 20:
            flags.append("aging_dog_elevated_single_day_load")
            explanations.append("Aging dog recorded an elevated single-day distance.")
            risk_score += 1

        if workload.km_7d >= 50:
            flags.append("aging_dog_high_recent_load")
            explanations.append("Aging dog has elevated recent workload.")
            risk_score += 2
        elif workload.km_7d >= 40:
            flags.append("aging_dog_moderate_recent_load")
            explanations.append("Aging dog has moderate recent workload that may need attention.")
            risk_score += 1

        if workload.worked_days_7d >= 5:
            flags.append("aging_dog_dense_schedule")
            explanations.append("Aging dog has worked frequently in the last 7 days.")
            risk_score += 1

    if is_senior:
        if workload.last_day_km >= 20:
            flags.append("senior_dog_high_single_day_load")
            explanations.append("Senior dog recorded a high single-day distance.")
            risk_score += 2
        elif workload.last_day_km >= 17:
            flags.append("senior_dog_elevated_single_day_load")
            explanations.append("Senior dog recorded an elevated single-day distance.")
            risk_score += 1

        if workload.km_7d >= 40:
            flags.append("senior_dog_high_recent_load")
            explanations.append("Senior dog has elevated recent workload.")
            risk_score += 2
        elif workload.km_7d >= 30:
            flags.append("senior_dog_moderate_recent_load")
            explanations.append("Senior dog has moderate recent workload that may need attention.")
            risk_score += 1

        if workload.worked_days_7d >= 4:
            flags.append("senior_dog_dense_schedule")
            explanations.append("Senior dog has worked frequently in the last 7 days.")
            risk_score += 1

    # ---------------------------
    # Usage / underuse signals
    # ---------------------------

    usage_level = "normal"

    if workload.days_since_last_run is not None and workload.days_since_last_run >= 5:
        flags.append("long_idle_period")
        explanations.append("The dog has not run for several days.")
        usage_level = "underused"

    if workload.worked_days_14d <= 2:
        flags.append("very_low_recent_usage")
        explanations.append("The dog has had very few working days in the last 14 days.")
        usage_level = "underused"

    if age_group == "young" and workload.worked_days_14d <= 2:
        flags.append("young_dog_low_usage_context")
        explanations.append("Low usage may be normal for a very young dog or a dog with operational constraints.")

    # ---------------------------
    # Final risk level calibration
    # ---------------------------

    if risk_score >= 6:
        risk_level = "high"
    elif risk_score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Safety bump:
    # don't keep aging/senior dogs at low risk when there is already
    # an explicit age-related load warning.
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

    metrics = RiskMetrics(
        last_day_km=workload.last_day_km,
        km_3d=workload.km_3d,
        km_7d=workload.km_7d,
        km_14d=workload.km_14d,
        worked_days_7d=workload.worked_days_7d,
        worked_days_14d=workload.worked_days_14d,
        days_since_last_run=workload.days_since_last_run,
        average_km_per_worked_day=workload.average_km_per_worked_day,
        recent_avg_km_per_worked_day_7d=workload.recent_avg_km_per_worked_day_7d,
        load_vs_own_average_ratio=workload.load_vs_own_average_ratio,
        last_day_vs_own_average_ratio=workload.last_day_vs_own_average_ratio,
        current_hard_streak=workload.current_hard_streak,
        hard_days_count=workload.hard_days_count,
        age_years_estimate=age_years_estimate,
        age_group=age_group,
        is_prime_age=is_prime_age,
        is_aging=is_aging,
        is_senior=is_senior,
    )

    return DogRiskSummary(
        dog_id=dog.id,
        dog_name=dog.name,
        risk_level=risk_level,
        usage_level=usage_level,
        flags=flags,
        explanations=explanations,
        metrics=metrics,
    )