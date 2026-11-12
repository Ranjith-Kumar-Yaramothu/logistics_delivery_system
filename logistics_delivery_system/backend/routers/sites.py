from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import CustomerSite

router = APIRouter(prefix="/sites", tags=["Customer sites"])

@router.get("/")
def list_sites(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(CustomerSite).limit(min(limit, 1000)).all()
