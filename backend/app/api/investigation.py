from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample
from ..services.investigation import build_investigation_summary
from ..services.ollama_client import ollama_client

router = APIRouter(tags=["investigation"])


@router.get("/samples/{sample_id}/investigation")
def get_investigation(sample_id: str, db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return build_investigation_summary(db, sample)


@router.get("/ai/ollama/health")
async def ollama_health():
    return await ollama_client.health()


@router.post("/samples/{sample_id}/investigation/explain")
async def explain_investigation(sample_id: str, db: Session = Depends(get_db)):
    """Ask local Gemma to explain already-computed FreshFusion evidence.

    This endpoint never decides the freshness verdict. The deterministic
    investigation/critic result remains authoritative for gating.
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
        "analysts": investigation["analysts"],
        "critic": investigation["critic"],
        "decision": investigation["decision"],
    }
    explanation = await ollama_client.explain(evidence_payload)
    return {
        "status": "ready",
        "required_for_verdict": False,
        "explanation": explanation,
    }
