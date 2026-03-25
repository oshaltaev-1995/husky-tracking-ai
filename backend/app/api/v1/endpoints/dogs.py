from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.dog_repository import DogRepository
from app.schemas.dog import DogCreate, DogRead

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


@router.post("/", response_model=DogRead, status_code=201)
def create_dog(payload: DogCreate, db: Session = Depends(get_db)):
    return DogRepository(db).create(payload)