from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FruitSample, SensorReading
from ..schemas import SensorIn
from ..realtime import manager
from ..services.inspection_control import active_sample
from ..services.sensor_assessment import (
    SENSOR_MAX_AGE,
    age_seconds,
    sensor_source,
    serialize_sensor,
    valid_measurements,
)
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
    db.add(reading)
    db.commit()
    db.refresh(reading)
    await run_in_threadpool(compute_fusion, db, sample)
    message = {"type": "sensor", "data": serialize_sensor(reading)}
    await manager.broadcast(sample.sample_id, message)
    return {"ok": True, **message["data"]}


@router.post("/{sample_id}/baseline/from-latest")
async def capture_baseline_from_latest(sample_id: str, db: Session = Depends(get_db)):
    """Store the latest physical telemetry as an explicit empty-chamber baseline.

    The operator must only call this while the chamber is empty. The copied row is
    tagged as baseline evidence and is excluded from fruit-scoring eligibility.
    Repeated captures are allowed so baseline stability can be estimated.
    """
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    latest = (
        db.query(SensorReading)
        .filter(SensorReading.sample_id == sample_id)
        .order_by(SensorReading.captured_at.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(409, "No sensor reading is available to record as baseline")
    if sensor_source(latest) != "hardware":
        raise HTTPException(409, "Baseline requires a physical hardware reading, not simulator data")
    if not valid_measurements(latest):
        raise HTTPException(409, "Latest sensor reading is incomplete or outside the accepted electrical range")
    if age_seconds(latest.captured_at) > SENSOR_MAX_AGE:
        raise HTTPException(409, "Latest sensor reading is stale; wait for a fresh ESP32 packet")

    copied_extra = dict(latest.extra_metrics or {})
    copied_extra.update(
        {
            "measurement_phase": "baseline",
            "baseline_protocol": "empty_chamber_operator_confirmed",
            "baseline_source_reading_id": latest.id,
        }
    )
    baseline = SensorReading(
        sample_id=sample_id,
        device_id=latest.device_id,
        temperature=latest.temperature,
        humidity=latest.humidity,
        mq135_raw=latest.mq135_raw,
        gas_ppm=latest.gas_ppm,
        voc_index=latest.voc_index,
        rssi=latest.rssi,
        uptime_ms=latest.uptime_ms,
        extra_metrics=copied_extra,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    await run_in_threadpool(compute_fusion, db, sample)
    message = {"type": "sensor_baseline", "data": serialize_sensor(baseline)}
    await manager.broadcast(sample_id, message)
    return {
        "ok": True,
        "instruction": "Baseline stored. Keep the chamber empty and capture at least three stable baseline readings before inserting fruit.",
        **message["data"],
    }


@router.get("/{sample_id}/latest")
def latest(sample_id: str, db: Session = Depends(get_db)):
    row = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).first()
    if not row:
        return None
    return serialize_sensor(row)
