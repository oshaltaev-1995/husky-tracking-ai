from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


RelationType = Literal["forced_pair", "preferred_pair", "allowed_pair", "avoid_pair"]


@dataclass
class DogRule:
    dog_name: str
    solo_only: bool = False
    big_sled_only: bool = False
    lead_only: bool = False
    avoid_home_pair: bool = False
    solo_team_allowed: bool = True
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


def get_preferred_partner_names(dog, all_dogs_by_home: dict[tuple[str | None, int | None], list]) -> list[str]:
    dog_name = normalize_name(dog.name)
    rule = get_rule(dog_name)

    partners: list[str] = []

    # home pair by default
    home_partner = get_home_partner_name(dog, all_dogs_by_home)
    if home_partner:
        partners.append(normalize_name(home_partner))

    # explicit rules
    if rule:
        if rule.avoid_home_pair and home_partner:
            partners = [p for p in partners if p != normalize_name(home_partner)]

        partners.extend(rule.forced_partners)
        partners.extend(rule.preferred_partners)
        partners.extend(rule.allowed_partners)

        for avoid_name in rule.avoid_partners:
            partners = [p for p in partners if p != normalize_name(avoid_name)]

    # unique keep order
    seen = set()
    return [p for p in partners if not (p in seen or seen.add(p))]


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