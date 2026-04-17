from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Dog, Worklog
from app.schemas.worklog_entry import WorklogEntryCreate, WorklogEntryRead

router = APIRouter(prefix="/worklogs", tags=["worklogs-entry"])


@router.get("/by-date", response_model=list[WorklogEntryRead])
def list_worklogs_by_date(
    work_date: date = Query(...),
    db: Session = Depends(get_db),
):
    rows = list(
        db.execute(
            select(Worklog)
            .where(Worklog.work_date == work_date)
            .order_by(Worklog.dog_id.asc(), Worklog.id.asc())
        ).scalars().all()
    )
    return rows


@router.post("/log-run", response_model=WorklogEntryRead, status_code=201)
def log_work_run(
    payload: WorklogEntryCreate,
    db: Session = Depends(get_db),
):
    dog = db.execute(select(Dog).where(Dog.id == payload.dog_id)).scalar_one_or_none()
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={payload.dog_id} not found")

    existing = db.execute(
        select(Worklog).where(
            Worklog.dog_id == payload.dog_id,
            Worklog.work_date == payload.work_date,
        )
    ).scalar_one_or_none()

    if existing is None:
        row = Worklog(
            dog_id=payload.dog_id,
            work_date=payload.work_date,
            week_label=payload.week_label,
            km=payload.km,
            worked=payload.worked,
            programs_10km=payload.programs_10km,
            programs_3km=payload.programs_3km,
            kennel_row=payload.kennel_row,
            home_slot=payload.home_slot,
            status=payload.status,
            main_role=payload.main_role,
            notes=payload.notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    existing.week_label = payload.week_label
    existing.km = payload.km
    existing.worked = payload.worked
    existing.programs_10km = payload.programs_10km
    existing.programs_3km = payload.programs_3km
    existing.kennel_row = payload.kennel_row
    existing.home_slot = payload.home_slot
    existing.status = payload.status
    existing.main_role = payload.main_role
    existing.notes = payload.notes

    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing