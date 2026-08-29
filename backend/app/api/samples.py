from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FruitSample
from ..schemas import SampleCreate, SampleOut

router = APIRouter(prefix="/api/samples", tags=["samples"])


@router.post("", response_model=SampleOut, status_code=201)
def create_sample(payload: SampleCreate, db: Session = Depends(get_db)) -> FruitSample:
    prefix = "".join(ch for ch in payload.fruit_type.upper() if ch.isalnum())[:3] or "FRT"
    sample = FruitSample(
        sample_code=f"{prefix}-{uuid4().hex[:6].upper()}",
        fruit_type=payload.fruit_type.strip().title(),
        notes=payload.notes,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


@router.get("", response_model=list[SampleOut])
def list_samples(limit: int = 50, db: Session = Depends(get_db)) -> list[FruitSample]:
    limit = min(max(limit, 1), 200)
    return list(
        db.scalars(select(FruitSample).order_by(FruitSample.created_at.desc()).limit(limit)).all()
    )


@router.get("/{sample_code}", response_model=SampleOut)
def get_sample(sample_code: str, db: Session = Depends(get_db)) -> FruitSample:
    sample = db.scalar(select(FruitSample).where(FruitSample.sample_code == sample_code))
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample
