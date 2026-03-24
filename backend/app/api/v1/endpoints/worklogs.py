from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.worklog_repository import WorklogRepository
from app.schemas.worklog import WorklogCreate, WorklogRead

router = APIRouter()


@router.post("/", response_model=WorklogRead, status_code=201)
def create_worklog(payload: WorklogCreate, db: Session = Depends(get_db)):
    return WorklogRepository(db).create(payload)
