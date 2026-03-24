from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.worklog import Worklog


class WorkloadService:
    def __init__(self, db: Session):
        self.db = db

    def total_km_by_dog(self) -> list[dict]:
        rows = (
            self.db.query(Worklog.dog_id, func.sum(Worklog.km).label("total_km"))
            .group_by(Worklog.dog_id)
            .all()
        )
        return [{"dog_id": row.dog_id, "total_km": float(row.total_km or 0)} for row in rows]
