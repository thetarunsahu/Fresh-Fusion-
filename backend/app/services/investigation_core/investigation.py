from ..fusion import evaluate_fusion
from ...models import FruitImage, FusionResult, InspectionProfile
from ..inspection_events import recent_events
from ..image_quality_gate import evaluate_image_quality
from ..product_rules import recommendation, score_breakdown
from .evidence import collect_evidence, sample_info
from .analysts import summarize_analysts
from .confidence import decision_from_fusion


def _profile_info(db, sample_id):
    row = db.query(InspectionProfile).filter_by(sample_id=sample_id).first()
    if not row:
        return {"fruit_count": 1, "approximate_weight_g": None, "batch_id": None, "supplier": None,
                "storage_location": None, "protocol": {}}
    return {"fruit_count": row.fruit_count, "approximate_weight_g": row.approximate_weight_g,
            "batch_id": row.batch_id, "supplier": row.supplier, "storage_location": row.storage_location,
            "protocol": row.protocol or {}}


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
    if image_quality["blocking"] and decision.get("verdict_ready"):
        decision = {
            **decision,
            "status": "MORE EVIDENCE REQUIRED",
            "verdict_ready": False,
            "label": None,
            "freshness_score": None,
            "confidence": None,
            "risk": "unverified",
            "reason": " ".join(image_quality["issues"]),
        }
    analysts = summarize_analysts(evidence, fusion)
    vision = analysts.get("vision", {})
    fruit = (vision.get("identity") or {}).get("fruit") or sample.fruit_type
    visible_damage = (vision.get("defects") or {}).get("visible_damage_estimate_pct")
    product = recommendation(fruit, decision.get("label"), verdict_ready=decision.get("verdict_ready") is True, visible_damage_pct=visible_damage)
    return {
        "inspection_id": sample.sample_id,
        "sample": sample_info(sample),
        "status": decision["status"],
        "evidence": evidence,
        "analysts": analysts,
        "critic": fusion["components"]["critic"],
        "decision": decision,
        "product": {
            "recommendation": product,
            "score_breakdown": score_breakdown(fusion),
            "condition_comparison": _condition_comparison(db, sample.sample_id, fusion),
            "profile": _profile_info(db, sample.sample_id),
            "image_quality": image_quality,
            "events": recent_events(db, sample.sample_id, 30),
        },
        "timeline": timeline,
        "timeline_note": "Newest 200 frames, 200 readings and 100 stored fusion results; rolling preview retention may remove older frames. Analysis events share their frame timestamp.",
        "human_verifications": verifications,
    }
