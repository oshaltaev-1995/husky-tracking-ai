from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


RelationType = Literal["forced_pair", "home_pair", "preferred_pair", "allowed_pair"]


@dataclass
class PartnerOption:
    partner_name: str
    relation: RelationType


@dataclass
class DogRule:
    dog_name: str

    solo_only: bool = False
    big_sled_only: bool = False
    lead_only: bool = False

    avoid_home_pair: bool = False
    preserve_home_pair: bool = True
    solo_team_allowed: bool = True

    preferred_team_number: int | None = None
    preferred_role: str | None = None

    forced_partners: list[str] = field(default_factory=list)
    preferred_partners: list[str] = field(default_factory=list)
    allowed_partners: list[str] = field(default_factory=list)
    avoid_partners: list[str] = field(default_factory=list)


DOG_RULES: dict[str, DogRule] = {
    "BOBBY": DogRule(
        dog_name="BOBBY",
        allowed_partners=["POPPANA", "FOX", "FOREST", "DIMMU"],
    ),
    "ESKO": DogRule(
        dog_name="ESKO",
        preferred_partners=["PUHTI"],
        solo_team_allowed=True,
    ),
    "PUHTI": DogRule(
        dog_name="PUHTI",
        preferred_partners=["ESKO"],
        solo_team_allowed=True,
    ),
    "VIPER": DogRule(
        dog_name="VIPER",
        avoid_home_pair=True,
        solo_team_allowed=True,
    ),
    "VIRTA": DogRule(
        dog_name="VIRTA",
        avoid_home_pair=True,
        solo_team_allowed=True,
    ),
    "HELLE": DogRule(
        dog_name="HELLE",
        forced_partners=["TEX"],
    ),
    "AMOK": DogRule(
        dog_name="AMOK",
        solo_team_allowed=True,
    ),
    "UKKO": DogRule(
        dog_name="UKKO",
        preferred_partners=["DIMMU"],
    ),
    "DIMMU": DogRule(
        dog_name="DIMMU",
        preferred_partners=["UKKO"],
        allowed_partners=["BOBBY"],
        preserve_home_pair=True,
    ),
    "ROLLO": DogRule(
        dog_name="ROLLO",
        solo_only=True,
        big_sled_only=True,
        solo_team_allowed=True,
    ),
    "SIMO": DogRule(
        dog_name="SIMO",
        solo_only=True,
        lead_only=True,
        solo_team_allowed=False,
        preferred_team_number=1,
        preferred_role="lead",
        avoid_partners=["SUMU"],
    ),
    "SUMU": DogRule(
        dog_name="SUMU",
        avoid_home_pair=True,
        solo_team_allowed=True,
        avoid_partners=["SIMO"],
    ),
    "PAPPI": DogRule(
        dog_name="PAPPI",
        forced_partners=["MIRELLA"],
        preferred_team_number=2,
        preferred_role="lead",
    ),
    "MIRELLA": DogRule(
        dog_name="MIRELLA",
        forced_partners=["PAPPI"],
        preferred_team_number=2,
        preferred_role="lead",
    ),
}


def normalize_name(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().upper()


def get_rule(dog_name: str | None) -> DogRule | None:
    return DOG_RULES.get(normalize_name(dog_name))


def get_home_partner_name(dog, all_dogs_by_home: dict[tuple[str | None, int | None], list]) -> str | None:
    key = (dog.kennel_row, dog.home_slot)
    same_home = all_dogs_by_home.get(key, [])

    if len(same_home) != 2:
        return None

    for other in same_home:
        if other.id != dog.id:
            return other.name

    return None


def is_pair_explicitly_avoided(dog_name: str | None, partner_name: str | None) -> bool:
    rule = get_rule(dog_name)
    if rule is None:
        return False

    partner_norm = normalize_name(partner_name)
    return partner_norm in {normalize_name(name) for name in rule.avoid_partners}


def get_partner_options(dog, all_dogs_by_home: dict[tuple[str | None, int | None], list]) -> list[PartnerOption]:
    dog_name = normalize_name(dog.name)
    rule = get_rule(dog_name)

    home_partner = get_home_partner_name(dog, all_dogs_by_home)
    home_partner_norm = normalize_name(home_partner)

    options: list[PartnerOption] = []

    forced_norms = [normalize_name(name) for name in (rule.forced_partners if rule else [])]
    preferred_norms = [normalize_name(name) for name in (rule.preferred_partners if rule else [])]
    allowed_norms = [normalize_name(name) for name in (rule.allowed_partners if rule else [])]
    avoid_norms = {normalize_name(name) for name in (rule.avoid_partners if rule else [])}

    # 1. forced pairs always first
    for partner_name in forced_norms:
        if partner_name and partner_name != dog_name and partner_name not in avoid_norms:
            options.append(PartnerOption(partner_name=partner_name, relation="forced_pair"))

    # 2. home pair stays stronger than alternates unless explicitly avoided
    if home_partner_norm and home_partner_norm != dog_name:
        allow_home_pair = True

        if rule and rule.avoid_home_pair:
            allow_home_pair = False

        if home_partner_norm in avoid_norms:
            allow_home_pair = False

        if allow_home_pair:
            options.append(PartnerOption(partner_name=home_partner_norm, relation="home_pair"))

    # 3. preferred alternates
    for partner_name in preferred_norms:
        if not partner_name or partner_name == dog_name:
            continue
        if partner_name == home_partner_norm:
            continue
        if partner_name in avoid_norms:
            continue
        options.append(PartnerOption(partner_name=partner_name, relation="preferred_pair"))

    # 4. allowed alternates
    for partner_name in allowed_norms:
        if not partner_name or partner_name == dog_name:
            continue
        if partner_name == home_partner_norm:
            continue
        if partner_name in avoid_norms:
            continue
        options.append(PartnerOption(partner_name=partner_name, relation="allowed_pair"))

    seen: set[tuple[str, RelationType]] = set()
    unique: list[PartnerOption] = []

    for option in options:
        key = (option.partner_name, option.relation)
        if key in seen:
            continue
        seen.add(key)
        unique.append(option)

    return unique


def is_solo_only(dog_name: str | None) -> bool:
    rule = get_rule(dog_name)
    return bool(rule and rule.solo_only)


def is_big_sled_only(dog_name: str | None) -> bool:
    rule = get_rule(dog_name)
    return bool(rule and rule.big_sled_only)


def is_lead_only(dog_name: str | None) -> bool:
    rule = get_rule(dog_name)
    return bool(rule and rule.lead_only)


def solo_team_allowed(dog_name: str | None) -> bool:
    rule = get_rule(dog_name)
    if rule is None:
        return True
    return rule.solo_team_allowed


def get_preferred_team_number(dog_name: str | None) -> int | None:
    rule = get_rule(dog_name)
    if rule is None:
        return None
    return rule.preferred_team_number


def get_preferred_role(dog_name: str | None) -> str | None:
    rule = get_rule(dog_name)
    if rule is None:
        return None
    return rule.preferred_role