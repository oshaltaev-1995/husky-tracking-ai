from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog


DATA_FILE = Path("/app/data/raw/vanha_puoli_dataset.xlsx")


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value != "" else None
    return value


def _to_bool(value: Any) -> bool:
    if pd.isna(value) or value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "worked", "x"}


def _to_int(value: Any, default: int = 0) -> int:
    if pd.isna(value) or value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    if pd.isna(value) or value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_date(value: Any):
    if pd.isna(value) or value is None:
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()


def _normalize_name(value: Any) -> str | None:
    value = _clean_value(value)
    if value is None:
        return None
    return str(value).strip()


def import_excel_to_db(db: Session, file_path: Path = DATA_FILE) -> dict[str, int]:
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    dogs_created = 0
    dogs_updated = 0
    worklogs_created = 0
    worklogs_updated = 0

    # dogs_static: первая строка у тебя служебная, заголовки со 2-й строки
    dogs_df = pd.read_excel(
        file_path,
        sheet_name="dogs_static",
        header=1,
    )

    # daily_work: обычная таблица
    work_df = pd.read_excel(
        file_path,
        sheet_name="daily_work",
    )

    dogs_df.columns = [str(col).strip() for col in dogs_df.columns]
    work_df.columns = [str(col).strip() for col in work_df.columns]

    # --- Импорт dogs ---
    for _, row in dogs_df.iterrows():
        name = _normalize_name(row.get("dog_name") or row.get("name"))
        if not name:
            continue

        stmt = select(Dog).where(Dog.name == name)
        dog = db.execute(stmt).scalar_one_or_none()

        payload = {
            "sex": _clean_value(row.get("sex")),
            "birth_year": _to_int(row.get("birth_year"), default=None) if _clean_value(row.get("birth_year")) is not None else None,
            "age_years": _to_int(row.get("age_years"), default=None) if _clean_value(row.get("age_years")) is not None else None,
            "status": _clean_value(row.get("status")),
            "main_role": _clean_value(row.get("main_role")),
            "kennel_row": _clean_value(row.get("kennel_row")),
            "home_slot": _clean_value(row.get("home_slot")),
            "notes": _clean_value(row.get("notes")),
            "is_active": True,
        }

        if dog is None:
            dog = Dog(name=name, **payload)
            db.add(dog)
            dogs_created += 1
        else:
            dog.sex = payload["sex"]
            dog.birth_year = payload["birth_year"]
            dog.age_years = payload["age_years"]
            dog.status = payload["status"]
            dog.main_role = payload["main_role"]
            dog.kennel_row = payload["kennel_row"]
            dog.home_slot = payload["home_slot"]
            dog.notes = payload["notes"]
            dog.is_active = payload["is_active"]
            dogs_updated += 1

    db.flush()

    # Индекс собак по имени
    dogs_by_name = {
        dog.name: dog
        for dog in db.execute(select(Dog)).scalars().all()
    }

    # --- Импорт worklogs ---
    for _, row in work_df.iterrows():
        dog_name = _normalize_name(row.get("dog_name"))
        if not dog_name:
            continue

        dog = dogs_by_name.get(dog_name)
        if dog is None:
            # если собака есть в daily_work, но нет в dogs_static
            dog = Dog(name=dog_name, is_active=True)
            db.add(dog)
            db.flush()
            dogs_by_name[dog_name] = dog
            dogs_created += 1

        work_date = _to_date(row.get("date"))
        if work_date is None:
            continue

        stmt = select(Worklog).where(
            Worklog.dog_id == dog.id,
            Worklog.work_date == work_date,
        )
        worklog = db.execute(stmt).scalar_one_or_none()

        payload = {
            "week_label": _clean_value(row.get("week")),
            "km": _to_float(row.get("km"), default=0.0),
            "worked": _to_bool(row.get("worked")),
            "programs_10km": _to_int(row.get("programs_10km"), default=0),
            "programs_3km": _to_int(row.get("programs_3km"), default=0),
            "kennel_row": _clean_value(row.get("kennel_row")),
            "home_slot": _clean_value(row.get("home_slot")),
            "status": _clean_value(row.get("status")),
            "main_role": _clean_value(row.get("main_role")),
            "notes": _clean_value(row.get("notes")),
        }

        if worklog is None:
            worklog = Worklog(
                dog_id=dog.id,
                work_date=work_date,
                **payload,
            )
            db.add(worklog)
            worklogs_created += 1
        else:
            worklog.week_label = payload["week_label"]
            worklog.km = payload["km"]
            worklog.worked = payload["worked"]
            worklog.programs_10km = payload["programs_10km"]
            worklog.programs_3km = payload["programs_3km"]
            worklog.kennel_row = payload["kennel_row"]
            worklog.home_slot = payload["home_slot"]
            worklog.status = payload["status"]
            worklog.main_role = payload["main_role"]
            worklog.notes = payload["notes"]
            worklogs_updated += 1

    db.commit()

    return {
        "dogs_created": dogs_created,
        "dogs_updated": dogs_updated,
        "worklogs_created": worklogs_created,
        "worklogs_updated": worklogs_updated,
    }