import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..auth import get_current_user, require_roles
from ..database import get_db
from ..models import FruitImage, FruitSample, FusionResult, SensorReading, HumanVerification, User
from ..schemas import SampleCreate, SampleOut, VerificationIn
from ..services.fusion import compute_fusion, evaluate_fusion
from ..services.sensor_assessment import serialize_sensor, utc_iso
from ..services.inspection_control import active_sample, set_active
from ..services.investigation_core.investigation import investigate
from ..services.investigation_core.evidence import sample_info, verification_info

router = APIRouter(prefix="/samples", tags=["samples"])

@router.post("", response_model=SampleOut)
def create_sample(
    payload: SampleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
):
    prefix = payload.fruit_type[:3].upper() or "FRT"
    sample = FruitSample(sample_id=f"{prefix}-{secrets.token_hex(3).upper()}", fruit_type=payload.fruit_type, variety=payload.variety, source=payload.source)
    db.add(sample)
    db.commit(); db.refresh(sample)
    set_active(db, sample)
    return sample

@router.get("")
def list_samples(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.query(FruitSample).order_by(FruitSample.created_at.desc()).limit(min(limit, 200)).all()
    image_counts = dict(db.query(FruitImage.sample_id, func.count(FruitImage.id)).group_by(FruitImage.sample_id).all())
    sensor_counts = dict(db.query(SensorReading.sample_id, func.count(SensorReading.id)).group_by(SensorReading.sample_id).all())
    review_counts = dict(db.query(HumanVerification.sample_id, func.count(HumanVerification.id)).group_by(HumanVerification.sample_id).all())
    latest_reviews = {}
    for review in (
        db.query(HumanVerification)
        .order_by(HumanVerification.created_at.desc(), HumanVerification.id.desc())
        .all()
    ):
        latest_reviews.setdefault(review.sample_id, review)

    output = []
    for row in rows:
        result = db.query(FusionResult).filter_by(sample_id=row.sample_id).order_by(FusionResult.created_at.desc()).first()
        gate = (result.components or {}).get("validation", {}) if result else {}
        latest_review = latest_reviews.get(row.sample_id)
        output.append({
            **sample_info(row),
            "camera_frames": image_counts.get(row.sample_id, 0),
            "sensor_readings": sensor_counts.get(row.sample_id, 0),
            "last_recorded_verdict_ready": bool(gate.get("verdict_ready")),
            "last_assessed_at": utc_iso(result.created_at) if result else None,
            "verification_state": gate.get("status", "not-assessed"),
            "human_review_count": review_counts.get(row.sample_id, 0),
            "latest_ground_truth": latest_review.ground_truth if latest_review else None,
            "last_review_action": latest_review.action if latest_review else None,
            "last_reviewed_at": utc_iso(latest_review.created_at) if latest_review else None,
        })
    return output

@router.get("/active")
def get_active(db: Session = Depends(get_db)):
    # Kept public for the phone/ESP32 capture path. Dashboard operations use JWT.
    sample = active_sample(db)
    return sample_info(sample) if sample else None

@router.put("/{sample_id}/active")
def activate(
    sample_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    set_active(db, sample)
    return sample_info(sample)

@router.post("/{sample_id}/verification", status_code=201)
def verify(
    sample_id: str,
    payload: VerificationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator", "reviewer")),
):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    summary = investigate(db, sample)
    if payload.action == "accept" and not summary["decision"]["verdict_ready"]:
        raise HTTPException(409, "Cannot accept a locked assessment; collect evidence or add human ground truth separately")
    snapshot = {**summary["decision"], "evidence_image_id": summary["evidence"]["camera"]["latest_image_id"],
                "evidence_sensor_id": (summary["evidence"]["sensors"]["latest"] or {}).get("id")}
    values = payload.model_dump()
    if not values.get("reviewer"):
        values["reviewer"] = f"{user.full_name} ({user.role})"
    row = HumanVerification(sample_id=sample_id, **values, assessment=snapshot)
    db.add(row)
    db.commit()
    db.refresh(row)
    return verification_info(row)

@router.get("/{sample_id}/bundle")
def bundle(
    sample_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    sensors = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).limit(500).all()
    sensors.reverse()
    images = db.query(FruitImage).filter(FruitImage.sample_id == sample_id).order_by(FruitImage.uploaded_at.desc()).all()
    result = db.query(FusionResult).filter(FusionResult.sample_id == sample_id).order_by(FusionResult.created_at.desc()).first()
    return {
        "sample": sample_info(sample),
        "sensors": [serialize_sensor(s) for s in sensors],
        "images": [{"id": i.id, "angle": i.angle, "ground_truth": i.ground_truth, "url": i.url, "analysis": i.analysis, "uploaded_at": utc_iso(i.uploaded_at)} for i in images],
        "fusion": {**evaluate_fusion(db, sample), "created_at": utc_iso(result.created_at) if result else None},
    }

@router.post("/{sample_id}/fusion")
def fuse(
    sample_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    return compute_fusion(db, sample)
