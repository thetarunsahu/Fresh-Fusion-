import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import FruitImage, FruitSample, FusionResult, SensorReading, HumanVerification, InspectionProfile
from ..schemas import SampleCreate, SampleOut, VerificationIn, InspectionProfileIn
from ..services.fusion import compute_fusion, evaluate_fusion
from ..services.sensor_assessment import serialize_sensor, utc_iso
from ..services.inspection_control import active_sample, set_active
from ..services.investigation_core.investigation import investigate
from ..services.investigation_core.evidence import sample_info, verification_info
from ..services.inspection_events import recent_events, record_event

router = APIRouter(prefix="/samples", tags=["samples"])
SUPPORTED_IDENTITIES = {"Apple", "Banana", "Tomato"}


@router.post("", response_model=SampleOut)
def create_sample(payload: SampleCreate, db: Session = Depends(get_db)):
    prefix = payload.fruit_type[:3].upper() or "FRT"
    sample = FruitSample(sample_id=f"{prefix}-{secrets.token_hex(3).upper()}", fruit_type=payload.fruit_type, variety=payload.variety, source=payload.source)
    db.add(sample)
    db.flush()
    db.add(InspectionProfile(sample_id=sample.sample_id, fruit_count=1, protocol={"chamber_purged": None, "inspection_duration_seconds": None, "fruit_instance_id": None}))
    db.commit(); db.refresh(sample)
    set_active(db, sample)
    return sample


