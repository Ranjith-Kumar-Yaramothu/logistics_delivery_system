
from fastapi import FastAPI
from sqlalchemy import text

from backend.database import engine, Base

from backend.routers import (
    sites,
    deliveries,
    vehicles,
    routes,
    analytics,
    exports
)


app = FastAPI(
    title="Intelligent Logistics & Delivery Route Optimization",
    description="Synthetic delivery planning, routing, simulation and analytics",
    version="1.0.0"
)


app.include_router(sites.router)
app.include_router(deliveries.router)
app.include_router(vehicles.router)
app.include_router(routes.router)
app.include_router(analytics.router)
app.include_router(exports.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Logistics Delivery Optimization API",
        "status": "running"
    }


@app.get("/database-check")
def database_check():

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "MySQL",
        "status": "connected"
    }
