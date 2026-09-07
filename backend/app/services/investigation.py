"""Evidence-grounded FreshFusion investigation summary.

This service adapts the ReliAI investigation philosophy to fruit-quality analysis:
existing CV, sensor, reference, physical-validation and fusion outputs are exposed as
specialized analysts, followed by a deterministic evidence critic. The critic can
block a verdict when evidence is missing or contradictory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import FruitImage, FruitSample, FusionResult, SensorReading
from .physical_validation import evaluate_physical_evidence


VALID_VIEWS = {"front", "back", "left", "right", "top"}


def _view_name(angle: str | None) -> str:
    value = (angle or "unknown").lower()
    return value[5:] if value.startswith("live-") else value


def _age_seconds(value: datetime | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, (datetime.utcnow() - value).total_seconds())
    except Exception:
        return None


def _source_kind(reading: SensorReading | None) -> str:
    if reading is None:
        return "missing"
    text = f"{reading.device_id or ''} {(reading.extra_metrics or {}).get('source', '')}".lower()
    if any(token in text for token in ("sim", "mock", "test", "demo")):
        return "simulator"
    return "physical-device"


def _valid_sensor(reading: SensorReading | None) -> bool:
    if reading is None:
        return False
    return any(
        value is not None
        for value in (
            reading.temperature,
            reading.humidity,
            reading.mq135_raw,
            reading.gas_ppm,
            reading.voc_index,
        )
    )


def _accepted_images(images: list[FruitImage]) -> list[FruitImage]:
    accepted = []
    for row in images:
        analysis = row.analysis or {}
        if analysis.get("quality", {}).get("fruit_present") is True:
            accepted.append(row)
    return accepted


def build_investigation_summary(db: Session, sample: FruitSample) -> dict[str, Any]:
    images = (
        db.query(FruitImage)
        .filter(FruitImage.sample_id == sample.sample_id)
        .order_by(FruitImage.uploaded_at.desc())
        .limit(40)
        .all()
    )
    sensors = (
        db.query(SensorReading)
        .filter(SensorReading.sample_id == sample.sample_id)
        .order_by(SensorReading.captured_at.desc())
        .limit(30)
        .all()
    )
    latest_fusion = (
        db.query(FusionResult)
        .filter(FusionResult.sample_id == sample.sample_id)
        .order_by(FusionResult.created_at.desc())
        .first()
    )

    accepted = _accepted_images(images)
    latest_image = accepted[0] if accepted else (images[0] if images else None)
    latest_analysis = (latest_image.analysis or {}) if latest_image else {}
    identity = latest_analysis.get("identity", {})
    color = latest_analysis.get("color", {})
    defects = latest_analysis.get("defects", {})
    reference = latest_analysis.get("reference_match", {})

    views = sorted({_view_name(row.angle) for row in accepted if _view_name(row.angle) in VALID_VIEWS})
    validation = evaluate_physical_evidence(db, sample, images=images, sensors=sensors)

    latest_sensor = sensors[0] if sensors else None
    sensor_age = _age_seconds(latest_sensor.captured_at) if latest_sensor else None
    sensor_valid = _valid_sensor(latest_sensor)
    sensor_source = _source_kind(latest_sensor)

    vision_analyst = {
        "status": "ready" if accepted else "waiting-for-fruit",
        "detected_fruit": identity.get("fruit"),
        "identity_confidence_pct": identity.get("confidence"),
        "usable_images": len(accepted),
        "views": views,
        "healthy_surface_estimate_pct": defects.get("healthy_surface_estimate_pct"),
        "brown_surface_pct": color.get("brown_pct"),
        "dark_surface_pct": color.get("dark_pct"),
        "note": "OpenCV/ML-ready visual evidence; prototype measurements are not a food-safety verdict.",
    }

    sensor_analyst = {
        "status": "ready" if sensor_valid else "waiting-for-sensor",
        "source": sensor_source,
        "device_id": latest_sensor.device_id if latest_sensor else None,
        "temperature_c": latest_sensor.temperature if latest_sensor else None,
        "humidity_pct": latest_sensor.humidity if latest_sensor else None,
        "mq135_raw": latest_sensor.mq135_raw if latest_sensor else None,
        "gas_ppm": latest_sensor.gas_ppm if latest_sensor else None,
        "voc_index": latest_sensor.voc_index if latest_sensor else None,
        "age_seconds": round(sensor_age, 1) if sensor_age is not None else None,
        "note": "MQ135 raw ADC is relative prototype evidence unless separately calibrated; it is not ppm.",
    }

    reference_analyst = {
        "status": reference.get("status", "not-available"),
        "dataset": reference.get("dataset") or reference.get("source"),
        "matched_class": reference.get("class") or reference.get("label") or reference.get("matched_class"),
        "similarity_pct": reference.get("similarity"),
        "reference_count": reference.get("reference_count") or reference.get("samples"),
        "note": "Reference similarity is a handcrafted comparison signal, not model probability or validated accuracy.",
    }

    multiview_analyst = {
        "status": validation.get("status"),
        "physical_likely": validation.get("physical_likely", False),
        "vision_verified": validation.get("vision_verified", False),
        "views": validation.get("views", views),
        "views_count": validation.get("views_count", len(views)),
        "required_views": validation.get("required_views", 3),
        "screen_suspicion_pct": validation.get("screen_suspicion_pct"),
        "appearance_diversity_pct": validation.get("appearance_diversity_pct"),
        "identity_consistency_pct": validation.get("identity_consistency_pct"),
        "message": validation.get("message"),
        "note": validation.get("note"),
    }

    missing: list[str] = []
    warnings: list[str] = []
    contradictions: list[str] = []

    if not accepted:
        missing.append("No quality-gated fruit image is available.")
    if len(views) < int(validation.get("required_views", 3) or 3):
        missing.append("More distinct physical viewpoints are required.")
    if not sensor_valid:
        missing.append("A valid sensor reading is required.")
    elif sensor_age is None or sensor_age > float(validation.get("sensor_freshness_window_seconds", 45) or 45):
        missing.append("Recent ESP32 telemetry is required.")
    if sensor_source == "simulator":
        warnings.append("Latest sensor evidence is simulator/test data, not physical ESP32 evidence.")
    if validation.get("status") == "suspected_2d_display":
        contradictions.append("Camera evidence is consistent with a screen/display presentation.")
    if validation.get("status") == "suspected_flat_reference":
        contradictions.append("Multi-view evidence remains consistent with a flat photo/reference.")

    detected = str(identity.get("fruit") or "").strip().lower()
    expected = str(sample.fruit_type or "").strip().lower()
    identity_conf = float(identity.get("confidence") or 0.0)
    if detected and detected != "unknown" and expected in {"apple", "banana"} and detected != expected and identity_conf >= 58.0:
        contradictions.append(
            f"Visual identity ({detected}) conflicts with the active sample ({expected})."
        )
    if identity_conf and identity_conf < 58.0:
        warnings.append("Fruit identity confidence is below the current prototype acceptance threshold.")

    verdict_ready = bool(validation.get("verdict_ready")) and sensor_valid and sensor_source != "simulator"
    if contradictions:
        critic_status = "blocked"
        decision_reason = "Conflicting evidence detected."
        verdict_ready = False
    elif missing:
        critic_status = "needs-more-data"
        decision_reason = "More evidence is required before a final freshness assessment."
        verdict_ready = False
    elif warnings:
        critic_status = "warning"
        decision_reason = "Evidence is usable but contains warnings that require review."
    else:
        critic_status = "passed"
        decision_reason = "Required prototype evidence checks passed."

    public_score = None
    public_label = None
    public_confidence = None
    if latest_fusion and verdict_ready:
        public_score = latest_fusion.freshness_score
        public_label = latest_fusion.label
        public_confidence = latest_fusion.confidence

    return {
        "inspection_id": sample.sample_id,
        "sample": {
            "sample_id": sample.sample_id,
            "fruit_type": sample.fruit_type,
            "variety": sample.variety,
            "status": sample.status,
            "created_at": sample.created_at,
            "updated_at": sample.updated_at,
        },
        "status": "conclusive" if verdict_ready else "investigating",
        "evidence": {
            "camera_frames": len(images),
            "accepted_fruit_frames": len(accepted),
            "sensor_readings": len(sensors),
            "latest_frame_at": latest_image.uploaded_at if latest_image else None,
            "latest_sensor_at": latest_sensor.captured_at if latest_sensor else None,
        },
        "analysts": {
            "vision": vision_analyst,
            "sensor": sensor_analyst,
            "reference": reference_analyst,
            "multiview": multiview_analyst,
        },
        "critic": {
            "status": critic_status,
            "supporting_evidence": [
                item
                for item in (
                    f"{len(accepted)} usable fruit frame(s) available." if accepted else None,
                    f"{len(views)} distinct physical view(s) captured." if views else None,
                    "Recent physical sensor evidence available." if sensor_valid and sensor_source == "physical-device" and sensor_age is not None and sensor_age <= 45 else None,
                    "Physical multi-view evidence likely." if validation.get("physical_likely") else None,
                )
                if item
            ],
            "missing_evidence": missing,
            "contradictions": contradictions,
            "warnings": warnings,
        },
        "decision": {
            "verdict_ready": verdict_ready,
            "label": public_label,
            "freshness_score": public_score,
            "confidence_pct": public_confidence,
            "reason": decision_reason,
            "scientific_status": "experimental-prototype",
        },
        "llm": {
            "provider": "Ollama",
            "model_family": "Gemma",
            "role": "evidence explanation only",
            "required_for_verdict": False,
        },
    }
