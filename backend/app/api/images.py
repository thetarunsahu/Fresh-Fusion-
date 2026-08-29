import secrets
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from PIL import Image
from ..config import UPLOAD_DIR
from ..database import get_db
from ..models import FruitImage, FruitSample
from ..realtime import manager
from ..services.image_analysis import analyze_image

router = APIRouter(prefix="/images", tags=["images"])
ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

@router.post("/upload")
async def upload_image(request: Request, sample_id: str = Form(...), angle: str = Form("unknown"), file: UploadFile = File(...), db: Session = Depends(get_db)):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample: raise HTTPException(404, "Sample not found")
    if file.content_type not in ALLOWED: raise HTTPException(415, "Only JPEG, PNG and WEBP images are supported")
    raw = await file.read()
    if len(raw) > 12 * 1024 * 1024: raise HTTPException(413, "Image must be under 12 MB")
    ext = ALLOWED[file.content_type]; filename = f"{sample_id}_{angle}_{secrets.token_hex(5)}{ext}"; path = UPLOAD_DIR / filename; path.write_bytes(raw)
    try:
        with Image.open(path) as im: width, height = im.size
        analysis = analyze_image(path)
        if analysis.get("artifacts"):
            analysis["artifacts"] = {k: str(request.base_url).rstrip("/") + f"/uploads/{v}" for k, v in analysis["artifacts"].items()}
    except Exception as exc:
        path.unlink(missing_ok=True); raise HTTPException(400, f"Image analysis failed: {exc}")
    url = str(request.base_url).rstrip("/") + f"/uploads/{filename}"
    record = FruitImage(sample_id=sample_id, angle=angle, filename=filename, original_name=file.filename, url=url, width=width, height=height, analysis=analysis)
    db.add(record); db.commit(); db.refresh(record)
    payload={"id":record.id,"sample_id":sample_id,"angle":angle,"url":url,"analysis":analysis,"uploaded_at":record.uploaded_at.isoformat()}
    await manager.broadcast(sample_id,{"type":"image","data":payload}); return payload