@router.get("")
def list_samples(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(FruitSample).order_by(FruitSample.created_at.desc()).limit(min(limit, 200)).all()
    image_counts = dict(db.query(FruitImage.sample_id, func.count(FruitImage.id)).group_by(FruitImage.sample_id).all())
    sensor_counts = dict(db.query(SensorReading.sample_id, func.count(SensorReading.id)).group_by(SensorReading.sample_id).all())
    output = []
    for row in rows:
        result = db.query(FusionResult).filter_by(sample_id=row.sample_id).order_by(FusionResult.created_at.desc()).first()
        gate = (result.components or {}).get("validation", {}) if result else {}
        output.append({**sample_info(row), "camera_frames": image_counts.get(row.sample_id, 0),
                       "sensor_readings": sensor_counts.get(row.sample_id, 0),
                       "last_recorded_verdict_ready": bool(gate.get("verdict_ready")),
                       "last_assessed_at": utc_iso(result.created_at) if result else None,
                       "verification_state": gate.get("status", "not-assessed")})
    return output


@router.get("/active")
def get_active(db: Session = Depends(get_db)):
    sample = active_sample(db)
    return sample_info(sample) if sample else None


@router.put("/{sample_id}/active")
def activate(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    set_active(db, sample)
    return sample_info(sample)


@router.get("/{sample_id}/profile")
def get_profile(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    row = db.query(InspectionProfile).filter_by(sample_id=sample_id).first()
    if not row:
        row = InspectionProfile(sample_id=sample_id, fruit_count=1, protocol={})
        db.add(row); db.commit(); db.refresh(row)
    protocol = dict(row.protocol or {})
    return {"sample_id": sample_id, "approximate_weight_g": row.approximate_weight_g, "fruit_count": row.fruit_count,
            "fruit_instance_id": protocol.get("fruit_instance_id"),
            "batch_id": row.batch_id, "supplier": row.supplier, "storage_location": row.storage_location,
            "protocol": protocol, "updated_at": utc_iso(row.updated_at)}


@router.put("/{sample_id}/profile")
def update_profile(sample_id: str, payload: InspectionProfileIn, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    row = db.query(InspectionProfile).filter_by(sample_id=sample_id).first()
    if not row:
        row = InspectionProfile(sample_id=sample_id, fruit_count=1, protocol={})
        db.add(row)
    data = payload.model_dump()
    row.approximate_weight_g = data["approximate_weight_g"]
    row.fruit_count = data["fruit_count"]
    row.batch_id = data["batch_id"]
    row.supplier = data["supplier"]
    row.storage_location = data["storage_location"]
    protocol = dict(row.protocol or {})
    protocol["fruit_instance_id"] = data["fruit_instance_id"]
    protocol["inspection_duration_seconds"] = data["inspection_duration_seconds"]
    protocol["chamber_purged"] = data["chamber_purged"]
    row.protocol = protocol
    db.commit(); db.refresh(row)
    return get_profile(sample_id, db)


@router.get("/{sample_id}/events")
def events(sample_id: str, limit: int = 50, db: Session = Depends(get_db)):
    if not db.query(FruitSample).filter_by(sample_id=sample_id).first():
        raise HTTPException(404, "Sample not found")
    return recent_events(db, sample_id, min(limit, 200))


@router.post("/{sample_id}/verification", status_code=201)
def verify(sample_id: str, payload: VerificationIn, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter_by(sample_id=sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    summary = investigate(db, sample)
    if payload.action == "accept" and not summary["decision"]["verdict_ready"]:
        raise HTTPException(409, "Cannot accept a locked assessment; collect evidence or add human ground truth separately")
    snapshot = {**summary["decision"], "evidence_image_id": summary["evidence"]["camera"]["latest_image_id"],
                "evidence_sensor_id": (summary["evidence"]["sensors"]["latest"] or {}).get("id")}
    row = HumanVerification(sample_id=sample_id, **payload.model_dump(), assessment=snapshot)
    db.add(row)
    event_type = "human_override" if payload.action == "override" else "human_verification"
    event_message = (
        f"Human override recorded as {payload.ground_truth}."
        if payload.action == "override"
        else f"Human verification recorded: {payload.action}."
    )
    record_event(
        db,
        sample_id,
        event_type,
        event_message,
        severity="warning" if payload.action == "override" else "info",
        payload={
            "action": payload.action,
            "ground_truth": payload.ground_truth,
            "reviewer": payload.reviewer,
            "notes": payload.notes,
            "system_label": snapshot.get("label"),
            "system_score": snapshot.get("freshness_score"),
        },
    )
    db.commit()
    db.refresh(row)
    return verification_info(row)


def _bundle_analysis(image: FruitImage, sample: FruitSample) -> dict:
    """Return a UI-stable analysis without mutating stored raw evidence.

    Older frames may predate temporal stabilization. For presentation, the
    inspection's accepted fruit identity is authoritative; raw frame identity is
    retained alongside it for engineering diagnostics.
    """
    analysis = dict(image.analysis or {})
    raw_identity = dict(analysis.get("raw_frame_identity") or analysis.get("identity") or {})
    stable = str(sample.fruit_type or "").strip().title()
    if stable in SUPPORTED_IDENTITIES:
        identity = dict(analysis.get("identity") or {})
        analysis["raw_frame_identity"] = raw_identity
        state = dict(analysis.get("identity_state") or {})
        state.setdefault("raw_frame_fruit", raw_identity.get("fruit"))
        state.setdefault("raw_frame_confidence", raw_identity.get("confidence"))
        state["stable_fruit"] = stable
        analysis["identity_state"] = state
        analysis["identity"] = {
            **identity,
            "fruit": stable,
            "raw_frame_fruit": raw_identity.get("fruit"),
            "raw_frame_confidence": raw_identity.get("confidence"),
            "stabilized": True,
            "method": "inspection-stabilized identity",
        }
        analysis["fruit_type"] = stable
    return analysis


def _serialize_image(image: FruitImage, sample: FruitSample) -> dict:
    return {
        "id": image.id,
        "angle": image.angle,
        "ground_truth": image.ground_truth,
        "url": image.url,
        "analysis": _bundle_analysis(image, sample),
        "uploaded_at": utc_iso(image.uploaded_at),
    }


@router.get("/{sample_id}/bundle")
def bundle(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    sensors = db.query(SensorReading).filter(SensorReading.sample_id == sample_id).order_by(SensorReading.captured_at.desc()).limit(500).all()
    sensors.reverse()
    images = db.query(FruitImage).filter(FruitImage.sample_id == sample_id).order_by(FruitImage.uploaded_at.desc()).all()
    result = db.query(FusionResult).filter(FusionResult.sample_id == sample_id).order_by(FusionResult.created_at.desc()).first()
    return {
        "sample": sample_info(sample),
        "sensors": [serialize_sensor(s) for s in sensors],
        "images": [_serialize_image(i, sample) for i in images],
        "fusion": {**evaluate_fusion(db, sample), "created_at": utc_iso(result.created_at) if result else None},
    }


@router.post("/{sample_id}/fusion")
def fuse(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample not found")
    return compute_fusion(db, sample)
