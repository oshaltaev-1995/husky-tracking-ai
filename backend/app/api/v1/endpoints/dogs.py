from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.dog_repository import DogRepository
from app.schemas.dog import DogCreate, DogRead

router = APIRouter()


@router.get("/", response_model=list[DogRead])
def list_dogs(db: Session = Depends(get_db)):
    return DogRepository(db).list_all()


@router.post("/", response_model=DogRead, status_code=201)
def create_dog(payload: DogCreate, db: Session = Depends(get_db)):
    return DogRepository(db).create(payload)
