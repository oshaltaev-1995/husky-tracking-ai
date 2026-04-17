from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.attention import DogAttentionItem, DogAttentionListResponse
from app.services.eligibility_service import (
    get_team_builder_eligibility,
    is_operationally_available,
)
from app.services.risk_service import get_dog_risk_summary


def _as_str(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _is_temporary_planning_blocker(dog: Dog) -> bool:
    lifecycle_status = _as_str(dog.lifecycle_status).strip().lower()
    availability_status = _as_str(dog.availability_status).strip().lower()
    exclude_reason = (dog.exclude_reason or "").strip().lower()

    if lifecycle_status != "active":
        return False

    if "too young" in exclude_reason:
        return False

    if availability_status != "available":
        return True

    if dog.exclude_from_team_builder:
        return True

    return False


def _build_suggested_action(
    eligible: bool,
    risk_level: str,
    usage_level: str,
    availability_status: str,
    exclude_from_team_builder: bool,
    blocker_reasons: list[str] | None = None,
) -> str:
    blocker_reasons = blocker_reasons or []

    if not eligible:
        if availability_status != "available":
            return "Do not use in team builder until availability issue is resolved."
        if exclude_from_team_builder:
            return "Do not use in team builder due to manual exclusion."
        return "Do not include in team builder."

    if risk_level == "high":
        return "Avoid tomorrow if possible or use only with explicit manual review."

    if risk_level == "moderate":
        return "Use with caution and review role/program suitability."

    if usage_level == "underused":
        return "Consider for tomorrow if otherwise suitable."

    return "Review manually."


def _build_attention_item(
    dog: Dog,
    eligible_for_team_builder: bool,
    risk_level: str,
    usage_level: str,
    attention_level: str,
    reasons: list[str],
    suggested_action: str,
) -> DogAttentionItem:
    return DogAttentionItem(
        dog_id=dog.id,
        dog_name=dog.name,
        attention_level=attention_level,
        eligible_for_team_builder=eligible_for_team_builder,
        risk_level=risk_level,
        usage_level=usage_level,
        lifecycle_status=_as_str(dog.lifecycle_status),
        availability_status=_as_str(dog.availability_status),
        exclude_from_team_builder=dog.exclude_from_team_builder,
        exclude_reason=dog.exclude_reason,
        reasons=reasons,
        suggested_action=suggested_action,
    )


def get_planning_blockers(
    db: Session,
    as_of_date: date | None = None,
) -> DogAttentionListResponse:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())
    items: list[DogAttentionItem] = []

    for dog in dogs:
        if not _is_temporary_planning_blocker(dog):
            continue

        eligibility = get_team_builder_eligibility(dog, as_of_date)
        reasons = list(eligibility.reasons)

        item = _build_attention_item(
            dog=dog,
            eligible_for_team_builder=False,
            risk_level="n/a",
            usage_level="n/a",
            attention_level="critical",
            reasons=reasons,
            suggested_action=_build_suggested_action(
                eligible=False,
                risk_level="n/a",
                usage_level="n/a",
                availability_status=_as_str(dog.availability_status),
                exclude_from_team_builder=dog.exclude_from_team_builder,
                blocker_reasons=reasons,
            ),
        )
        items.append(item)

    items.sort(key=lambda x: x.dog_name)

    return DogAttentionListResponse(
        total_items=len(items),
        items=items,
    )


def get_operational_watchlist(
    db: Session,
    hard_day_km_threshold: float,
    recent_days: int,
    as_of_date: date | None = None,
) -> DogAttentionListResponse:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())
    items: list[DogAttentionItem] = []

    for dog in dogs:
        if not is_operationally_available(dog, as_of_date):
            continue

        eligibility = get_team_builder_eligibility(dog, as_of_date)
        if not eligibility.eligible_for_team_builder:
            continue

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
            as_of_date=as_of_date,
        )
        if risk is None:
            continue

        reasons = list(risk.flags)

        strong_flags = {
            "high_7d_load",
            "high_14d_load",
            "recent_heavy_block_despite_rest_day",
            "aging_dog_high_recent_load",
            "senior_dog_high_recent_load",
            "aging_dog_dense_schedule",
            "senior_dog_dense_schedule",
            "aging_dog_high_single_day_load",
            "senior_dog_high_single_day_load",
        }

        attention_level = None

        if risk.risk_level == "high":
            attention_level = "high"
            reasons = ["high_risk_tomorrow"] + reasons
        elif risk.risk_level == "moderate" and any(flag in reasons for flag in strong_flags):
            attention_level = "medium"
            reasons = ["moderate_risk_tomorrow"] + reasons

        if attention_level is None:
            continue

        seen = set()
        reasons = [r for r in reasons if not (r in seen or seen.add(r))]

        item = _build_attention_item(
            dog=dog,
            eligible_for_team_builder=True,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            attention_level=attention_level,
            reasons=reasons,
            suggested_action=_build_suggested_action(
                eligible=True,
                risk_level=risk.risk_level,
                usage_level=risk.usage_level,
                availability_status=_as_str(dog.availability_status),
                exclude_from_team_builder=dog.exclude_from_team_builder,
            ),
        )
        items.append(item)

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: (order.get(x.attention_level, 99), x.dog_name))

    return DogAttentionListResponse(
        total_items=len(items),
        items=items,
    )


def get_underused_candidates(
    db: Session,
    hard_day_km_threshold: float,
    recent_days: int,
    as_of_date: date | None = None,
) -> DogAttentionListResponse:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())
    items: list[DogAttentionItem] = []

    for dog in dogs:
        if not is_operationally_available(dog, as_of_date):
            continue

        eligibility = get_team_builder_eligibility(dog, as_of_date)
        if not eligibility.eligible_for_team_builder:
            continue

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
            as_of_date=as_of_date,
        )
        if risk is None:
            continue

        if risk.usage_level != "underused":
            continue

        if risk.risk_level == "high":
            continue

        reasons = ["underused_recently"] + list(risk.flags)

        seen = set()
        reasons = [r for r in reasons if not (r in seen or seen.add(r))]

        item = _build_attention_item(
            dog=dog,
            eligible_for_team_builder=True,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            attention_level="medium",
            reasons=reasons,
            suggested_action=_build_suggested_action(
                eligible=True,
                risk_level=risk.risk_level,
                usage_level=risk.usage_level,
                availability_status=_as_str(dog.availability_status),
                exclude_from_team_builder=dog.exclude_from_team_builder,
            ),
        )
        items.append(item)

    items.sort(key=lambda x: x.dog_name)

    return DogAttentionListResponse(
        total_items=len(items),
        items=items,
    )