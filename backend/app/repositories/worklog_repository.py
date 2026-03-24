from sqlalchemy.orm import Session

from app.models.worklog import Worklog
from app.schemas.worklog import WorklogCreate


class WorklogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: WorklogCreate) -> Worklog:
        worklog = Worklog(**payload.model_dump())
        self.db.add(worklog)
        self.db.commit()
        self.db.refresh(worklog)
        return worklog
