from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardHeatmapResponse,
    DashboardOverviewResponse,
    DashboardTodayResponse,
)
from app.services.dashboard_service import (
    get_dashboard_heatmap,
    get_dashboard_overview,
    get_dashboard_today,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_dashboard_overview(db=db, as_of_date=as_of_date)


@router.get("/today", response_model=DashboardTodayResponse)
def dashboard_today(
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_dashboard_today(db=db, as_of_date=as_of_date)


@router.get("/heatmap", response_model=DashboardHeatmapResponse)
def dashboard_heatmap(
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_dashboard_heatmap(db=db, as_of_date=as_of_date)