
import csv
import io

import pandas as pd

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import (
    Delivery,
    Route,
    RouteStop,
    DeliveryOutcome
)
from backend.services.anomaly_detector import (
    detect_route_anomalies
)


router = APIRouter(
    prefix="/exports",
    tags=["Data Exports"]
)


def model_to_dict(record):

    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }


def create_csv_response(rows, columns, filename):

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(rows)

    content = io.BytesIO(
        output.getvalue().encode("utf-8-sig")
    )

    return StreamingResponse(
        content,
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )


@router.get("/deliveries.csv")
def export_deliveries(db: Session = Depends(get_db)):

    records = db.query(Delivery).order_by(
        Delivery.delivery_id
    ).all()

    columns = list(Delivery.__table__.columns.keys())

    rows = [
        model_to_dict(record)
        for record in records
    ]

    return create_csv_response(
        rows,
        columns,
        "deliveries.csv"
    )


@router.get("/routes.csv")
def export_routes(db: Session = Depends(get_db)):

    records = db.query(Route).order_by(
        Route.route_date,
        Route.route_id
    ).all()

    columns = list(Route.__table__.columns.keys())

    rows = [
        model_to_dict(record)
        for record in records
    ]

    return create_csv_response(
        rows,
        columns,
        "routes.csv"
    )


@router.get("/route-stops.csv")
def export_route_stops(db: Session = Depends(get_db)):

    records = db.query(RouteStop).order_by(
        RouteStop.route_id,
        RouteStop.sequence_no
    ).all()

    columns = list(RouteStop.__table__.columns.keys())

    rows = [
        model_to_dict(record)
        for record in records
    ]

    return create_csv_response(
        rows,
        columns,
        "route_stops.csv"
    )


@router.get("/anomalies.csv")
def export_anomalies(db: Session = Depends(get_db)):

    routes = db.query(Route).order_by(
        Route.route_date,
        Route.route_id
    ).all()

    rows = []

    for route in routes:

        anomalies = detect_route_anomalies(
            db,
            route.route_id
        )

        for anomaly in anomalies:

            rows.append({
                "route_id": route.route_id,
                "route_date": route.route_date,
                "issue_type": anomaly.get("issue_type"),
                "severity": anomaly.get("severity"),
                "delivery_id": anomaly.get("delivery_id"),
                "other_route_id": anomaly.get("other_route_id")
            })

    columns = [
        "route_id",
        "route_date",
        "issue_type",
        "severity",
        "delivery_id",
        "other_route_id"
    ]

    return create_csv_response(
        rows,
        columns,
        "anomaly_report.csv"
    )


@router.get("/analytics.xlsx")
def export_analytics(db: Session = Depends(get_db)):

    total = (
        db.query(func.count(Delivery.delivery_id))
        .scalar() or 0
    )

    status_counts = dict(
        db.query(
            Delivery.status,
            func.count(Delivery.delivery_id)
        )
        .group_by(Delivery.status)
        .all()
    )

    total_routes = (
        db.query(func.count(Route.route_id))
        .scalar() or 0
    )

    completed_routes = (
        db.query(func.count(Route.route_id))
        .filter(Route.status == "COMPLETED")
        .scalar() or 0
    )

    distance = (
        db.query(func.sum(Route.planned_distance_km))
        .scalar() or 0
    )

    delivered = status_counts.get("DELIVERED", 0)
    assigned = status_counts.get("ASSIGNED", 0)

    summary = [{
        "Total Deliveries": total,
        "Pending Deliveries": status_counts.get("PENDING", 0),
        "Assigned Deliveries": assigned,
        "Delivered Deliveries": delivered,
        "Total Routes": total_routes,
        "Completed Routes": completed_routes,
        "Planned Distance (KM)": round(float(distance), 2),
        "Assignment Rate (%)": round(
            (assigned + delivered) / total * 100, 2
        ) if total else 0
    }]

    deliveries = db.query(Delivery).all()
    routes = db.query(Route).all()
    stops = db.query(RouteStop).all()
    outcomes = db.query(DeliveryOutcome).all()

    delivery_rows = [
        model_to_dict(record)
        for record in deliveries
    ]

    route_rows = [
        model_to_dict(record)
        for record in routes
    ]

    stop_rows = [
        model_to_dict(record)
        for record in stops
    ]

    outcome_rows = [
        model_to_dict(record)
        for record in outcomes
    ]

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        pd.DataFrame(summary).to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        pd.DataFrame(
            list(status_counts.items()),
            columns=["Delivery Status", "Count"]
        ).to_excel(
            writer,
            sheet_name="Delivery Status",
            index=False
        )

        pd.DataFrame(delivery_rows).to_excel(
            writer,
            sheet_name="Deliveries",
            index=False
        )

        pd.DataFrame(route_rows).to_excel(
            writer,
            sheet_name="Routes",
            index=False
        )

        pd.DataFrame(stop_rows).to_excel(
            writer,
            sheet_name="Route Stops",
            index=False
        )

        pd.DataFrame(outcome_rows).to_excel(
            writer,
            sheet_name="Delivery Outcomes",
            index=False
        )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                'attachment; filename="logistics_analytics.xlsx"'
        }
    )
