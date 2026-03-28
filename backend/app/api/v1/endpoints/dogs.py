from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.dog_repository import DogRepository
from app.schemas.dog import DogCreate, DogRead
from app.schemas.risk import DogRiskSummary
from app.schemas.workload import DogWorkloadSummary
from app.services.risk_service import get_dog_risk_summary
from app.services.workload_service import get_dog_workload_summary

router = APIRouter()


@router.get("/", response_model=list[DogRead])
def list_dogs(db: Session = Depends(get_db)):
    return DogRepository(db).list_all()


@router.get("/{dog_id}", response_model=DogRead)
def get_dog(dog_id: int, db: Session = Depends(get_db)):
    dog = DogRepository(db).get_by_id(dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return dog


@router.get("/{dog_id}/workload", response_model=DogWorkloadSummary)
def get_dog_workload(
    dog_id: int,
    hard_day_km_threshold: float = Query(default=10.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    db: Session = Depends(get_db),
):
    summary = get_dog_workload_summary(
        db=db,
        dog_id=dog_id,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return summary


@router.get("/{dog_id}/risk", response_model=DogRiskSummary)
def get_dog_risk(
    dog_id: int,
    hard_day_km_threshold: float = Query(default=10.0, gt=0),
    recent_days: int = Query(default=14, ge=1, le=60),
    db: Session = Depends(get_db),
):
    summary = get_dog_risk_summary(
        db=db,
        dog_id=dog_id,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Dog with id={dog_id} not found")
    return summary


@router.post("/", response_model=DogRead, status_code=201)
def create_dog(payload: DogCreate, db: Session = Depends(get_db)):
    return DogRepository(db).create(payload)