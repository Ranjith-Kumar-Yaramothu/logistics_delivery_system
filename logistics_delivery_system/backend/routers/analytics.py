
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Delivery, Route

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):

    total = (
        db.query(func.count(Delivery.delivery_id)).scalar() or 0
    )

    status_counts = dict(
        db.query(
            Delivery.status,
            func.count(Delivery.delivery_id)
        )
        .group_by(Delivery.status)
        .all()
    )

    pending = status_counts.get("PENDING", 0)
    assigned = status_counts.get("ASSIGNED", 0)
    delivered = status_counts.get("DELIVERED", 0)

    total_routes = (
        db.query(func.count(Route.route_id)).scalar() or 0
    )

    completed_routes = (
        db.query(func.count(Route.route_id))
        .filter(Route.status == "COMPLETED")
        .scalar() or 0
    )

    planned_distance = (
        db.query(func.sum(Route.planned_distance_km)).scalar() or 0
    )

    planned_deliveries = assigned + delivered

    return {
        "total_deliveries": total,
        "pending_deliveries": pending,
        "assigned_deliveries": assigned,
        "delivered_deliveries": delivered,
        "delivered_outcomes": delivered,
        "routes": total_routes,
        "completed_routes": completed_routes,
        "planned_distance_km": round(float(planned_distance), 2),
        "assignment_rate_pct": round(
            planned_deliveries / total * 100, 2
        ) if total else 0,
        "delivery_status": {
            "PENDING": pending,
            "ASSIGNED": assigned,
            "DELIVERED": delivered
        }
    }
