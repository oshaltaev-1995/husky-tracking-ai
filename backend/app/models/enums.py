from enum import Enum


class LifecycleStatus(str, Enum):
    active = "active"
    retired = "retired"
    deceased = "deceased"
    archived = "archived"


class AvailabilityStatus(str, Enum):
    available = "available"
    injured = "injured"
    sick = "sick"
    treatment = "treatment"
    rest = "rest"
    restricted = "restricted"