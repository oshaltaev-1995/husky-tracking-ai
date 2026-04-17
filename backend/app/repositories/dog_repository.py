from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog
from app.schemas.dog import DogCreate, DogUpdate
from app.schemas.dog_status import DogStatusUpdate


class DogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Dog]:
        stmt = select(Dog).order_by(Dog.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, dog_id: int) -> Dog | None:
        stmt = select(Dog).where(Dog.id == dog_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, payload: DogCreate) -> Dog:
        dog = Dog(**payload.model_dump())
        self.db.add(dog)
        self.db.commit()
        self.db.refresh(dog)
        return dog

    def update(self, dog: Dog, payload: DogUpdate) -> Dog:
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(dog, field, value)

        self.db.add(dog)
        self.db.commit()
        self.db.refresh(dog)
        return dog

    def update_status(self, dog: Dog, payload: DogStatusUpdate) -> Dog:
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(dog, field, value)

        self.db.add(dog)
        self.db.commit()
        self.db.refresh(dog)
        return dog

    def list_team_builder_candidates(self) -> list[Dog]:
        stmt = select(Dog).order_by(Dog.name.asc())
        return list(self.db.execute(stmt).scalars().all())