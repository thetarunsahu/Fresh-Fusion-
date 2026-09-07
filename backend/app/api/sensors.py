from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FruitSample, SensorReading
from ..schemas import SensorIn
from ..realtime import manager
from ..services.inspection_control import active_sample
from ..services.sensor_assessment import serialize_sensor
from ..services.fusion import compute_fusion
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.post("/readings")
async def ingest(payload: SensorIn, db: Session = Depends(get_db)):
    if payload.sample_id:
        sample = db.query(FruitSample).filter(FruitSample.sample_id == payload.sample_id).first()
        if not sample:
            raise HTTPException(404, "Sample not found")
    else:
        sample = active_sample(db)
        if not sample:
            raise HTTPException(409, "Create a fruit sample before sending ESP32 telemetry")

    values = payload.model_dump()
    known = {"sample_id", "device_id", "temperature", "humidity", "mq135_raw", "gas_ppm", "voc_index", "rssi", "uptime_ms", "extra_metrics"}
    extra = {k: v for k, v in values.items() if k not in known}
    clean = {k: v for k, v in values.items() if k in known}
    clean["sample_id"] = sample.sample_id
    clean["extra_metrics"] = {**(clean.get("extra_metrics") or {}), **extra}
    reading = SensorReading(**clean)
    db.add(reading); db.commit(); db.refresh(reading)
    await run_in_threadpool(compute_fusion, db, sample)
    message = {"type": "sensor", "data": serialize_sensor(reading)}
    await manager.broadcast(sample.sample_id, message)
    return {"ok": True, **message["data"]}

@router.get("/{sample_id}/latest")
def latest(sample_id: str, db: Session = Depends(get_db)):
    row = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).first()
    if not row: return None
    return serialize_sensor(row)
