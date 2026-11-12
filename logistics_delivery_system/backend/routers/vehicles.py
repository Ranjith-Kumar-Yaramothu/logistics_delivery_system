from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Vehicle

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("/")
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()
