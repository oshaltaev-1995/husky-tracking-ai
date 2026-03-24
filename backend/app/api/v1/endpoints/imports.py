from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.import_result import ImportResult
from app.services.import_excel import import_excel_to_db

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/excel", response_model=ImportResult)
def import_excel(db: Session = Depends(get_db)) -> ImportResult:
    try:
        result = import_excel_to_db(db)
        return ImportResult(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc