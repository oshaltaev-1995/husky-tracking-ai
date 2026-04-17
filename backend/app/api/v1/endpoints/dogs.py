from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.dog_repository import DogRepository
from app.schemas.attention import DogAttentionListResponse
from app.schemas.dog import DogCreate, DogRead, DogUpdate
from app.schemas.dog_status import DogEligibilityRead, DogStatusUpdate
from app.schemas.dog_summary import DogSummaryRead
from app.schemas.risk import DogRiskSummary
from app.schemas.workload import DogWorkloadSummary
from app.services.dog_summary_service import get_dogs_summary
from app.services.eligibility_service import get_team_builder_eligibility
from app.services.risk_service import get_dog_risk_summary
from app.services.segmentation_service import (
    get_operational_watchlist,
    get_planning_blockers,
    get_underused_candidates,
)
from app.services.workload_service import get_dog_workload_summary

router = APIRouter()


@router.get("/", response_model=list[DogRead])
def list_dogs(db: Session = Depends(get_db)):
    return DogRepository(db).list_all()


@router.post("/", response_model=DogRead, status_code=201)
def create_dog(payload: DogCreate, db: Session = Depends(get_db)):
    return DogRepository(db).create(payload)


@router.get("/summary", response_model=list[DogSummaryRead])
def list_dogs_summary(
    hard_day_km_threshold: float = Query(default=15.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_dogs_summary(
        db=db,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
        as_of_date=as_of_date,
    )


@router.get("/eligible-for-team-builder", response_model=list[DogEligibilityRead])
def list_eligible_for_team_builder(db: Session = Depends(get_db)):
    dogs = DogRepository(db).list_team_builder_candidates()
    result: list[DogEligibilityRead] = []

    for dog in dogs:
        eligibility = get_team_builder_eligibility(dog)
        if eligibility.eligible_for_team_builder:
            result.append(eligibility)

    return result


@router.get("/planning-blockers", response_model=DogAttentionListResponse)
def planning_blockers(
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_planning_blockers(db, as_of_date=as_of_date)


@router.get("/operational-watchlist", response_model=DogAttentionListResponse)
def operational_watchlist(
    hard_day_km_threshold: float = Query(default=15.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_operational_watchlist(
        db=db,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
        as_of_date=as_of_date,
    )


@router.get("/underused", response_model=DogAttentionListResponse)
def underused_candidates(
    hard_day_km_threshold: float = Query(default=15.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_underused_candidates(
        db=db,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
        as_of_date=as_of_date,
    )


@router.get("/{dog_id}", response_model=DogRead)
def get_dog(dog_id: int, db: Session = Depends(get_db)):
    dog = DogRepository(db).get_by_id(dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return dog


@router.patch("/{dog_id}", response_model=DogRead)
def update_dog(
    dog_id: int,
    payload: DogUpdate,
    db: Session = Depends(get_db),
):
    repo = DogRepository(db)
    dog = repo.get_by_id(dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return repo.update(dog, payload)


@router.patch("/{dog_id}/status", response_model=DogRead)
def update_dog_status(
    dog_id: int,
    payload: DogStatusUpdate,
    db: Session = Depends(get_db),
):
    repo = DogRepository(db)
    dog = repo.get_by_id(dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return repo.update_status(dog, payload)


@router.get("/{dog_id}/eligibility", response_model=DogEligibilityRead)
def get_dog_eligibility(
    dog_id: int,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    dog = DogRepository(db).get_by_id(dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return get_team_builder_eligibility(dog, as_of_date)


@router.get("/{dog_id}/workload", response_model=DogWorkloadSummary)
def get_dog_workload(
    dog_id: int,
    hard_day_km_threshold: float = Query(default=15.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    summary = get_dog_workload_summary(
        db=db,
        dog_id=dog_id,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
        as_of_date=as_of_date,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return summary


@router.get("/{dog_id}/risk", response_model=DogRiskSummary)
def get_dog_risk(
    dog_id: int,
    hard_day_km_threshold: float = Query(default=15.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    summary = get_dog_risk_summary(
        db=db,
        dog_id=dog_id,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
        as_of_date=as_of_date,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return summary