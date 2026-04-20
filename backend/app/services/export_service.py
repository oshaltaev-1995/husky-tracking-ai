from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dog, Worklog
from app.models.enums import LifecycleStatus
from app.services.analytics_service import (
    get_analytics_summary,
    get_weekly_analytics,
    get_weekly_compare,
)


THIN_GRAY = Side(style="thin", color="D1D5DB")
BORDER_ALL = Border(left=THIN_GRAY, right=THIN_GRAY, top=THIN_GRAY, bottom=THIN_GRAY)

FILL_TITLE = PatternFill("solid", fgColor="0F172A")
FILL_SECTION = PatternFill("solid", fgColor="E5E7EB")
FILL_HEADER = PatternFill("solid", fgColor="CBD5E1")
FILL_SUBHEADER = PatternFill("solid", fgColor="E2E8F0")
FILL_INFO = PatternFill("solid", fgColor="EFF6FF")
FILL_GOOD = PatternFill("solid", fgColor="ECFDF5")
FILL_WARN = PatternFill("solid", fgColor="FFF7ED")

FONT_TITLE = Font(color="FFFFFF", bold=True, size=14)
FONT_SECTION = Font(color="111827", bold=True, size=12)
FONT_HEADER = Font(color="111827", bold=True)
FONT_BOLD = Font(color="111827", bold=True)

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_WRAP = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _start_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _is_operational_dog(dog: Dog) -> bool:
    lifecycle = str(
        dog.lifecycle_status.value if hasattr(dog.lifecycle_status, "value") else dog.lifecycle_status
    ).lower()
    return lifecycle not in {"archived", "deceased"}


def _autosize_columns(ws, min_width: int = 12, max_width: int = 36) -> None:
    widths: dict[int, int] = {}

    for row in ws.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            length = len(str(cell.value))
            widths[cell.column] = max(widths.get(cell.column, 0), length + 2)

    for column_idx, width in widths.items():
        ws.column_dimensions[get_column_letter(column_idx)].width = max(min_width, min(width, max_width))


def _set_number_formats(ws) -> None:
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, float):
                cell.number_format = "0.00"


def _write_title(ws, title: str, subtitle: str | None = None, width_to_col: int = 9) -> int:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=width_to_col)
    cell = ws.cell(row=1, column=1, value=title)
    cell.fill = FILL_TITLE
    cell.font = FONT_TITLE
    cell.alignment = ALIGN_LEFT
    cell.border = BORDER_ALL
    ws.row_dimensions[1].height = 24

    current_row = 2
    if subtitle:
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width_to_col)
        sub = ws.cell(row=2, column=1, value=subtitle)
        sub.alignment = ALIGN_LEFT
        sub.border = BORDER_ALL
        current_row = 3

    return current_row


def _fetch_operational_dogs(db: Session) -> list[Dog]:
    dogs = list(
        db.execute(
            select(Dog).order_by(
                Dog.kennel_row.asc(),
                Dog.kennel_block.asc(),
                Dog.home_slot.asc(),
                Dog.name.asc(),
            )
        ).scalars().all()
    )
    return [dog for dog in dogs if _is_operational_dog(dog)]


def _fetch_worklogs_in_range(db: Session, date_from: date, date_to: date) -> list[Worklog]:
    return list(
        db.execute(
            select(Worklog)
            .where(Worklog.work_date >= date_from, Worklog.work_date <= date_to)
            .order_by(Worklog.work_date.asc(), Worklog.dog_id.asc(), Worklog.id.asc())
        ).scalars().all()
    )


def _comparison_hint(metric: str, delta: float | int) -> str:
    if delta == 0:
        return "No change"

    if metric in {"total_km", "worked_dogs", "avg_km_per_worked_dog"}:
        return "Improved" if delta > 0 else "Lower"

    if metric in {"high_risk_dogs", "moderate_risk_dogs", "underused_dogs"}:
        return "Reduced" if delta < 0 else "Increased"

    return "Changed"


