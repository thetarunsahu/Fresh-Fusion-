from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FruitImage, HumanVerification
from ..services.ai import MODEL_PATH, LABELS_PATH
from ..services.datasets import DATASETS

from ..services.datasets import dataset_registry, reference_index_status

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/registry")
async def registry(fruit_type: str | None = None):
    return await dataset_registry(fruit_type)


@router.get("/reference-status")
def reference_status():
    return reference_index_status()

@router.get('/validation')
def validation(db: Session = Depends(get_db)):
    return {
        'datasets': DATASETS,
        'reference_index': reference_index_status(),
        'labelled_images': db.query(FruitImage).filter(FruitImage.ground_truth.isnot(None)).count(),
        'human_ground_truth_records': db.query(HumanVerification).filter(HumanVerification.ground_truth.isnot(None)).count(),
        'human_labelled_inspections': db.query(HumanVerification.sample_id).filter(HumanVerification.ground_truth.isnot(None)).distinct().count(),
        'model': {'status': 'artifacts_present_unverified' if MODEL_PATH.exists() and LABELS_PATH.exists() else 'not_deployed',
                  'note': 'Artifact presence does not establish successful inference or measured accuracy. Identity currently uses CV/reference heuristics.'},
        'metrics': {name: {'status': 'NOT YET VALIDATED', 'value': None} for name in ['accuracy', 'precision', 'recall', 'f1', 'confusion_matrix']},
        'label_policy': 'FreshFusion human labels are stored separately from published fresh/normal/rotten reference classes. Reviews are not automatically propagated to every camera frame.',
    }
