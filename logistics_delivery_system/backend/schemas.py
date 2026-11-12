from datetime import date
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    mode: str = Field(default="starter", pattern="^(starter|full)$")
    seed: int = 20261022

class PlanRequest(BaseModel):
    plan_date: date
    max_deliveries: int = Field(default=100, ge=1, le=2000)

class HealthResponse(BaseModel):
    status: str
    database: str
