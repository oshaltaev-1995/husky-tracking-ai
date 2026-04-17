from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.attention import DogAttentionItem, DogAttentionListResponse
from app.services.eligibility_service import get_team_builder_eligibility
from app.services.risk_service import get_dog_risk_summary


def _build_suggested_action(
    eligible: bool,
    risk_level: str,
    usage_level: str,
    availability_status: str,
    exclude_from_team_builder: bool,
) -> str:
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


def _attention_level(
    eligible: bool,
    risk_level: str,
    usage_level: str,
    availability_status: str,
    exclude_from_team_builder: bool,
) -> str:
    if not eligible or availability_status != "available" or exclude_from_team_builder:
        return "critical"
    if risk_level == "high":
        return "high"
    if risk_level == "moderate" or usage_level == "underused":
        return "medium"
    return "low"


def _is_priority_item(
    eligible: bool,
    attention_level: str,
    risk_level: str,
    reasons: list[str],
) -> bool:
    if not eligible:
        return True

    if attention_level in {"critical", "high"}:
        return True

    if risk_level == "high":
        return True

    if risk_level == "moderate":
        strong_reason_flags = {
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
        if any(flag in reasons for flag in strong_reason_flags):
            return True

    return False


def get_attention_list(
    db: Session,
    hard_day_km_threshold: float = 10.0,
    recent_days: int = 14,
    include_low: bool = False,
    priority_only: bool = False,
) -> DogAttentionListResponse:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())

    items: list[DogAttentionItem] = []

    for dog in dogs:
        eligibility = get_team_builder_eligibility(dog)
        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
        )

        if risk is None:
            continue

        reasons: list[str] = []

        if not eligibility.eligible_for_team_builder:
            reasons.extend(eligibility.reasons)

        if risk.risk_level == "high":
            reasons.append("high_risk_tomorrow")
        elif risk.risk_level == "moderate":
            reasons.append("moderate_risk_tomorrow")

        if risk.usage_level == "underused":
            reasons.append("underused_recently")

        reasons.extend(risk.flags)

        seen = set()
        reasons = [r for r in reasons if not (r in seen or seen.add(r))]

        lifecycle_status = dog.lifecycle_status.value if hasattr(dog.lifecycle_status, "value") else str(dog.lifecycle_status)
        availability_status = dog.availability_status.value if hasattr(dog.availability_status, "value") else str(dog.availability_status)

        attention_level = _attention_level(
            eligible=eligibility.eligible_for_team_builder,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            availability_status=availability_status,
            exclude_from_team_builder=dog.exclude_from_team_builder,
        )

        if not include_low and attention_level == "low":
            continue

        if priority_only and not _is_priority_item(
            eligible=eligibility.eligible_for_team_builder,
            attention_level=attention_level,
            risk_level=risk.risk_level,
            reasons=reasons,
        ):
            continue

        item = DogAttentionItem(
            dog_id=dog.id,
            dog_name=dog.name,
            attention_level=attention_level,
            eligible_for_team_builder=eligibility.eligible_for_team_builder,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            lifecycle_status=lifecycle_status,
            availability_status=availability_status,
            exclude_from_team_builder=dog.exclude_from_team_builder,
            exclude_reason=dog.exclude_reason,
            reasons=reasons,
            suggested_action=_build_suggested_action(
                eligible=eligibility.eligible_for_team_builder,
                risk_level=risk.risk_level,
                usage_level=risk.usage_level,
                availability_status=availability_status,
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