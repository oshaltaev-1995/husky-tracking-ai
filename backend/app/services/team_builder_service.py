from __future__ import annotations

from dataclasses import dataclass
from math import inf

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.team_builder import (
    ExcludedDog,
    HarnessDog,
    HarnessLayout,
    HarnessRow,
    SuggestedTeam,
    TeamBuilderRequest,
    TeamBuilderResponse,
    TeamDogAssignment,
)
from app.services.eligibility_service import get_team_builder_eligibility
from app.services.risk_service import get_dog_risk_summary
from app.services.team_rules_service import (
    get_partner_options,
    get_preferred_role,
    get_preferred_team_number,
    is_big_sled_only,
    is_lead_only,
    is_pair_explicitly_avoided,
    is_solo_only,
    normalize_name,
    solo_team_allowed,
)


@dataclass
class CandidateDog:
    dog: Dog
    risk_level: str
    usage_level: str
    score: float
    age_group: str | None
    days_since_last_run: int | None


@dataclass
class PairUnit:
    dogs: list[CandidateDog]
    relation: str
    can_split: bool
    priority_rank: int
    is_stable_pair: bool


@dataclass
class SelectedUnit:
    dogs: list[CandidateDog]
    relation: str
    row_role: str
    row_type: str
    warnings: list[str]


def _primary_role_value(dog: Dog) -> str | None:
    return dog.primary_role.lower().strip() if dog.primary_role else None


def _relation_rank(relation: str) -> int:
    order = {
        "forced_pair": 1,
        "home_pair": 2,
        "preferred_pair": 3,
        "allowed_pair": 4,
        "solo": 5,
        "single_lead": 6,
        "single_center": 6,
        "single_wheel": 6,
        "single_fallback": 7,
    }
    return order.get(relation, 99)


def _pair_relation_bonus(relation: str) -> float:
    if relation == "forced_pair":
        return 40
    if relation == "home_pair":
        return 30
    if relation == "preferred_pair":
        return 16
    if relation == "allowed_pair":
        return 8
    return 0


def _pair_relation_split_allowed(relation: str) -> bool:
    return relation not in {"forced_pair", "home_pair"}


def _build_assignment(dog: Dog, assigned_role: str, risk_level: str, usage_level: str) -> TeamDogAssignment:
    return TeamDogAssignment(
        dog_id=dog.id,
        dog_name=dog.name,
        primary_role=dog.primary_role,
        assigned_role=assigned_role,
        risk_level=risk_level,
        usage_level=usage_level,
    )


def _build_harness_dog(dog: CandidateDog, assigned_role: str) -> HarnessDog:
    return HarnessDog(
        dog_id=dog.dog.id,
        dog_name=dog.dog.name,
        primary_role=dog.dog.primary_role,
        assigned_role=assigned_role,
        risk_level=dog.risk_level,
        usage_level=dog.usage_level,
    )


def _build_harness_row(unit: SelectedUnit) -> HarnessRow:
    return HarnessRow(
        row_role=unit.row_role,
        row_type=unit.row_type,
        relation=unit.relation,
        dogs=[_build_harness_dog(cd, unit.row_role) for cd in unit.dogs],
        warnings=unit.warnings,
    )


def _can_fill_role(dog: Dog, role: str) -> bool:
    if role == "lead":
        return bool(dog.can_lead)
    if role == "wheel":
        return bool(dog.can_wheel)
    if role == "team":
        return bool(dog.can_team)
    return False


def _is_yksiot(dog: Dog) -> bool:
    return normalize_name(dog.kennel_row) == "YKSIOT"


def _prefer_single_team_position(dog: Dog) -> bool:
    if is_solo_only(dog.name) and solo_team_allowed(dog.name):
        return True
    return False


def _is_prime_rotation_candidate(age_group: str | None) -> bool:
    return age_group == "prime"


def _prime_rotation_bonus(age_group: str | None, days_since_last_run: int | None) -> float:
    if not _is_prime_rotation_candidate(age_group):
        return 0.0
    if days_since_last_run is None:
        return 0.0
    if days_since_last_run >= 5:
        return 18.0
    if days_since_last_run >= 4:
        return 14.0
    if days_since_last_run >= 3:
        return 10.0
    if days_since_last_run >= 2:
        return 6.0
    return 0.0


