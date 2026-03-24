from sqlalchemy.orm import Session

from app.models.dog import Dog
from app.schemas.dog import DogCreate


class DogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Dog]:
        return self.db.query(Dog).order_by(Dog.name.asc()).all()

    def create(self, payload: DogCreate) -> Dog:
        dog = Dog(**payload.model_dump())
        self.db.add(dog)
        self.db.commit()
        self.db.refresh(dog)
        return dog
