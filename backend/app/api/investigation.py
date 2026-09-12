from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample, InvestigationRun
from ..schemas import AssistantQuestionIn
from ..services.investigation_core.investigation import investigate as build_investigation_summary
from ..services.inspection_events import record_event
from ..services.ollama_client import ollama_client

router = APIRouter(tags=["investigation"])


def _deterministic_assistant(question: str, investigation: dict) -> dict:
    """Useful fallback when Ollama is offline; never fabricates measurements."""
    q = question.lower()
    decision = investigation.get("decision") or {}
    product = investigation.get("product") or {}
    analysts = investigation.get("analysts") or {}
    sensor = analysts.get("sensor") or {}
    vision = analysts.get("vision") or {}
    multiview = analysts.get("multiview") or {}
    image_quality = product.get("image_quality") or {}
    comparison = product.get("condition_comparison") or {}
    recommendation = product.get("recommendation") or {}
    score_info = product.get("score_breakdown") or {}
    fruit = product.get("fruit") or (investigation.get("sample") or {}).get("fruit_type") or "fruit"
    score = decision.get("freshness_score") if decision.get("verdict_ready") else product.get("provisional_quality_score") or score_info.get("provisional_score")
    damage = (vision.get("defects") or {}).get("visible_damage_estimate_pct")
    views_count = multiview.get("views_count") or len(multiview.get("views") or [])

    if any(word in q for word in ("score", "why", "freshness", "quality")):
        pieces = []
        if score is not None:
            pieces.append(f"current {'final' if decision.get('verdict_ready') else 'provisional'} quality score {round(float(score))}/100")
        sensor_score = score_info.get("sensor", {}).get("score")
        vision_score = score_info.get("vision", {}).get("provisional_score") or score_info.get("vision", {}).get("score")
        if vision_score is not None:
            pieces.append(f"vision evidence {round(float(vision_score))}/100")
        if sensor_score is not None:
            pieces.append(f"sensor evidence {round(float(sensor_score))}/100")
        if damage is not None:
            pieces.append(f"visible surface damage {round(float(damage))}%")
        pieces.append(f"{views_count}/3 changed views verified")
        reason = decision.get("reason") or "The evidence gate is still being checked."
        return {
            "answer": f"For this {fruit}, " + ", ".join(pieces) + f". {reason}",
            "evidence_used": ["live quality score", "vision evidence", "sensor evidence", "multi-view status"],
            "uncertainty": "The score is provisional until the final evidence gate passes; prototype weights are not validated scientific constants.",
            "next_action": recommendation.get("action") or ("Capture the remaining changed views and keep the ESP32 reading current." if views_count < 3 else "Complete the remaining evidence check shown in Live Inspection."),
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    if any(word in q for word in ("sell", "sale", "action", "do", "recommend")):
        answer = recommendation.get("action") or "Collect more evidence before taking a stock action."
        reason = recommendation.get("reason") or decision.get("reason") or "The current evidence is still incomplete."
        return {
            "answer": f"Recommended action: {answer}. {reason}",
            "evidence_used": ["deterministic recommendation", "current decision state"],
            "uncertainty": "Recommendation rules are decision support and still require dataset calibration.",
            "next_action": recommendation.get("next_action") or answer,
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    if any(word in q for word in ("gas", "mq135", "sensor", "temperature", "humidity")):
        latest = sensor.get("latest") or {}
        baseline = sensor.get("baseline") or {}
        delta = sensor.get("baseline_delta_raw")
        trend = sensor.get("trend") or {}
        pieces = []
        if latest.get("temperature") is not None:
            pieces.append(f"temperature {latest['temperature']}°C")
        if latest.get("humidity") is not None:
            pieces.append(f"humidity {latest['humidity']}%")
        if latest.get("mq135_raw") is not None:
            pieces.append(f"MQ135 raw {latest['mq135_raw']} ADC")
        if delta is not None:
            pieces.append(f"baseline delta {delta:+.0f} ADC")
        if trend.get("direction"):
            pieces.append(f"gas trend {trend['direction']}")
        answer = "Current sensor evidence: " + (", ".join(pieces) if pieces else "no usable sensor reading is available yet") + "."
        if not baseline.get("available"):
            answer += " An empty-chamber baseline has not been established yet."
        answer += " MQ135 is treated as raw/relative evidence, not calibrated ppm."
        return {
            "answer": answer,
            "evidence_used": ["latest sensor reading", "MQ135 baseline/trend"],
            "uncertainty": "No universal fresh-fruit MQ135 value is assumed.",
            "next_action": "Record a stable empty-chamber baseline and compare repeated fruit readings." if not baseline.get("available") else "Continue collecting repeated readings under the same chamber protocol.",
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    if any(word in q for word in ("image", "camera", "blur", "light", "view", "photo", "missing", "evidence")):
        issues = image_quality.get("issues") or []
        answer = "Camera evidence is usable." if not image_quality.get("blocking") else "Camera evidence needs improvement before the result can be trusted."
        if issues:
            answer += " " + " ".join(str(x) for x in issues[:3])
        answer += f" Current changed-view coverage is {views_count}/3. One camera is enough for fruit identity; the extra views improve surface coverage and physical verification."
        return {
            "answer": answer,
            "evidence_used": ["image quality gate", "multi-view check"],
            "uncertainty": "Phone-camera physical verification is probabilistic and does not provide true depth sensing.",
            "next_action": "Capture the remaining clear, well-lit changed viewpoints of the same physical fruit." if views_count < 3 else "Review any remaining sensor or critic warning shown in Live Inspection.",
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    if any(word in q for word in ("change", "previous", "worse", "better", "trend")):
        if comparison.get("available"):
            change = comparison.get("score_change")
            direction = "improved" if (change or 0) > 0 else "declined" if (change or 0) < 0 else "stayed similar"
            answer = f"Compared with the previous verified assessment, the condition {direction}. Previous: {comparison.get('previous_label')}; current: {comparison.get('current_label')}; score change: {change:+.1f}."
        else:
            answer = "There is not yet a previous verified assessment that can be compared with the current one."
        return {
            "answer": answer,
            "evidence_used": ["previous verified assessment", "current deterministic assessment"],
            "uncertainty": "Only verified assessment snapshots are compared.",
            "next_action": "Re-inspect the same fruit later using the same capture and sensor protocol.",
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    if not decision.get("verdict_ready"):
        latest = sensor.get("latest") or {}
        compact = []
        if score is not None:
            compact.append(f"provisional score {round(float(score))}/100")
        if damage is not None:
            compact.append(f"visible damage {round(float(damage))}%")
        if latest.get("mq135_raw") is not None:
            compact.append(f"MQ135 {latest['mq135_raw']} ADC")
        compact.append(f"views {views_count}/3")
        return {
            "answer": f"Current {fruit} snapshot: " + ", ".join(compact) + ". " + str(decision.get("reason") or "More evidence is required before the final verdict is released."),
            "evidence_used": ["current fruit identity", "live score", "sensor evidence", "evidence critic"],
            "uncertainty": "The assessment is intentionally locked until required evidence is available.",
            "next_action": recommendation.get("action") or "Follow the highlighted evidence request shown on the Live Inspection page.",
            "model": "deterministic-fallback",
            "role": "evidence_qna_only",
        }

    return {
        "answer": f"Current verified condition for {fruit}: {decision.get('label')}. Score: {decision.get('freshness_score')}/100. Risk: {decision.get('risk')}. " + str(decision.get("reason") or "The result uses the currently verified evidence."),
        "evidence_used": ["deterministic decision", "evidence critic", "sensor and vision evidence"],
        "uncertainty": "Freshness scoring remains calibration-dependent and is not food-safety certification.",
        "next_action": recommendation.get("action") or "Continue monitoring if the fruit remains in storage.",
        "model": "deterministic-fallback",
        "role": "evidence_qna_only",
    }


@router.get("/samples/{sample_id}/investigation")
def get_investigation(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return build_investigation_summary(db, sample)


@router.post("/samples/{sample_id}/investigation/snapshot")
def save_investigation_snapshot(
    sample_id: str,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    snapshot = build_investigation_summary(db, sample)
    trigger = str(payload.get("trigger") or "manual-ui")[:40]
    run = InvestigationRun(sample_id=sample_id, trigger=trigger, snapshot=snapshot)
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "id": run.id,
        "sample_id": sample_id,
        "trigger": run.trigger,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.get("/ai/ollama/health")
async def ollama_health():
    return await ollama_client.health()


@router.post("/samples/{sample_id}/investigation/explain")
async def explain_investigation(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    investigation = build_investigation_summary(db, sample)
    health = await ollama_client.health()
    if not health.get("available"):
        return {
            "status": "ollama-unavailable",
            "required_for_verdict": False,
            "health": health,
            "explanation": None,
        }
    if not health.get("model_installed", True):
        return {
            "status": "model-not-installed",
            "required_for_verdict": False,
            "health": health,
            "explanation": None,
        }

    evidence_payload = {
        "sample": investigation["sample"],
        "analysts": investigation["analysts"],
        "critic": investigation["critic"],
        "decision": investigation["decision"],
        "product": investigation.get("product", {}),
    }
    explanation = await ollama_client.explain(evidence_payload)
    return {
        "status": "ready",
        "required_for_verdict": False,
        "explanation": explanation,
    }


@router.post("/samples/{sample_id}/assistant/ask")
async def ask_assistant(sample_id: str, payload: AssistantQuestionIn, db: Session = Depends(get_db)):
    """Interactive assistant grounded in the current inspection and prior verified context."""
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    investigation = build_investigation_summary(db, sample)
    evidence_payload = {
        "sample": investigation.get("sample"),
        "decision": investigation.get("decision"),
        "critic": investigation.get("critic"),
        "analysts": investigation.get("analysts"),
        "product": investigation.get("product"),
        "recent_human_verifications": (investigation.get("human_verifications") or [])[:5],
    }

    health = await ollama_client.health()
    if health.get("available") and health.get("model_installed", True):
        try:
            response = await ollama_client.answer(payload.question, evidence_payload)
            mode = "gemma"
        except Exception:
            response = _deterministic_assistant(payload.question, investigation)
            mode = "deterministic-fallback"
    else:
        response = _deterministic_assistant(payload.question, investigation)
        mode = "deterministic-fallback"

    record_event(
        db,
        sample_id,
        "assistant_question",
        "FreshFusion Assistant answered an operator question.",
        severity="info",
        payload={
            "question": payload.question,
            "answer": response.get("answer"),
            "mode": mode,
            "evidence_used": response.get("evidence_used", []),
        },
    )
    db.commit()
    return {
        "status": "ready",
        "mode": mode,
        "required_for_verdict": False,
        "response": response,
    }