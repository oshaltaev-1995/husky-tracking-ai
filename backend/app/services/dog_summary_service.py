from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.dog import DogRead
from app.schemas.dog_summary import DogSummaryRead
from app.services.eligibility_service import get_team_builder_eligibility
from app.services.risk_service import get_dog_risk_summary


def get_dogs_summary(
    db: Session,
    hard_day_km_threshold: float = 15.0,
    recent_days: int = 14,
    as_of_date: date | None = None,
) -> list[DogSummaryRead]:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())

    result: list[DogSummaryRead] = []

    for dog in dogs:
        eligibility = get_team_builder_eligibility(dog, as_of_date)
        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
            as_of_date=as_of_date,
        )

        usage_level = None
        if eligibility.eligible_for_team_builder and risk:
            usage_level = risk.usage_level

        result.append(
            DogSummaryRead(
                dog=DogRead.model_validate(dog),
                eligible_for_team_builder=eligibility.eligible_for_team_builder,
                eligibility_reasons=eligibility.reasons,
                risk_level=risk.risk_level if risk else "unknown",
                usage_level=usage_level,
            )
        )

    return result