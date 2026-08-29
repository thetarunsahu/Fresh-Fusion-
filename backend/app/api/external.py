from fastapi import APIRouter
from ..services.external import external_context

router = APIRouter(prefix="/external", tags=["external"])

@router.get("/context")
async def context(fruit_type: str = "Banana", lat: float | None = None, lon: float | None = None):
    return await external_context(fruit_type, lat, lon)
