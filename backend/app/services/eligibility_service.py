from __future__ import annotations

from datetime import date

from app.models import Dog
from app.schemas.dog_status import DogEligibilityRead


MIN_WORKING_AGE_YEARS = 2


def estimate_age_years(birth_year: int | None, reference_date: date | None = None) -> int | None:
    if birth_year is None:
        return None
    if reference_date is None:
        reference_date = date.today()
    return reference_date.year - birth_year


def get_team_builder_eligibility(dog: Dog, reference_date: date | None = None) -> DogEligibilityRead:
    reasons: list[str] = []

    age_years = estimate_age_years(dog.birth_year, reference_date)

    if dog.lifecycle_status != "active":
        reasons.append(f"lifecycle_status={dog.lifecycle_status}")

    if dog.availability_status != "available":
        reasons.append(f"availability_status={dog.availability_status}")

    if dog.exclude_from_team_builder:
        reasons.append("manual_exclusion")

    if age_years is not None and age_years < MIN_WORKING_AGE_YEARS:
        reasons.append("too_young")

    eligible = len(reasons) == 0

    return DogEligibilityRead(
        dog_id=dog.id,
        dog_name=dog.name,
        eligible_for_team_builder=eligible,
        reasons=reasons,
    )