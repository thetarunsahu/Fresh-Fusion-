import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FruitImage, FruitSample, FusionResult, SensorReading
from ..schemas import SampleCreate, SampleOut
from ..services.fusion import compute_fusion

router = APIRouter(prefix="/samples", tags=["samples"])

@router.post("", response_model=SampleOut)
def create_sample(payload: SampleCreate, db: Session = Depends(get_db)):
    prefix = payload.fruit_type[:3].upper() or "FRT"
    sample = FruitSample(sample_id=f"{prefix}-{secrets.token_hex(3).upper()}", fruit_type=payload.fruit_type, variety=payload.variety, source=payload.source)
    db.add(sample)
    db.commit(); db.refresh(sample)
    return sample

@router.get("")
def list_samples(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(FruitSample).order_by(FruitSample.created_at.desc()).limit(min(limit, 200)).all()
    return [{"sample_id": x.sample_id, "fruit_type": x.fruit_type, "status": x.status, "created_at": x.created_at} for x in rows]

@router.get("/{sample_id}/bundle")
def bundle(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    sensors = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).limit(500).all()
    sensors.reverse()
    images = db.query(FruitImage).filter(FruitImage.sample_id == sample_id).order_by(FruitImage.uploaded_at.desc()).all()
    result = db.query(FusionResult).filter(FusionResult.sample_id == sample_id).order_by(FusionResult.created_at.desc()).first()
    return {
        "sample": {"sample_id": sample.sample_id, "fruit_type": sample.fruit_type, "variety": sample.variety, "status": sample.status, "created_at": sample.created_at},
        "sensors": [{"id": s.id, "device_id": s.device_id, "temperature": s.temperature, "humidity": s.humidity, "mq135_raw": s.mq135_raw, "gas_ppm": s.gas_ppm, "voc_index": s.voc_index, "rssi": s.rssi, "captured_at": s.captured_at} for s in sensors],
        "images": [{"id": i.id, "angle": i.angle, "ground_truth": i.ground_truth, "url": i.url, "analysis": i.analysis, "uploaded_at": i.uploaded_at} for i in images],
        "fusion": None if not result else {"freshness_score": result.freshness_score, "sensor_score": result.sensor_score, "vision_score": result.vision_score, "label": result.label, "confidence": result.confidence, "risk": result.risk, "components": result.components, "created_at": result.created_at},
    }

@router.post("/{sample_id}/fusion")
def fuse(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    return compute_fusion(db, sample)
