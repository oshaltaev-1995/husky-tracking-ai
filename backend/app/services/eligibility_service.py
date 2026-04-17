from __future__ import annotations

from datetime import date

from app.models import Dog
from app.schemas.dog_status import DogEligibilityRead


def _as_str(value) -> str:
    if hasattr(value, "value"):
        return str(value.value).strip().lower()
    return str(value).strip().lower()


def estimate_age_years(birth_year: int | None, reference_date: date | None = None) -> int | None:
    if birth_year is None:
        return None
    if reference_date is None:
        reference_date = date.today()
    return reference_date.year - birth_year


def is_operationally_available(dog: Dog, reference_date: date | None = None) -> bool:
    lifecycle_status = _as_str(dog.lifecycle_status)
    availability_status = _as_str(dog.availability_status)

    if lifecycle_status != "active":
        return False

    if availability_status != "available":
        return False

    if dog.exclude_from_team_builder:
        return False

    return True


def get_team_builder_eligibility(dog: Dog, reference_date: date | None = None) -> DogEligibilityRead:
    reasons: list[str] = []

    lifecycle_status = _as_str(dog.lifecycle_status)
    availability_status = _as_str(dog.availability_status)

    if lifecycle_status != "active":
        reasons.append(f"lifecycle_status={lifecycle_status}")

    if availability_status != "available":
        reasons.append(f"availability_status={availability_status}")

    if dog.exclude_from_team_builder:
        reasons.append("manual_exclusion")

    eligible = len(reasons) == 0

    return DogEligibilityRead(
        dog_id=dog.id,
        dog_name=dog.name,
        eligible_for_team_builder=eligible,
        reasons=reasons,
    )