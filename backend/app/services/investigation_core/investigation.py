from datetime import datetime

from ..fusion import evaluate_fusion
from ...models import FruitImage, FusionResult, InspectionProfile
from ..inspection_events import recent_events
from ..image_quality_gate import evaluate_image_quality
from ..product_rules import recommendation, score_breakdown, SUPPORTED_FRUITS
from ..sensor_drift import assess_historical_drift
from ..provenance import decision_provenance
from .evidence import collect_evidence, sample_info
from .analysts import summarize_analysts
from .confidence import decision_from_fusion


def _profile_info(db, sample_id):
    row = db.query(InspectionProfile).filter_by(sample_id=sample_id).first()
    if not row:
        return {"fruit_count": 1, "approximate_weight_g": None, "fruit_instance_id": None,
                "batch_id": None, "supplier": None, "storage_location": None, "protocol": {}}
    protocol = row.protocol or {}
    return {"fruit_count": row.fruit_count, "approximate_weight_g": row.approximate_weight_g,
            "fruit_instance_id": protocol.get("fruit_instance_id"),
            "batch_id": row.batch_id, "supplier": row.supplier, "storage_location": row.storage_location,
            "protocol": protocol}


def _protocol_state(sample, profile):
    protocol = profile.get("protocol") or {}
    target = protocol.get("inspection_duration_seconds")
    purged = protocol.get("chamber_purged")
    elapsed = max(0.0, (datetime.utcnow() - sample.created_at).total_seconds()) if sample.created_at else 0.0
    issues = []
    warnings = []
    if purged is False:
        issues.append("Chamber purge/reset is marked incomplete.")
    elif purged is None:
        warnings.append("Chamber purge/reset has not been confirmed for this inspection.")
    if target is not None and elapsed < float(target):
        issues.append(f"Inspection stabilization time is not complete: {int(elapsed)}s of {int(target)}s.")
    if profile.get("fruit_count", 1) > 1 and profile.get("approximate_weight_g") is None:
        warnings.append("Multiple fruits are recorded without approximate weight; gas-response comparison may be harder to interpret.")
    if not profile.get("fruit_instance_id"):
        warnings.append("No physical fruit specimen ID is assigned; repeated-inspection validation leakage cannot be prevented reliably.")
    return {
        "ready": not issues,
        "elapsed_seconds": round(elapsed, 1),
        "target_seconds": target,
        "chamber_purged": purged,
        "issues": issues,
        "warnings": warnings,
    }


def _condition_comparison(db, sample_id, current_fusion):
    rows = db.query(FusionResult).filter_by(sample_id=sample_id).order_by(FusionResult.created_at.desc(), FusionResult.id.desc()).limit(2).all()
    previous = rows[1] if len(rows) > 1 else None
    current_ready = (current_fusion.get("components") or {}).get("validation", {}).get("verdict_ready") is True
    previous_ready = bool(previous and (previous.components or {}).get("validation", {}).get("verdict_ready"))
    return {
        "available": bool(previous and current_ready and previous_ready),
        "previous_label": previous.label if previous_ready else None,
        "current_label": current_fusion.get("label") if current_ready else None,
        "previous_score": previous.freshness_score if previous_ready else None,
        "current_score": current_fusion.get("freshness_score") if current_ready else None,
        "score_change": round(float(current_fusion.get("freshness_score")) - float(previous.freshness_score), 2) if previous and current_ready and previous_ready else None,
        "previous_at": previous.created_at.isoformat() if previous and previous.created_at else None,
    }


def investigate(db, sample):
    fusion = evaluate_fusion(db, sample)
    evidence, timeline, verifications = collect_evidence(db, sample, fusion)
    decision = decision_from_fusion(fusion)
    images = db.query(FruitImage).filter_by(sample_id=sample.sample_id).order_by(FruitImage.uploaded_at.desc()).limit(30).all()
    image_quality = evaluate_image_quality(images)
    profile = _profile_info(db, sample.sample_id)
    protocol_state = _protocol_state(sample, profile)
    sensor_evidence = (fusion.get("components") or {}).get("sensor_evidence", evidence.get("sensors", {}))
    sensor_drift = assess_historical_drift(db, sample.sample_id, sensor_evidence)

    analysts = summarize_analysts(evidence, fusion)
    vision = analysts.get("vision", {})
    detected_fruit = (vision.get("identity") or {}).get("fruit")
    sample_fruit = str(sample.fruit_type or "").strip()
    locked_fruit = sample_fruit if sample_fruit.lower() in SUPPORTED_FRUITS else None

    # Product UI must not flicker with every noisy camera frame. Once the sample
    # has an accepted Apple/Banana/Tomato identity, that sample identity is the
    # operator-facing fruit name. Per-frame CV identity is still retained below
    # as diagnostic evidence and may trigger a conflict warning/correction in the
    # image router, but it no longer replaces the title on every refresh.
    if locked_fruit:
        fruit = locked_fruit.title()
    elif str(detected_fruit or "").lower() in SUPPORTED_FRUITS:
        fruit = detected_fruit
    else:
        fruit = detected_fruit or sample.fruit_type

    identity_conflict = bool(
        locked_fruit
        and str(detected_fruit or "").lower() in SUPPORTED_FRUITS
        and str(detected_fruit).lower() != locked_fruit.lower()
    )
    unsupported = str(fruit or "").lower() not in SUPPORTED_FRUITS

    gate_issues = list(image_quality["issues"])
    gate_issues.extend(protocol_state["issues"])
    if sensor_drift.get("suspected"):
        gate_issues.append("Sensor baseline drift warning requires review before relying on gas evidence.")
    if unsupported:
        gate_issues.append("Unsupported fruit. Current decision rules support Apple, Banana and Tomato only.")

    if gate_issues and decision.get("verdict_ready"):
        decision = {
            **decision,
            "status": "MORE EVIDENCE REQUIRED",
            "verdict_ready": False,
            "label": None,
            "freshness_score": None,
            "confidence": None,
            "risk": "unverified",
            "reason": " ".join(gate_issues),
        }

    visible_damage = (vision.get("defects") or {}).get("visible_damage_estimate_pct")
    product = recommendation(fruit, decision.get("label"), verdict_ready=decision.get("verdict_ready") is True, visible_damage_pct=visible_damage)
    score_info = score_breakdown(fusion)
    return {
        "inspection_id": sample.sample_id,
        "sample": sample_info(sample),
        "status": decision["status"],
        "evidence": evidence,
        "analysts": analysts,
        "critic": fusion["components"]["critic"],
        "decision": decision,
        "product": {
            "fruit": fruit,
            "detected_fruit": detected_fruit,
            "identity_conflict": identity_conflict,
            "recommendation": product,
            "score_breakdown": score_info,
            "provisional_quality_score": score_info.get("provisional_score"),
            "condition_comparison": _condition_comparison(db, sample.sample_id, fusion),
            "profile": profile,
            "protocol": protocol_state,
            "image_quality": image_quality,
            "sensor_drift": sensor_drift,
            "events": recent_events(db, sample.sample_id, 30),
            "provenance": decision_provenance(),
        },
        "timeline": timeline,
        "timeline_note": "Newest 200 frames, 200 readings and 100 stored fusion results; rolling preview retention may remove older frames. Analysis events share their frame timestamp.",
        "human_verifications": verifications,
    }
