from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.export_service import (
    build_analytics_summary_pdf,
    build_analytics_workbook,
    build_raw_run_logs_csv,
)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/analytics-workbook.xlsx")
def export_analytics_workbook(
    date_from: date = Query(...),
    date_to: date = Query(...),
    week_a_start: date | None = Query(default=None),
    week_b_start: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    content = build_analytics_workbook(
        db=db,
        date_from=date_from,
        date_to=date_to,
        week_a_start=week_a_start,
        week_b_start=week_b_start,
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"husky-analytics-{date_from.isoformat()}-to-{date_to.isoformat()}-{timestamp}.xlsx"

    return StreamingResponse(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/analytics-summary.pdf")
def export_analytics_summary_pdf(
    date_from: date = Query(...),
    date_to: date = Query(...),
    week_a_start: date | None = Query(default=None),
    week_b_start: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    content = build_analytics_summary_pdf(
        db=db,
        date_from=date_from,
        date_to=date_to,
        week_a_start=week_a_start,
        week_b_start=week_b_start,
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"husky-analytics-summary-{date_from.isoformat()}-to-{date_to.isoformat()}-{timestamp}.pdf"

    return StreamingResponse(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/raw-run-logs.csv")
def export_raw_run_logs_csv(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
):
    content, filename = build_raw_run_logs_csv(
        db=db,
        date_from=date_from,
        date_to=date_to,
    )

    return StreamingResponse(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )