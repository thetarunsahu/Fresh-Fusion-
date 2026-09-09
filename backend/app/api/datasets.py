from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitImage, HumanVerification, ValidationRun
from ..services.ai import MODEL_PATH, LABELS_PATH
from ..services.datasets import DATASETS, dataset_registry, reference_index_status
from ..services.validation import (
    current_validation_snapshot,
    persist_validation_run,
    serialize_validation_run,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/registry")
async def registry(fruit_type: str | None = None):
    return await dataset_registry(fruit_type)


@router.get("/reference-status")
def reference_status():
    return reference_index_status()


@router.get("/validation")
def validation(db: Session = Depends(get_db)):
    evaluation = current_validation_snapshot(db)
    latest_run = (
        db.query(ValidationRun)
        .order_by(ValidationRun.created_at.desc(), ValidationRun.id.desc())
        .first()
    )
    # Preserve the legacy metric contract without fabricating an empty matrix as
    # a measured result. Until at least one comparable human-labelled inspection
    # exists, every legacy metric value remains explicitly unavailable.
    has_comparable_samples = evaluation["sample_count"] > 0
    legacy_metrics = {
        name: {
            "status": evaluation["status"],
            "value": evaluation.get(name) if has_comparable_samples else None,
        }
        for name in ["accuracy", "precision", "recall", "f1", "confusion_matrix"]
    }
    return {
        "datasets": DATASETS,
        "reference_index": reference_index_status(),
        "labelled_images": db.query(FruitImage).filter(FruitImage.ground_truth.isnot(None)).count(),
        "human_ground_truth_records": db.query(HumanVerification).filter(HumanVerification.ground_truth.isnot(None)).count(),
        "human_labelled_inspections": db.query(HumanVerification.sample_id).filter(HumanVerification.ground_truth.isnot(None)).distinct().count(),
        "model": {
            "status": "artifacts_present_unverified" if MODEL_PATH.exists() and LABELS_PATH.exists() else "not_deployed",
            "note": (
                "Artifact presence does not establish successful inference or measured accuracy. "
                "Identity currently uses CV/reference heuristics."
            ),
        },
        "metrics": legacy_metrics,
        "evaluation": evaluation,
        "latest_persisted_run": serialize_validation_run(latest_run) if latest_run else None,
        "label_policy": (
            "FreshFusion human labels are stored separately from published fresh/normal/rotten reference classes. "
            "Reviews are not automatically propagated to every camera frame."
        ),
    }


@router.post("/validation-runs", status_code=201)
def create_validation_run(
    name: str = Query(default="manual", min_length=1, max_length=120),
    db: Session = Depends(get_db),
):
    return serialize_validation_run(persist_validation_run(db, name=name))


@router.get("/validation-runs")
def list_validation_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ValidationRun)
        .order_by(ValidationRun.created_at.desc(), ValidationRun.id.desc())
        .limit(limit)
        .all()
    )
    return [serialize_validation_run(row) for row in rows]
