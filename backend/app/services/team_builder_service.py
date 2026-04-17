from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.team_builder import (
    ExcludedDog,
    SuggestedTeam,
    TeamBuilderRequest,
    TeamBuilderResponse,
    TeamDogAssignment,
)
from app.services.eligibility_service import get_team_builder_eligibility
from app.services.risk_service import get_dog_risk_summary
from app.services.team_rules_service import (
    get_preferred_partner_names,
    is_big_sled_only,
    is_lead_only,
    is_solo_only,
    normalize_name,
)


@dataclass
class CandidateDog:
    dog: Dog
    risk_level: str
    usage_level: str
    score: float


@dataclass
class PairUnit:
    dogs: list[CandidateDog]
    relation: str
    can_split: bool


def _primary_role_value(dog: Dog) -> str | None:
    return dog.primary_role.lower().strip() if dog.primary_role else None


def _score_candidate(
    dog: Dog,
    risk_level: str,
    usage_level: str,
    prefer_underused: bool,
) -> float:
    score = 0.0

    if risk_level == "low":
        score += 30
    elif risk_level == "moderate":
        score += 15
    else:
        score -= 100

    if prefer_underused and usage_level == "underused":
        score += 20

    primary_role = _primary_role_value(dog)
    if primary_role == "lead":
        score += 8
    elif primary_role == "wheel":
        score += 6
    elif primary_role == "team":
        score += 4

    role_count = int(bool(dog.can_lead)) + int(bool(dog.can_team)) + int(bool(dog.can_wheel))
    score += role_count * 2
    score += 5

    return score


def _build_assignment(dog: Dog, assigned_role: str, risk_level: str, usage_level: str) -> TeamDogAssignment:
    return TeamDogAssignment(
        dog_id=dog.id,
        dog_name=dog.name,
        primary_role=dog.primary_role,
        assigned_role=assigned_role,
        risk_level=risk_level,
        usage_level=usage_level,
    )


def _can_fill_role(dog: Dog, role: str) -> bool:
    if role == "lead":
        return bool(dog.can_lead)
    if role == "wheel":
        return bool(dog.can_wheel)
    if role == "team":
        return bool(dog.can_team)
    return False


def _role_fit_score(dog: Dog, role: str) -> float:
    score = 0.0
    primary = _primary_role_value(dog)

    if primary == role:
        score += 20
    elif role == "team" and primary in {"wheel", "lead"} and dog.can_team:
        score += 10
    elif _can_fill_role(dog, role):
        score += 5

    if role == "lead" and is_lead_only(dog.name):
        score += 20

    if role != "lead" and is_lead_only(dog.name):
        score -= 100

    return score


def _build_home_index(dogs: list[Dog]) -> dict[tuple[str | None, int | None], list[Dog]]:
    by_home: dict[tuple[str | None, int | None], list[Dog]] = {}
    for dog in dogs:
        key = (dog.kennel_row, dog.home_slot)
        by_home.setdefault(key, []).append(dog)
    return by_home


def _filter_candidates_for_request(
    dogs: list[Dog],
    db: Session,
    request: TeamBuilderRequest,
    hard_day_km_threshold: float,
    recent_days: int,
) -> tuple[list[CandidateDog], list[ExcludedDog]]:
    candidates: list[CandidateDog] = []
    excluded: list[ExcludedDog] = []

    for dog in dogs:
        eligibility = get_team_builder_eligibility(dog)
        if not eligibility.eligible_for_team_builder:
            excluded.append(
                ExcludedDog(
                    dog_id=dog.id,
                    dog_name=dog.name,
                    reasons=eligibility.reasons,
                )
            )
            continue

        if request.sled_type != "big_sled" and is_big_sled_only(dog.name):
            excluded.append(
                ExcludedDog(
                    dog_id=dog.id,
                    dog_name=dog.name,
                    reasons=["big_sled_only"],
                )
            )
            continue

        risk = get_dog_risk_summary(
            db=db,
            dog_id=dog.id,
            hard_day_km_threshold=hard_day_km_threshold,
            recent_days=recent_days,
        )
        if risk is None:
            excluded.append(
                ExcludedDog(
                    dog_id=dog.id,
                    dog_name=dog.name,
                    reasons=["risk_unavailable"],
                )
            )
            continue

        if request.avoid_high_risk and risk.risk_level == "high":
            excluded.append(
                ExcludedDog(
                    dog_id=dog.id,
                    dog_name=dog.name,
                    reasons=["high_risk_tomorrow"],
                )
            )
            continue

        score = _score_candidate(
            dog=dog,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            prefer_underused=request.prefer_underused,
        )

        candidates.append(
            CandidateDog(
                dog=dog,
                risk_level=risk.risk_level,
                usage_level=risk.usage_level,
                score=score,
            )
        )

    candidates.sort(key=lambda c: (-c.score, c.dog.name))
    return candidates, excluded


