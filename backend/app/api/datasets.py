from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitImage, HumanVerification
from ..services.ai import MODEL_PATH, LABELS_PATH
from ..services.datasets import DATASETS, dataset_registry, reference_index_status
from ..services.validation_metrics import compute_metrics, split_manifest

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/registry")
async def registry(fruit_type: str | None = None):
    return await dataset_registry(fruit_type)


@router.get("/reference-status")
def reference_status():
    return reference_index_status()


@router.get("/validation")
def validation(db: Session = Depends(get_db)):
    real = compute_metrics(db)
    metrics = {
        "accuracy": {"status": real["status"], "value": real["accuracy"]},
        "precision": {"status": real["status"], "value": real["macro_precision"]},
        "recall": {"status": real["status"], "value": real["macro_recall"]},
        "f1": {"status": real["status"], "value": real["macro_f1"]},
        "confusion_matrix": {"status": real["status"], "value": real["confusion_matrix"]},
    }
    return {
        "datasets": DATASETS,
        "reference_index": reference_index_status(),
        "labelled_images": db.query(FruitImage).filter(FruitImage.ground_truth.isnot(None)).count(),
        "human_ground_truth_records": db.query(HumanVerification).filter(HumanVerification.ground_truth.isnot(None)).count(),
        "human_labelled_inspections": db.query(HumanVerification.sample_id).filter(HumanVerification.ground_truth.isnot(None)).distinct().count(),
        "model": {
            "status": "artifacts_present_unverified" if MODEL_PATH.exists() and LABELS_PATH.exists() else "not_deployed",
            "note": "Artifact presence does not establish successful inference or measured accuracy. Identity currently uses CV/reference heuristics plus conservative Tomato compatibility support.",
        },
        "metrics": metrics,
        "validation": real,
        "claim_ready": real["claim_ready"],
        "label_policy": "FreshFusion human labels are stored separately from published reference classes. Metrics use only human ground truth paired with verified system decisions.",
        "split_policy": "Repeated views and repeated inspections should share a fruit_instance_id; deterministic split assignment then keeps that physical specimen in one train/validation/test partition.",
    }


@router.get("/validation/manifest")
def validation_manifest(db: Session = Depends(get_db)):
    return split_manifest(db)
