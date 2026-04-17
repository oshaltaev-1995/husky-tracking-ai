from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.team_builder import TeamBuilderRequest, TeamBuilderResponse
from app.services.team_builder_service import build_teams

router = APIRouter(prefix="/team-builder", tags=["team-builder"])


@router.post("/build", response_model=TeamBuilderResponse)
def build_team_plan(
    payload: TeamBuilderRequest,
    db: Session = Depends(get_db),
):
    return build_teams(db=db, request=payload)