def _build_pair_units(candidates: list[CandidateDog], all_dogs: list[Dog]) -> list[PairUnit]:
    home_index = _build_home_index(all_dogs)
    by_name = {normalize_name(c.dog.name): c for c in candidates}
    used: set[int] = set()
    units: list[PairUnit] = []

    for cand in candidates:
        if cand.dog.id in used:
            continue

        if is_solo_only(cand.dog.name):
            units.append(PairUnit(dogs=[cand], relation="solo", can_split=True))
            used.add(cand.dog.id)
            continue

        preferred_names = get_preferred_partner_names(cand.dog, home_index)
        chosen_partner = None
        chosen_relation = None

        for partner_name in preferred_names:
            partner = by_name.get(partner_name)
            if partner is None or partner.dog.id in used or partner.dog.id == cand.dog.id:
                continue

            chosen_partner = partner
            # simplified relation naming
            chosen_relation = "pair"
            break

        if chosen_partner:
            units.append(
                PairUnit(
                    dogs=[cand, chosen_partner],
                    relation=chosen_relation or "pair",
                    can_split=True,
                )
            )
            used.add(cand.dog.id)
            used.add(chosen_partner.dog.id)

    for cand in candidates:
        if cand.dog.id in used:
            continue
        units.append(PairUnit(dogs=[cand], relation="solo", can_split=True))
        used.add(cand.dog.id)

    return units


def _pair_role_score(unit: PairUnit, role: str) -> float:
    dogs = unit.dogs

    if len(dogs) == 1:
        dog = dogs[0].dog
        score = dogs[0].score + _role_fit_score(dog, role)
        if role != "team" and is_solo_only(dog.name):
            score -= 5
        return score

    d1, d2 = dogs[0], dogs[1]
    score = d1.score + d2.score
    score += _role_fit_score(d1.dog, role)
    score += _role_fit_score(d2.dog, role)
    score += 20  # pair bonus

    primary_roles = {_primary_role_value(d1.dog), _primary_role_value(d2.dog)}
    if role not in primary_roles:
        score -= 4

    if role == "team" and "wheel" in primary_roles:
        score += 3

    return score


def _unit_can_fill_as_pair(unit: PairUnit, role: str) -> bool:
    if len(unit.dogs) == 1:
        return _can_fill_role(unit.dogs[0].dog, role)
    return all(_can_fill_role(cd.dog, role) for cd in unit.dogs)


def _pick_best_pair_unit(units: list[PairUnit], used_ids: set[int], role: str) -> PairUnit | None:
    best_unit = None
    best_score = -10_000.0

    for unit in units:
        if any(cd.dog.id in used_ids for cd in unit.dogs):
            continue
        if len(unit.dogs) != 2:
            continue
        if not _unit_can_fill_as_pair(unit, role):
            continue

        score = _pair_role_score(unit, role)
        if score > best_score:
            best_score = score
            best_unit = unit

    return best_unit


def _pick_best_single_for_role(candidates: list[CandidateDog], used_ids: set[int], role: str) -> CandidateDog | None:
    best = None
    best_score = -10_000.0

    for cand in candidates:
        if cand.dog.id in used_ids:
            continue
        if not _can_fill_role(cand.dog, role):
            continue
        if is_lead_only(cand.dog.name) and role != "lead":
            continue

        score = cand.score + _role_fit_score(cand.dog, role)

        if score > best_score:
            best_score = score
            best = cand

    return best


def _base_role_needs_for_five() -> tuple[int, int, int]:
    # 5-dog base team: 2 lead, 1 team, 2 wheel
    return 2, 2, 1


def _should_add_sixth_dog(
    current_assignments: list[TeamDogAssignment],
    candidates: list[CandidateDog],
    used_ids: set[int],
) -> bool:
    # add 6th if there is a good available team-capable dog
    # and current team contains moderate-risk or aging-ish edge pressure indirectly via risk signal
    has_moderate = any(a.risk_level == "moderate" for a in current_assignments)
    available_team_filler = any(
        c.dog.id not in used_ids and c.dog.can_team and c.risk_level != "high"
        for c in candidates
    )

    return has_moderate and available_team_filler


