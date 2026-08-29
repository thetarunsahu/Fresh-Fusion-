from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FruitSample, SensorReading
from ..schemas import SensorIn
from ..realtime import manager

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.post("/readings")
async def ingest(payload: SensorIn, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == payload.sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    values = payload.model_dump()
    known = {"sample_id", "device_id", "temperature", "humidity", "mq135_raw", "gas_ppm", "voc_index", "rssi", "uptime_ms", "extra_metrics"}
    extra = {k: v for k, v in values.items() if k not in known}
    clean = {k: v for k, v in values.items() if k in known}
    clean["extra_metrics"] = {**(clean.get("extra_metrics") or {}), **extra}
    reading = SensorReading(**clean)
    db.add(reading); db.commit(); db.refresh(reading)
    message = {"type": "sensor", "data": {"id": reading.id, "sample_id": reading.sample_id, "device_id": reading.device_id, "temperature": reading.temperature, "humidity": reading.humidity, "mq135_raw": reading.mq135_raw, "gas_ppm": reading.gas_ppm, "voc_index": reading.voc_index, "rssi": reading.rssi, "captured_at": reading.captured_at.isoformat()}}
    await manager.broadcast(payload.sample_id, message)
    return {"ok": True, **message["data"]}

@router.get("/{sample_id}/latest")
def latest(sample_id: str, db: Session = Depends(get_db)):
    row = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).first()
    if not row: return None
    return {"id": row.id, "device_id": row.device_id, "temperature": row.temperature, "humidity": row.humidity, "mq135_raw": row.mq135_raw, "gas_ppm": row.gas_ppm, "voc_index": row.voc_index, "rssi": row.rssi, "captured_at": row.captured_at}
