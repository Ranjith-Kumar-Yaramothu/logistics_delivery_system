from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import PlanRequest
from backend.models import Route
from backend.services.route_optimizer import build_greedy_plan
from backend.services.simulation import simulate_route
from backend.services.anomaly_detector import detect_route_anomalies

router = APIRouter(prefix="/routes", tags=["Route planning"])

@router.post("/plan")
def plan_routes(request: PlanRequest, db: Session = Depends(get_db)):
    return build_greedy_plan(db, request.plan_date, request.max_deliveries)

@router.get("/")
def list_routes(plan_date: date | None = None, db: Session = Depends(get_db)):
    q = db.query(Route)
    if plan_date:
        q = q.filter(Route.route_date == plan_date)
    return q.all()

@router.post("/{route_id}/simulate")
def simulate(route_id: str, db: Session = Depends(get_db)):
    if not db.query(Route).filter_by(route_id=route_id).first():
        raise HTTPException(status_code=404, detail="Route not found")
    return simulate_route(db, route_id)

@router.get("/{route_id}/anomalies")
def anomalies(route_id: str, db: Session = Depends(get_db)):
    return detect_route_anomalies(db, route_id)