def build_teams(
    db: Session,
    request: TeamBuilderRequest,
    hard_day_km_threshold: float = 15.0,
    recent_days: int = 14,
) -> TeamBuilderResponse:
    dogs = list(db.execute(select(Dog).order_by(Dog.name.asc())).scalars().all())

    if request.max_dogs_per_team < request.min_dogs_per_team:
        raise ValueError("max_dogs_per_team cannot be less than min_dogs_per_team")

    candidates, excluded_dogs = _filter_candidates_for_request(
        dogs=dogs,
        db=db,
        request=request,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )

    pair_units = _build_pair_units(candidates, dogs)

    needed_total_min = request.team_count * request.min_dogs_per_team
    global_warnings: list[str] = []

    if len(candidates) < needed_total_min:
        global_warnings.append(
            f"Not enough eligible dogs for minimum plan: need {needed_total_min}, have {len(candidates)}."
        )

    used_ids: set[int] = set()
    teams: list[SuggestedTeam] = []

    for team_number in range(1, request.team_count + 1):
        team_assignments: list[TeamDogAssignment] = []
        warnings: list[str] = []

        # Start from 5-dog logic as default base if allowed by request
        if request.min_dogs_per_team <= 5 <= request.max_dogs_per_team:
            base_team_size = 5
        else:
            base_team_size = request.min_dogs_per_team

        if base_team_size == 5:
            lead_needed, wheel_needed, team_needed = _base_role_needs_for_five()
        else:
            # fallback generic
            lead_needed = 2 if base_team_size >= 5 else 1
            wheel_needed = 2 if base_team_size >= 5 else 1
            team_needed = max(0, base_team_size - lead_needed - wheel_needed)

        # 1. leads
        while len([a for a in team_assignments if a.assigned_role == "lead"]) + 1 < lead_needed:
            unit = _pick_best_pair_unit(pair_units, used_ids, "lead")
            if unit is None:
                break
            for cd in unit.dogs:
                used_ids.add(cd.dog.id)
                team_assignments.append(_build_assignment(cd.dog, "lead", cd.risk_level, cd.usage_level))

        while len([a for a in team_assignments if a.assigned_role == "lead"]) < lead_needed:
            cand = _pick_best_single_for_role(candidates, used_ids, "lead")
            if cand is None:
                warnings.append("Not enough lead-capable dogs for ideal structure.")
                break
            used_ids.add(cand.dog.id)
            team_assignments.append(_build_assignment(cand.dog, "lead", cand.risk_level, cand.usage_level))

        # 2. wheels
        while len([a for a in team_assignments if a.assigned_role == "wheel"]) + 1 < wheel_needed:
            unit = _pick_best_pair_unit(pair_units, used_ids, "wheel")
            if unit is None:
                break
            for cd in unit.dogs:
                used_ids.add(cd.dog.id)
                team_assignments.append(_build_assignment(cd.dog, "wheel", cd.risk_level, cd.usage_level))

        while len([a for a in team_assignments if a.assigned_role == "wheel"]) < wheel_needed:
            cand = _pick_best_single_for_role(candidates, used_ids, "wheel")
            if cand is None:
                warnings.append("Not enough wheel-capable dogs for ideal structure.")
                break
            used_ids.add(cand.dog.id)
            team_assignments.append(_build_assignment(cand.dog, "wheel", cand.risk_level, cand.usage_level))

        # 3. center/team
        while len([a for a in team_assignments if a.assigned_role == "team"]) + 1 < team_needed:
            unit = _pick_best_pair_unit(pair_units, used_ids, "team")
            if unit is None:
                break
            for cd in unit.dogs:
                used_ids.add(cd.dog.id)
                team_assignments.append(_build_assignment(cd.dog, "team", cd.risk_level, cd.usage_level))

        while len([a for a in team_assignments if a.assigned_role == "team"]) < team_needed:
            cand = _pick_best_single_for_role(candidates, used_ids, "team")
            if cand is None:
                warnings.append("Not enough team-capable dogs for ideal structure.")
                break
            used_ids.add(cand.dog.id)
            team_assignments.append(_build_assignment(cand.dog, "team", cand.risk_level, cand.usage_level))

        # 4. Optional 6th dog if allowed
        if request.max_dogs_per_team >= 6 and len(team_assignments) == 5:
            if _should_add_sixth_dog(team_assignments, candidates, used_ids):
                filler = _pick_best_single_for_role(candidates, used_ids, "team")
                if filler is not None:
                    used_ids.add(filler.dog.id)
                    team_assignments.append(
                        _build_assignment(filler.dog, "team", filler.risk_level, filler.usage_level)
                    )

        # 5. If still below min, fill with any usable dogs
        while len(team_assignments) < request.min_dogs_per_team:
            filler = None
            filler_score = -10_000.0

            for cand in candidates:
                if cand.dog.id in used_ids:
                    continue
                if is_lead_only(cand.dog.name):
                    continue

                score = cand.score
                if cand.dog.can_team:
                    score += _role_fit_score(cand.dog, "team")
                elif cand.dog.can_wheel:
                    score += 2
                elif cand.dog.can_lead:
                    score += 1
                else:
                    continue

                if score > filler_score:
                    filler = cand
                    filler_score = score

            if filler is None:
                warnings.append("Team is incomplete due to insufficient remaining dogs.")
                break

            used_ids.add(filler.dog.id)
            team_assignments.append(
                _build_assignment(filler.dog, "team", filler.risk_level, filler.usage_level)
            )

        # reorder for readability: lead -> team -> wheel
        role_order = {"lead": 0, "team": 1, "wheel": 2}
        team_assignments.sort(key=lambda a: (role_order.get(a.assigned_role, 99), a.dog_name))

        teams.append(
            SuggestedTeam(
                team_number=team_number,
                dogs=team_assignments,
                warnings=warnings,
            )
        )

    unassigned_dogs: list[TeamDogAssignment] = []
    for cand in candidates:
        if cand.dog.id not in used_ids:
            unassigned_dogs.append(
                _build_assignment(cand.dog, "unassigned", cand.risk_level, cand.usage_level)
            )

    unassigned_dogs.sort(key=lambda x: x.dog_name)

    return TeamBuilderResponse(
        request=request,
        teams=teams,
        unassigned_dogs=unassigned_dogs,
        excluded_dogs=excluded_dogs,
        global_warnings=global_warnings,
    )