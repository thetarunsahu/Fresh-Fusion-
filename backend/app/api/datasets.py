from fastapi import APIRouter

from ..services.datasets import dataset_registry, reference_index_status

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/registry")
async def registry(fruit_type: str | None = None):
    return await dataset_registry(fruit_type)


@router.get("/reference-status")
def reference_status():
    return reference_index_status()
