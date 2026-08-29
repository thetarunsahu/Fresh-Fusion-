from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample, SensorReading
from ..schemas import SensorReadingCreate, SensorReadingOut

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(payload: SensorReadingCreate, db: Session = Depends(get_db)) -> SensorReading:
    sample = db.scalar(select(FruitSample).where(FruitSample.sample_code == payload.sample_code))
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    reading = SensorReading(
        sample_id=sample.id,
        device_id=payload.device_id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        gas_raw=payload.gas_raw,
        gas_ppm=payload.gas_ppm,
        voc_index=payload.voc_index,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/readings", response_model=list[SensorReadingOut])
def list_readings(
    sample_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[SensorReading]:
    stmt = select(SensorReading).order_by(SensorReading.captured_at.desc()).limit(limit)
    if sample_code:
        sample = db.scalar(select(FruitSample).where(FruitSample.sample_code == sample_code))
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        stmt = stmt.where(SensorReading.sample_id == sample.id)
    return list(db.scalars(stmt).all())


@router.get("/latest", response_model=SensorReadingOut | None)
def latest_reading(db: Session = Depends(get_db)) -> SensorReading | None:
    return db.scalar(select(SensorReading).order_by(SensorReading.captured_at.desc()).limit(1))
