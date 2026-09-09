from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample, InvestigationRun
from ..services.investigation_core.investigation import investigate as build_investigation_summary
from ..services.ollama_client import ollama_client

router = APIRouter(tags=["investigation"])


def _snapshot_payload(investigation: dict) -> dict:
    return {
        "inspection_id": investigation.get("inspection_id"),
        "sample": investigation.get("sample"),
        "evidence": investigation.get("evidence"),
        "analysts": investigation.get("analysts"),
        "agreement": investigation.get("agreement"),
        "critic": investigation.get("critic"),
        "decision": investigation.get("decision"),
    }


def _serialize_run(row: InvestigationRun) -> dict:
    return {
        "id": row.id,
        "sample_id": row.sample_id,
        "trigger": row.trigger,
        "snapshot": row.snapshot or {},
        "llm_explanation": row.llm_explanation,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/samples/{sample_id}/investigation")
def get_investigation(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return build_investigation_summary(db, sample)


@router.post("/samples/{sample_id}/investigation/snapshot", status_code=201)
def save_investigation_snapshot(
    sample_id: str,
    trigger: str = Query(default="manual", min_length=1, max_length=40),
    db: Session = Depends(get_db),
):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    investigation = build_investigation_summary(db, sample)
    row = InvestigationRun(
        sample_id=sample_id,
        trigger=trigger,
        snapshot=_snapshot_payload(investigation),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_run(row)


@router.get("/samples/{sample_id}/investigation/snapshots")
def list_investigation_snapshots(
    sample_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    exists = db.query(FruitSample.id).filter(FruitSample.sample_id == sample_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Sample not found")
    rows = (
        db.query(InvestigationRun)
        .filter(InvestigationRun.sample_id == sample_id)
        .order_by(InvestigationRun.created_at.desc(), InvestigationRun.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_run(row) for row in rows]


@router.get("/ai/ollama/health")
async def ollama_health():
    return await ollama_client.health()


@router.post("/samples/{sample_id}/investigation/explain")
async def explain_investigation(
    sample_id: str,
    question: str | None = Query(default=None, max_length=600),
    db: Session = Depends(get_db),
):
    """Explain or answer a question using already-computed FreshFusion evidence.

    Gemma never decides freshness. The deterministic investigation/critic result
    remains authoritative for release gating.
    """
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
        "evidence": investigation["evidence"],
        "analysts": investigation["analysts"],
        "agreement": investigation.get("agreement"),
        "critic": investigation["critic"],
        "decision": investigation["decision"],
        "human_verifications": investigation.get("human_verifications", []),
    }
    explanation = await ollama_client.explain(evidence_payload, question=question)

    row = InvestigationRun(
        sample_id=sample_id,
        trigger="gemma-question" if question else "gemma-explanation",
        snapshot=_snapshot_payload(investigation),
        llm_explanation=explanation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "status": "ready",
        "required_for_verdict": False,
        "snapshot_id": row.id,
        "question": question,
        "explanation": explanation,
    }