def _build_overview_sheet(
    wb: Workbook,
    date_from: date,
    date_to: date,
    weekly,
    summary,
    comparison,
) -> None:
    ws = wb.active
    ws.title = "Overview"

    row = _write_title(
        ws,
        title="Husky Tracking AI - Analytics Export",
        subtitle=f"Period: {date_from.isoformat()} → {date_to.isoformat()} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        width_to_col=9,
    )

    ws.cell(row=row, column=1, value="Summary").fill = FILL_SECTION
    ws.cell(row=row, column=1).font = FONT_SECTION
    ws.cell(row=row, column=1).border = BORDER_ALL
    row += 1

    summary_rows = [
        ("Total km", summary.total_km),
        ("Worked dogs", summary.unique_worked_dogs),
        ("Avg km / worked dog", summary.avg_km_per_worked_dog),
        ("Worked dog-days", summary.total_worked_dog_days),
        ("Weeks in export", summary.weeks_count),
        (
            "Latest snapshot",
            f"H {summary.latest_week_snapshot.high_risk_dogs} / "
            f"M {summary.latest_week_snapshot.moderate_risk_dogs} / "
            f"U {summary.latest_week_snapshot.underused_dogs}"
            if summary.latest_week_snapshot
            else "N/A",
        ),
    ]

    for label, value in summary_rows:
        ws.cell(row=row, column=1, value=label).font = FONT_HEADER
        ws.cell(row=row, column=1).fill = FILL_SUBHEADER
        ws.cell(row=row, column=1).border = BORDER_ALL
        ws.cell(row=row, column=2, value=value).border = BORDER_ALL
        ws.cell(row=row, column=2).alignment = ALIGN_LEFT
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Weekly summary").fill = FILL_SECTION
    ws.cell(row=row, column=1).font = FONT_SECTION
    ws.cell(row=row, column=1).border = BORDER_ALL
    row += 1

    headers = [
        "week_start",
        "week_end",
        "week_label",
        "total_km",
        "worked_dogs",
        "avg_km_per_worked_dog",
        "high_risk_dogs",
        "moderate_risk_dogs",
        "underused_dogs",
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_ALL

    row += 1
    for item in weekly.items:
        values = [
            item.week_start.isoformat(),
            item.week_end.isoformat(),
            item.week_label,
            item.total_km,
            item.worked_dogs,
            item.avg_km_per_worked_dog,
            item.high_risk_dogs,
            item.moderate_risk_dogs,
            item.underused_dogs,
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = BORDER_ALL
            cell.alignment = ALIGN_LEFT if col <= 3 else ALIGN_CENTER
        row += 1

    if comparison is not None:
        row += 1
        ws.cell(row=row, column=1, value="Selected week comparison").fill = FILL_SECTION
        ws.cell(row=row, column=1).font = FONT_SECTION
        ws.cell(row=row, column=1).border = BORDER_ALL
        row += 1

        compare_headers = ["metric", "week_a", "week_b", "delta", "note"]
        for col, header in enumerate(compare_headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = FILL_HEADER
            cell.font = FONT_HEADER
            cell.alignment = ALIGN_CENTER
            cell.border = BORDER_ALL

        row += 1
        compare_rows = [
            ("total_km", comparison.week_a.total_km, comparison.week_b.total_km, comparison.delta.total_km),
            ("worked_dogs", comparison.week_a.worked_dogs, comparison.week_b.worked_dogs, comparison.delta.worked_dogs),
            (
                "avg_km_per_worked_dog",
                comparison.week_a.avg_km_per_worked_dog,
                comparison.week_b.avg_km_per_worked_dog,
                comparison.delta.avg_km_per_worked_dog,
            ),
            ("high_risk_dogs", comparison.week_a.high_risk_dogs, comparison.week_b.high_risk_dogs, comparison.delta.high_risk_dogs),
            (
                "moderate_risk_dogs",
                comparison.week_a.moderate_risk_dogs,
                comparison.week_b.moderate_risk_dogs,
                comparison.delta.moderate_risk_dogs,
            ),
            ("underused_dogs", comparison.week_a.underused_dogs, comparison.week_b.underused_dogs, comparison.delta.underused_dogs),
        ]

        for metric, week_a, week_b, delta in compare_rows:
            values = [metric, week_a, week_b, delta, _comparison_hint(metric, delta)]
            for col, value in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = BORDER_ALL
                cell.alignment = ALIGN_CENTER if col > 1 else ALIGN_LEFT
            row += 1

    ws.freeze_panes = "A4"
    _set_number_formats(ws)
    _autosize_columns(ws, min_width=14, max_width=34)


def _build_weekly_comparison_sheet(wb: Workbook, comparison) -> None:
    ws = wb.create_sheet("Weekly Comparison")

    row = _write_title(
        ws,
        title="Weekly Comparison",
        subtitle=(
            f"{comparison.week_a.week_label} vs {comparison.week_b.week_label}"
            if comparison is not None
            else "No specific comparison selected"
        ),
        width_to_col=5,
    )

    headers = ["metric", "week_a", "week_b", "delta", "note"]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_ALL

    row += 1

    if comparison is None:
        ws.cell(row=row, column=1, value="No weeks selected for comparison.").alignment = ALIGN_LEFT
        ws.cell(row=row, column=1).border = BORDER_ALL
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    else:
        compare_rows = [
            ("total_km", comparison.week_a.total_km, comparison.week_b.total_km, comparison.delta.total_km),
            ("worked_dogs", comparison.week_a.worked_dogs, comparison.week_b.worked_dogs, comparison.delta.worked_dogs),
            (
                "avg_km_per_worked_dog",
                comparison.week_a.avg_km_per_worked_dog,
                comparison.week_b.avg_km_per_worked_dog,
                comparison.delta.avg_km_per_worked_dog,
            ),
            ("high_risk_dogs", comparison.week_a.high_risk_dogs, comparison.week_b.high_risk_dogs, comparison.delta.high_risk_dogs),
            (
                "moderate_risk_dogs",
                comparison.week_a.moderate_risk_dogs,
                comparison.week_b.moderate_risk_dogs,
                comparison.delta.moderate_risk_dogs,
            ),
            ("underused_dogs", comparison.week_a.underused_dogs, comparison.week_b.underused_dogs, comparison.delta.underused_dogs),
        ]

        for metric, week_a, week_b, delta in compare_rows:
            values = [metric, week_a, week_b, delta, _comparison_hint(metric, delta)]
            for col, value in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = BORDER_ALL
                cell.alignment = ALIGN_CENTER if col > 1 else ALIGN_LEFT

                if col == 4:
                    if metric in {"high_risk_dogs", "moderate_risk_dogs", "underused_dogs"}:
                        cell.fill = FILL_GOOD if delta < 0 else FILL_WARN if delta > 0 else PatternFill(fill_type=None)
                    else:
                        cell.fill = FILL_GOOD if delta > 0 else FILL_WARN if delta < 0 else PatternFill(fill_type=None)
            row += 1

    ws.freeze_panes = "A4"
    _set_number_formats(ws)
    _autosize_columns(ws, min_width=14, max_width=30)


def _build_dog_weekly_summary_sheet(
    wb: Workbook,
    db: Session,
    weekly,
    date_from: date,
    date_to: date,
) -> None:
    ws = wb.create_sheet("Dog Weekly Summary")

    row = _write_title(
        ws,
        title="Dog Weekly Summary",
        subtitle="Weekly dog-level totals. KM = kilometers, KERRAT = safari count, TP = worked days.",
        width_to_col=8 + len(weekly.items) * 3,
    )

    dogs = _fetch_operational_dogs(db)
    worklogs = _fetch_worklogs_in_range(db, date_from, date_to)

    week_order = [item.week_start for item in weekly.items]
    week_labels = {item.week_start: item.week_label for item in weekly.items}

    by_dog_week: dict[int, dict[date, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"km": 0.0, "kerrat": 0.0, "tp": 0.0})
    )

    for log in worklogs:
        week_start = _start_of_week(log.work_date)
        if week_start not in week_labels:
            continue

        bucket = by_dog_week[log.dog_id][week_start]
        bucket["km"] += _to_float(log.km)
        bucket["kerrat"] += int(log.programs_3km or 0) + int(log.programs_10km or 0)
        if log.worked:
            bucket["tp"] += 1

    base_headers = [
        "dog_name",
        "kennel_row",
        "kennel_block",
        "home_slot",
        "primary_role",
        "total_km",
        "total_kerrat",
        "total_tp",
    ]

    col = 1
    for header in base_headers:
        ws.merge_cells(start_row=row, start_column=col, end_row=row + 1, end_column=col)
        cell = ws.cell(row=row, column=col, value=header)
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_ALL
        ws.cell(row=row + 1, column=col).border = BORDER_ALL
        col += 1

    for week_start in week_order:
        week_label = week_labels[week_start]
        start_col = col
        end_col = col + 2
        ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)

        top = ws.cell(row=row, column=start_col, value=week_label)
        top.fill = FILL_INFO
        top.font = FONT_HEADER
        top.alignment = ALIGN_CENTER
        top.border = BORDER_ALL

        sub_headers = ["KM", "KERRAT", "TP"]
        for offset, sub in enumerate(sub_headers):
            c = ws.cell(row=row + 1, column=start_col + offset, value=sub)
            c.fill = FILL_SUBHEADER
            c.font = FONT_HEADER
            c.alignment = ALIGN_CENTER
            c.border = BORDER_ALL

        col += 3

    row += 2

    for dog in dogs:
        total_km = 0.0
        total_kerrat = 0.0
        total_tp = 0.0

        for week_start in week_order:
            stats = by_dog_week[dog.id][week_start]
            total_km += stats["km"]
            total_kerrat += stats["kerrat"]
            total_tp += stats["tp"]

        fixed_values = [
            dog.name,
            dog.kennel_row,
            dog.kennel_block,
            dog.home_slot,
            dog.primary_role,
            round(total_km, 2),
            int(total_kerrat),
            int(total_tp),
        ]

        col = 1
        for value in fixed_values:
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = BORDER_ALL
            cell.alignment = ALIGN_LEFT if col <= 5 else ALIGN_CENTER
            col += 1

        for week_start in week_order:
            stats = by_dog_week[dog.id][week_start]
            week_values = [
                round(stats["km"], 2),
                int(stats["kerrat"]),
                int(stats["tp"]),
            ]
            for value in week_values:
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = BORDER_ALL
                cell.alignment = ALIGN_CENTER
                col += 1

        row += 1

    ws.freeze_panes = "A4"
    _set_number_formats(ws)
    _autosize_columns(ws, min_width=10, max_width=26)


def build_raw_run_logs_csv(
    db: Session,
    date_from: date,
    date_to: date,
):
    dogs = {dog.id: dog for dog in _fetch_operational_dogs(db)}
    worklogs = _fetch_worklogs_in_range(db, date_from, date_to)

    buffer = StringIO()
    writer = csv.writer(buffer)

    writer.writerow([
        "work_date",
        "week_label",
        "dog_name",
        "kennel_row",
        "kennel_block",
        "home_slot",
        "primary_role",
        "worked",
        "km",
        "programs_3km",
        "programs_10km",
        "kerrat_total",
        "status",
        "notes",
    ])

    for log in worklogs:
        dog = dogs.get(log.dog_id)
        writer.writerow([
            log.work_date.isoformat(),
            log.week_label,
            dog.name if dog else f"dog_id={log.dog_id}",
            log.kennel_row or (dog.kennel_row if dog else None),
            dog.kennel_block if dog else None,
            log.home_slot or (dog.home_slot if dog else None),
            log.main_role or (dog.primary_role if dog else None),
            "yes" if log.worked else "no",
            round(_to_float(log.km), 2),
            int(log.programs_3km or 0),
            int(log.programs_10km or 0),
            int(log.programs_3km or 0) + int(log.programs_10km or 0),
            log.status,
            log.notes,
        ])

    content = BytesIO(buffer.getvalue().encode("utf-8-sig"))
    content.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"husky-run-logs-{date_from.isoformat()}-to-{date_to.isoformat()}-{timestamp}.csv"
    return content, filename


def build_analytics_workbook(
    db: Session,
    date_from: date,
    date_to: date,
    week_a_start: date | None = None,
    week_b_start: date | None = None,
):
    weekly = get_weekly_analytics(db=db, date_from=date_from, date_to=date_to)
    summary = get_analytics_summary(db=db, date_from=date_from, date_to=date_to)

    comparison = None
    if week_a_start is not None and week_b_start is not None:
        comparison = get_weekly_compare(
            db=db,
            week_a_start=week_a_start,
            week_b_start=week_b_start,
        )

    wb = Workbook()

    _build_overview_sheet(
        wb=wb,
        date_from=date_from,
        date_to=date_to,
        weekly=weekly,
        summary=summary,
        comparison=comparison,
    )
    _build_weekly_comparison_sheet(wb=wb, comparison=comparison)
    _build_dog_weekly_summary_sheet(
        wb=wb,
        db=db,
        weekly=weekly,
        date_from=weekly.date_from,
        date_to=weekly.date_to,
    )

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream