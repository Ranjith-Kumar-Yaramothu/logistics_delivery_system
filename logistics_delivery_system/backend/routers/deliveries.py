from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Delivery

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

@router.get("/")
def list_deliveries(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(Delivery)
    if status:
        q = q.filter(Delivery.status == status.upper())
    return q.limit(min(limit, 2000)).all()

@router.get("/summary")
def delivery_summary(db: Session = Depends(get_db)):
    rows = db.query(Delivery.status).all()
    result = {}
    for (status,) in rows:
        result[status] = result.get(status, 0) + 1
    return result
