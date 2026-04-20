from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    WeeklyAnalyticsResponse,
    WeeklyCompareResponse,
)
from app.services.analytics_service import (
    get_analytics_summary,
    get_weekly_analytics,
    get_weekly_compare,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/weekly", response_model=WeeklyAnalyticsResponse)
def analytics_weekly(
    date_from: date = Query(...),
    date_to: date = Query(...),
    hard_day_km_threshold: float = Query(default=10.0),
    recent_days: int = Query(default=14),
    db: Session = Depends(get_db),
):
    return get_weekly_analytics(
        db=db,
        date_from=date_from,
        date_to=date_to,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def analytics_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    hard_day_km_threshold: float = Query(default=10.0),
    recent_days: int = Query(default=14),
    db: Session = Depends(get_db),
):
    return get_analytics_summary(
        db=db,
        date_from=date_from,
        date_to=date_to,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )


@router.get("/weekly-compare", response_model=WeeklyCompareResponse)
def analytics_weekly_compare(
    week_a_start: date = Query(...),
    week_b_start: date = Query(...),
    hard_day_km_threshold: float = Query(default=10.0),
    recent_days: int = Query(default=14),
    db: Session = Depends(get_db),
):
    return get_weekly_compare(
        db=db,
        week_a_start=week_a_start,
        week_b_start=week_b_start,
        hard_day_km_threshold=hard_day_km_threshold,
        recent_days=recent_days,
    )