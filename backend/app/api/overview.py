from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample, SensorReading
from ..schemas import OverviewOut

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/overview", response_model=OverviewOut)
def overview(db: Session = Depends(get_db)) -> OverviewOut:
    total_samples = db.scalar(select(func.count()).select_from(FruitSample)) or 0
    total_readings = db.scalar(select(func.count()).select_from(SensorReading)) or 0
    latest_sample = db.scalar(select(FruitSample).order_by(FruitSample.created_at.desc()).limit(1))
    latest_reading = db.scalar(select(SensorReading).order_by(SensorReading.captured_at.desc()).limit(1))
    return OverviewOut(
        total_samples=total_samples,
        total_readings=total_readings,
        latest_sample=latest_sample,
        latest_reading=latest_reading,
    )