def _score_candidate(
    dog: Dog,
    risk_level: str,
    usage_level: str,
    age_group: str | None,
    days_since_last_run: int | None,
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

    score += _prime_rotation_bonus(age_group, days_since_last_run)

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


def _team_specific_bonus(dog: Dog, team_number: int, role: str) -> float:
    score = 0.0

    preferred_team = get_preferred_team_number(dog.name)
    preferred_role = get_preferred_role(dog.name)

    if preferred_team is not None and preferred_team == team_number:
        score += 16

    if preferred_role is not None and preferred_role == role:
        score += 14

    if preferred_team is not None and preferred_team == team_number and preferred_role == role:
        score += 12

    return score


def _role_fit_score(dog: Dog, role: str, team_number: int) -> float:
    score = 0.0
    primary = _primary_role_value(dog)
    preferred_role = get_preferred_role(dog.name)

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

    if preferred_role is not None and preferred_role != role:
        score -= 18

    if role == "team" and _prefer_single_team_position(dog):
        score += 10

    if role == "team" and _is_yksiot(dog):
        score += 4

    score += _team_specific_bonus(dog, team_number, role)

    return score


def _build_home_index(dogs: list[Dog]) -> dict[tuple[str | None, int | None], list[Dog]]:
    by_home: dict[tuple[str | None, int | None], list[Dog]] = {}
    for dog in dogs:
        key = (dog.kennel_row, dog.home_slot)
        by_home.setdefault(key, []).append(dog)
    return by_home


def _is_pair_known_safe(
    left: Dog,
    right: Dog,
    home_index: dict[tuple[str | None, int | None], list[Dog]],
) -> tuple[bool, str | None]:
    left_name = normalize_name(left.name)
    right_name = normalize_name(right.name)

    if left_name == right_name:
        return False, None

    if is_pair_explicitly_avoided(left.name, right.name) or is_pair_explicitly_avoided(right.name, left.name):
        return False, None

    left_options = get_partner_options(left, home_index)
    right_options = get_partner_options(right, home_index)

    left_map = {opt.partner_name: opt.relation for opt in left_options}
    right_map = {opt.partner_name: opt.relation for opt in right_options}

    left_relation = left_map.get(right_name)
    right_relation = right_map.get(left_name)

    if left_relation is None and right_relation is None:
        return False, None

    strength = {
        "forced_pair": 4,
        "home_pair": 3,
        "preferred_pair": 2,
        "allowed_pair": 1,
    }

    if left_relation and right_relation:
        relation = left_relation if strength[left_relation] >= strength[right_relation] else right_relation
    else:
        relation = left_relation or right_relation

    return True, relation


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

        age_group = risk.metrics.age_group if risk.metrics else None
        days_since_last_run = risk.metrics.days_since_last_run if risk.metrics else None

        score = _score_candidate(
            dog=dog,
            risk_level=risk.risk_level,
            usage_level=risk.usage_level,
            age_group=age_group,
            days_since_last_run=days_since_last_run,
            prefer_underused=request.prefer_underused,
        )

        candidates.append(
            CandidateDog(
                dog=dog,
                risk_level=risk.risk_level,
                usage_level=risk.usage_level,
                score=score,
                age_group=age_group,
                days_since_last_run=days_since_last_run,
            )
        )

    candidates.sort(key=lambda c: (-c.score, c.dog.name))
    return candidates, excluded


def _build_pair_units(
    candidates: list[CandidateDog],
    home_index: dict[tuple[str | None, int | None], list[Dog]],
) -> list[PairUnit]:
    by_name = {normalize_name(c.dog.name): c for c in candidates}
    used: set[int] = set()
    units: list[PairUnit] = []

    for cand in candidates:
        if cand.dog.id in used:
            continue

        if is_solo_only(cand.dog.name):
            units.append(
                PairUnit(
                    dogs=[cand],
                    relation="solo",
                    can_split=True,
                    priority_rank=_relation_rank("solo"),
                    is_stable_pair=False,
                )
            )
            used.add(cand.dog.id)
            continue

        if _prefer_single_team_position(cand.dog):
            units.append(
                PairUnit(
                    dogs=[cand],
                    relation="solo",
                    can_split=True,
                    priority_rank=_relation_rank("solo"),
                    is_stable_pair=False,
                )
            )
            used.add(cand.dog.id)
            continue

        chosen_partner: CandidateDog | None = None
        chosen_relation: str | None = None

        for option in get_partner_options(cand.dog, home_index):
            partner = by_name.get(option.partner_name)
            if partner is None:
                continue
            if partner.dog.id in used:
                continue
            if partner.dog.id == cand.dog.id:
                continue
            if is_solo_only(partner.dog.name):
                continue
            if _prefer_single_team_position(partner.dog):
                continue

            pair_ok, relation = _is_pair_known_safe(cand.dog, partner.dog, home_index)
            if not pair_ok or relation is None:
                continue

            chosen_partner = partner
            chosen_relation = relation
            break

        if chosen_partner is not None:
            units.append(
                PairUnit(
                    dogs=[cand, chosen_partner],
                    relation=chosen_relation or "allowed_pair",
                    can_split=_pair_relation_split_allowed(chosen_relation or "allowed_pair"),
                    priority_rank=_relation_rank(chosen_relation or "allowed_pair"),
                    is_stable_pair=(chosen_relation in {"forced_pair", "home_pair"}),
                )
            )
            used.add(cand.dog.id)
            used.add(chosen_partner.dog.id)

    for cand in candidates:
        if cand.dog.id in used:
            continue
        units.append(
            PairUnit(
                dogs=[cand],
                relation="solo",
                can_split=True,
                priority_rank=_relation_rank("solo"),
                is_stable_pair=False,
            )
        )
        used.add(cand.dog.id)

    return units


def _candidate_has_available_stable_pair(
    cand: CandidateDog,
    units: list[PairUnit],
    used_ids: set[int],
) -> bool:
    for unit in units:
        if len(unit.dogs) != 2:
            continue
        if not unit.is_stable_pair:
            continue
        ids = {dog.dog.id for dog in unit.dogs}
        if cand.dog.id in ids and not any(dog_id in used_ids for dog_id in ids):
            return True
    return False


def _pair_role_score(unit: PairUnit, role: str, team_number: int) -> float:
    dogs = unit.dogs

    if len(dogs) == 1:
        dog = dogs[0].dog
        score = dogs[0].score + _role_fit_score(dog, role, team_number)

        if is_solo_only(dog.name):
            score += 8
        if role == "team" and _prefer_single_team_position(dog):
            score += 12

        return score

    d1, d2 = dogs[0], dogs[1]
    score = d1.score + d2.score
    score += _role_fit_score(d1.dog, role, team_number)
    score += _role_fit_score(d2.dog, role, team_number)
    score += _pair_relation_bonus(unit.relation)

    primary_roles = {_primary_role_value(d1.dog), _primary_role_value(d2.dog)}
    if role not in primary_roles:
        score -= 6

    if role == "team" and "wheel" in primary_roles:
        score += 3

    if role == "lead" and unit.relation in {"forced_pair", "home_pair"}:
        score += 8

    if role != "lead":
        for cd in unit.dogs:
            preferred_role = get_preferred_role(cd.dog.name)
            if preferred_role == "lead":
                score -= 20

    return score


def _pick_best_pair_unit(
    units: list[PairUnit],
    used_ids: set[int],
    role: str,
    team_number: int,
    allow_relations: set[str] | None = None,
) -> PairUnit | None:
    best_unit = None
    best_score = -inf

    for unit in units:
        if any(cd.dog.id in used_ids for cd in unit.dogs):
            continue
        if len(unit.dogs) != 2:
            continue
        if not all(_can_fill_role(cd.dog, role) for cd in unit.dogs):
            continue
        if allow_relations is not None and unit.relation not in allow_relations:
            continue

        score = _pair_role_score(unit, role, team_number)

        if score > best_score:
            best_score = score
            best_unit = unit

    return best_unit


def _pick_named_pair_unit(
    units: list[PairUnit],
    used_ids: set[int],
    role: str,
    left_name: str,
    right_name: str,
) -> PairUnit | None:
    target = {normalize_name(left_name), normalize_name(right_name)}

    for unit in units:
        if len(unit.dogs) != 2:
            continue
        names = {normalize_name(unit.dogs[0].dog.name), normalize_name(unit.dogs[1].dog.name)}
        if names != target:
            continue
        if any(cd.dog.id in used_ids for cd in unit.dogs):
            continue
        if not all(_can_fill_role(cd.dog, role) for cd in unit.dogs):
            continue
        return unit

    return None


def _pick_named_single(
    candidates: list[CandidateDog],
    used_ids: set[int],
    role: str,
    dog_name: str,
) -> CandidateDog | None:
    target = normalize_name(dog_name)

    for cand in candidates:
        if normalize_name(cand.dog.name) != target:
            continue
        if cand.dog.id in used_ids:
            continue
        if not _can_fill_role(cand.dog, role):
            continue
        return cand

    return None


def _pick_best_single_for_role(
    candidates: list[CandidateDog],
    units: list[PairUnit],
    used_ids: set[int],
    role: str,
    team_number: int,
    prefer_single_center: bool = False,
) -> CandidateDog | None:
    best = None
    best_score = -inf

    for cand in candidates:
        if cand.dog.id in used_ids:
            continue
        if not _can_fill_role(cand.dog, role):
            continue
        if is_lead_only(cand.dog.name) and role != "lead":
            continue

        has_stable_pair_available = _candidate_has_available_stable_pair(cand, units, used_ids)

        if has_stable_pair_available and role in {"lead", "wheel"}:
            continue

        score = cand.score + _role_fit_score(cand.dog, role, team_number)

        if prefer_single_center and role == "team":
            if _prefer_single_team_position(cand.dog):
                score += 14
            elif _is_yksiot(cand.dog):
                score += 4
            else:
                score -= 6

        if has_stable_pair_available and role == "team":
            score -= 80

        if score > best_score:
            best_score = score
            best = cand

    return best


def _add_selected_unit(
    selected: list[SelectedUnit],
    used_ids: set[int],
    unit: PairUnit,
    role: str,
    warnings: list[str] | None = None,
) -> None:
    for cd in unit.dogs:
        used_ids.add(cd.dog.id)

    selected.append(
        SelectedUnit(
            dogs=unit.dogs,
            relation=unit.relation,
            row_role=role,
            row_type="pair" if len(unit.dogs) == 2 else "single",
            warnings=warnings or [],
        )
    )


def _add_selected_single(
    selected: list[SelectedUnit],
    used_ids: set[int],
    cand: CandidateDog,
    role: str,
    relation: str,
    warnings: list[str] | None = None,
) -> None:
    used_ids.add(cand.dog.id)

    selected.append(
        SelectedUnit(
            dogs=[cand],
            relation=relation,
            row_role=role,
            row_type="single",
            warnings=warnings or [],
        )
    )


def _flatten_assignments_from_selected(selected: list[SelectedUnit]) -> list[TeamDogAssignment]:
    role_order = {"lead": 0, "team": 1, "wheel": 2}
    ordered_units = sorted(selected, key=lambda item: (role_order.get(item.row_role, 99), item.row_type))

    assignments: list[TeamDogAssignment] = []
    for unit in ordered_units:
        for cd in unit.dogs:
            assignments.append(_build_assignment(cd.dog, unit.row_role, cd.risk_level, cd.usage_level))
    return assignments


def _build_layout_from_selected(selected: list[SelectedUnit]) -> HarnessLayout:
    lead_rows: list[HarnessRow] = []
    team_rows: list[HarnessRow] = []
    wheel_rows: list[HarnessRow] = []

    for unit in selected:
        row = _build_harness_row(unit)
        if unit.row_role == "lead":
            lead_rows.append(row)
        elif unit.row_role == "team":
            team_rows.append(row)
        elif unit.row_role == "wheel":
            wheel_rows.append(row)

    return HarnessLayout(
        lead_rows=lead_rows,
        team_rows=team_rows,
        wheel_rows=wheel_rows,
    )


def _choose_five_layout(
    candidates: list[CandidateDog],
    units: list[PairUnit],
    used_ids: set[int],
    team_number: int,
    force_simo_single_lead: bool,
    preferred_lead_pair: PairUnit | None,
) -> str:
    wheel_pair = _pick_best_pair_unit(units, used_ids, "wheel", team_number)

    if wheel_pair is None:
        return "2-1-2"

    if force_simo_single_lead:
        return "1-2-2"

    lead_pair_score = _pair_role_score(preferred_lead_pair, "lead", team_number) if preferred_lead_pair else -inf
    if preferred_lead_pair is None:
        best_lead_pair = _pick_best_pair_unit(units, used_ids, "lead", team_number)
        lead_pair_score = _pair_role_score(best_lead_pair, "lead", team_number) if best_lead_pair else -inf

    team_pair = _pick_best_pair_unit(units, used_ids, "team", team_number)
    team_pair_score = _pair_role_score(team_pair, "team", team_number) if team_pair else -inf

    single_lead = _pick_best_single_for_role(candidates, units, used_ids, "lead", team_number)
    single_lead_score = single_lead.score + _role_fit_score(single_lead.dog, "lead", team_number) if single_lead else -inf

    single_center = _pick_best_single_for_role(
        candidates,
        units,
        used_ids,
        "team",
        team_number,
        prefer_single_center=True,
    )
    single_center_score = (
        single_center.score + _role_fit_score(single_center.dog, "team", team_number)
        if single_center
        else -inf
    )

    option_122 = single_lead_score + team_pair_score
    option_212 = lead_pair_score + single_center_score

    if option_122 == -inf and option_212 == -inf:
        return "2-1-2"

    if option_122 >= option_212:
        return "1-2-2"

    return "2-1-2"


def _assemble_five_dog_team(
    candidates: list[CandidateDog],
    units: list[PairUnit],
    used_ids: set[int],
    team_number: int,
    force_simo_single_lead: bool,
    preferred_lead_pair: PairUnit | None,
) -> tuple[list[SelectedUnit], list[str], str]:
    selected: list[SelectedUnit] = []
    warnings: list[str] = []

    layout = _choose_five_layout(
        candidates=candidates,
        units=units,
        used_ids=used_ids,
        team_number=team_number,
        force_simo_single_lead=force_simo_single_lead,
        preferred_lead_pair=preferred_lead_pair,
    )

    if layout == "1-2-2":
        single_lead = None

        if force_simo_single_lead:
            single_lead = _pick_named_single(candidates, used_ids, "lead", "SIMO")

        if single_lead is None:
            single_lead = _pick_best_single_for_role(candidates, units, used_ids, "lead", team_number)

        if single_lead is None:
            warnings.append("Missing single lead for 1-2-2 structure.")
        else:
            relation = "single_lead" if normalize_name(single_lead.dog.name) == "SIMO" else "single_fallback"
            _add_selected_single(selected, used_ids, single_lead, "lead", relation=relation)

        team_pair = _pick_best_pair_unit(
            units,
            used_ids,
            "team",
            team_number,
            allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
        )
        if team_pair is None:
            warnings.append("Missing center pair for 1-2-2 structure.")
        else:
            _add_selected_unit(selected, used_ids, team_pair, "team")

        wheel_pair = _pick_best_pair_unit(
            units,
            used_ids,
            "wheel",
            team_number,
            allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
        )
        if wheel_pair is None:
            warnings.append("Missing wheel pair for 1-2-2 structure.")
        else:
            _add_selected_unit(selected, used_ids, wheel_pair, "wheel")

    else:
        lead_pair = preferred_lead_pair
        if lead_pair is None:
            lead_pair = _pick_best_pair_unit(
                units,
                used_ids,
                "lead",
                team_number,
                allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
            )

        if lead_pair is None:
            warnings.append("Missing lead pair for 2-1-2 structure.")
        else:
            _add_selected_unit(selected, used_ids, lead_pair, "lead")

        single_center = _pick_best_single_for_role(
            candidates,
            units,
            used_ids,
            "team",
            team_number,
            prefer_single_center=True,
        )
        if single_center is None:
            warnings.append("Missing single center dog for 2-1-2 structure.")
        else:
            _add_selected_single(selected, used_ids, single_center, "team", relation="single_center")

        wheel_pair = _pick_best_pair_unit(
            units,
            used_ids,
            "wheel",
            team_number,
            allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
        )
        if wheel_pair is None:
            warnings.append("Missing wheel pair for 2-1-2 structure.")
        else:
            _add_selected_unit(selected, used_ids, wheel_pair, "wheel")

    return selected, warnings, layout


def _assemble_six_dog_team(
    units: list[PairUnit],
    used_ids: set[int],
    team_number: int,
    preferred_lead_pair: PairUnit | None,
) -> tuple[list[SelectedUnit], list[str]]:
    selected: list[SelectedUnit] = []
    warnings: list[str] = []

    lead_pair = preferred_lead_pair
    if lead_pair is None:
        lead_pair = _pick_best_pair_unit(
            units,
            used_ids,
            "lead",
            team_number,
            allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
        )

    if lead_pair is None:
        warnings.append("Missing lead pair for 2-2-2 structure.")
    else:
        _add_selected_unit(selected, used_ids, lead_pair, "lead")

    team_pair = _pick_best_pair_unit(
        units,
        used_ids,
        "team",
        team_number,
        allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
    )
    if team_pair is None:
        warnings.append("Missing center pair for 2-2-2 structure.")
    else:
        _add_selected_unit(selected, used_ids, team_pair, "team")

    wheel_pair = _pick_best_pair_unit(
        units,
        used_ids,
        "wheel",
        team_number,
        allow_relations={"forced_pair", "home_pair", "preferred_pair", "allowed_pair"},
    )
    if wheel_pair is None:
        warnings.append("Missing wheel pair for 2-2-2 structure.")
    else:
        _add_selected_unit(selected, used_ids, wheel_pair, "wheel")

    return selected, warnings


def _find_safe_pair_completion_for_single_center(
    single_center: CandidateDog,
    candidates: list[CandidateDog],
    used_ids: set[int],
    home_index: dict[tuple[str | None, int | None], list[Dog]],
) -> CandidateDog | None:
    if _prefer_single_team_position(single_center.dog):
        return None

    best = None
    best_score = -inf

    for cand in candidates:
        if cand.dog.id in used_ids:
            continue
        if cand.dog.id == single_center.dog.id:
            continue
        if not _can_fill_role(cand.dog, "team"):
            continue
        if _prefer_single_team_position(cand.dog):
            continue

        pair_ok, relation = _is_pair_known_safe(single_center.dog, cand.dog, home_index)
        if not pair_ok or relation is None:
            continue

        score = cand.score + _pair_relation_bonus(relation)
        if score > best_score:
            best_score = score
            best = cand

    return best


def _find_safe_pair_completion_for_single_lead(
    single_lead: CandidateDog,
    candidates: list[CandidateDog],
    used_ids: set[int],
    home_index: dict[tuple[str | None, int | None], list[Dog]],
) -> CandidateDog | None:
    if normalize_name(single_lead.dog.name) == "SIMO":
        return None

    best = None
    best_score = -inf

    for cand in candidates:
        if cand.dog.id in used_ids:
            continue
        if cand.dog.id == single_lead.dog.id:
            continue
        if not _can_fill_role(cand.dog, "lead"):
            continue

        pair_ok, relation = _is_pair_known_safe(single_lead.dog, cand.dog, home_index)
        if not pair_ok or relation is None:
            continue

        score = cand.score + _pair_relation_bonus(relation)
        if score > best_score:
            best_score = score
            best = cand

    return best


def _current_layout_type(selected: list[SelectedUnit]) -> str:
    lead_rows = [unit for unit in selected if unit.row_role == "lead"]
    team_rows = [unit for unit in selected if unit.row_role == "team"]
    wheel_rows = [unit for unit in selected if unit.row_role == "wheel"]

    lead_pattern = "".join("2" if row.row_type == "pair" else "1" for row in lead_rows)
    team_pattern = "".join("2" if row.row_type == "pair" else "1" for row in team_rows)
    wheel_pattern = "".join("2" if row.row_type == "pair" else "1" for row in wheel_rows)

    if lead_pattern == "1" and team_pattern == "2" and wheel_pattern == "2":
        return "1-2-2"
    if lead_pattern == "2" and team_pattern == "1" and wheel_pattern == "2":
        return "2-1-2"
    if lead_pattern == "2" and team_pattern == "2" and wheel_pattern == "2":
        return "2-2-2"
    return "custom"


def _convert_five_to_six_if_safe(
    selected: list[SelectedUnit],
    candidates: list[CandidateDog],
    used_ids: set[int],
    home_index: dict[tuple[str | None, int | None], list[Dog]],
) -> bool:
    layout_type = _current_layout_type(selected)

    if layout_type == "2-1-2":
        team_single = None
        for unit in selected:
            if unit.row_role == "team" and unit.row_type == "single":
                team_single = unit
                break

        if team_single is None:
            return False

        base_dog = team_single.dogs[0]
        partner = _find_safe_pair_completion_for_single_center(
            single_center=base_dog,
            candidates=candidates,
            used_ids=used_ids,
            home_index=home_index,
        )

        if partner is None:
            return False

        used_ids.add(partner.dog.id)
        team_single.dogs.append(partner)
        team_single.row_type = "pair"
        team_single.relation = "allowed_pair"
        team_single.warnings = ["Added as optional sixth dog."]
        return True

    if layout_type == "1-2-2":
        lead_single = None
        for unit in selected:
            if unit.row_role == "lead" and unit.row_type == "single":
                lead_single = unit
                break

        if lead_single is None:
            return False

        base_dog = lead_single.dogs[0]
        partner = _find_safe_pair_completion_for_single_lead(
            single_lead=base_dog,
            candidates=candidates,
            used_ids=used_ids,
            home_index=home_index,
        )

        if partner is None:
            return False

        used_ids.add(partner.dog.id)
        lead_single.dogs.append(partner)
        lead_single.row_type = "pair"
        lead_single.relation = "allowed_pair"
        lead_single.warnings = ["Added as optional sixth dog."]
        return True

    return False


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

    home_index = _build_home_index(dogs)
    pair_units = _build_pair_units(candidates, home_index)

    needed_total_min = request.team_count * request.min_dogs_per_team
    global_warnings: list[str] = []

    if len(candidates) < needed_total_min:
        global_warnings.append(
            f"Not enough eligible dogs for minimum plan: need {needed_total_min}, have {len(candidates)}."
        )

    used_ids: set[int] = set()
    teams: list[SuggestedTeam] = []

    simo_team_one = False

    for team_number in range(1, request.team_count + 1):
        warnings: list[str] = []

        preferred_team_size = 5 if request.min_dogs_per_team <= 5 <= request.max_dogs_per_team else request.min_dogs_per_team
        target_size = 6 if request.min_dogs_per_team >= 6 else preferred_team_size

        force_simo_single_lead = False
        preferred_lead_pair = None

        simo_available = _pick_named_single(candidates, used_ids, "lead", "SIMO")
        pappi_mirella_pair = _pick_named_pair_unit(
            units=pair_units,
            used_ids=used_ids,
            role="lead",
            left_name="PAPPI",
            right_name="MIRELLA",
        )

        if target_size == 5 and team_number == 1 and simo_available is not None:
            force_simo_single_lead = True
            simo_team_one = True

        if simo_team_one and team_number == 2 and pappi_mirella_pair is not None:
            preferred_lead_pair = pappi_mirella_pair
        elif not simo_team_one and team_number == 1 and pappi_mirella_pair is not None:
            preferred_lead_pair = pappi_mirella_pair

        if target_size == 5:
            selected, build_warnings, _layout_type = _assemble_five_dog_team(
                candidates=candidates,
                units=pair_units,
                used_ids=used_ids,
                team_number=team_number,
                force_simo_single_lead=force_simo_single_lead,
                preferred_lead_pair=preferred_lead_pair,
            )
            warnings.extend(build_warnings)

            if request.max_dogs_per_team >= 6 and request.min_dogs_per_team < request.max_dogs_per_team:
                _convert_five_to_six_if_safe(
                    selected=selected,
                    candidates=candidates,
                    used_ids=used_ids,
                    home_index=home_index,
                )
        else:
            selected, build_warnings = _assemble_six_dog_team(
                units=pair_units,
                used_ids=used_ids,
                team_number=team_number,
                preferred_lead_pair=preferred_lead_pair,
            )
            warnings.extend(build_warnings)

        flat_assignments = _flatten_assignments_from_selected(selected)
        layout = _build_layout_from_selected(selected)

        teams.append(
            SuggestedTeam(
                team_number=team_number,
                dogs=flat_assignments,
                layout=layout,
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