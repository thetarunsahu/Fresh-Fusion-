import os
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..database import get_db
from ..models import FruitImage, FruitSample, FusionResult
from ..realtime import manager
from ..services.fusion import compute_fusion
from ..services.image_analysis import analyze_image

router = APIRouter(prefix='/images', tags=['images'])
ALLOWED = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
STREAM_KEEP = max(10, int(os.getenv('STREAM_KEEP', '30')))
FUSION_KEEP = max(40, int(os.getenv('FUSION_KEEP', '200')))
AUTO_IDENTITY_CONFIDENCE = float(os.getenv('AUTO_IDENTITY_CONFIDENCE', '72'))
AUTO_SCREEN_BLOCK = float(os.getenv('AUTO_SCREEN_BLOCK', '65'))


def _relative_artifacts(analysis: dict) -> dict:
    if analysis.get('artifacts'):
        analysis['artifacts'] = {k: f'/uploads/{Path(str(v)).name}' for k, v in analysis['artifacts'].items()}
    return analysis


def _delete_image_files(record: FruitImage) -> None:
    (UPLOAD_DIR / record.filename).unlink(missing_ok=True)
    for value in (record.analysis or {}).get('artifacts', {}).values():
        (UPLOAD_DIR / Path(str(value)).name).unlink(missing_ok=True)


def _trim_stream(db: Session, sample_id: str) -> None:
    stale = (db.query(FruitImage)
        .filter(FruitImage.sample_id == sample_id, FruitImage.angle.like('live-%'))
        .order_by(FruitImage.uploaded_at.desc())
        .offset(STREAM_KEEP).all())
    for row in stale:
        _delete_image_files(row)
        db.delete(row)
    old_results = (db.query(FusionResult)
        .filter(FusionResult.sample_id == sample_id)
        .order_by(FusionResult.created_at.desc())
        .offset(FUSION_KEEP).all())
    for row in old_results:
        db.delete(row)
    if stale or old_results:
        db.commit()


def _identity(analysis: dict) -> tuple[str, float]:
    identity = analysis.get('identity', {})
    return str(identity.get('fruit') or 'Unknown'), float(identity.get('confidence') or 0.0)


def _route_detected_fruit(db: Session, sample: FruitSample, analysis: dict) -> tuple[FruitSample, dict]:
    candidate, confidence = _identity(analysis)
    screen_suspicion = float(analysis.get('presentation', {}).get('screen_suspicion_pct') or 0.0)
    event = {
        'detected_fruit': candidate,
        'identity_confidence': confidence,
        'screen_suspicion_pct': screen_suspicion,
        'sample_changed': False,
        'previous_sample_id': sample.sample_id,
    }
    if analysis.get('quality', {}).get('fruit_present') is not True:
        return sample, event
    if screen_suspicion >= AUTO_SCREEN_BLOCK:
        event['routing_blocked'] = 'suspected_screen_or_photo'
        return sample, event
    if candidate not in {'Apple', 'Banana'} or confidence < AUTO_IDENTITY_CONFIDENCE:
        return sample, event

    current = (sample.fruit_type or 'Auto').strip().title()
    if current in {'Auto', 'Fruit', 'Unknown'}:
        sample.fruit_type = candidate
        db.add(sample)
        db.commit()
        db.refresh(sample)
        event['auto_selected'] = True
        return sample, event
    if current == candidate:
        return sample, event

    recent = (db.query(FruitImage)
        .filter(FruitImage.sample_id == sample.sample_id, FruitImage.angle.like('live-%'))
        .order_by(FruitImage.uploaded_at.desc())
        .limit(2).all())
    stable = []
    for row in recent:
        row_analysis = row.analysis or {}
        row_candidate, row_confidence = _identity(row_analysis)
        row_screen = float(row_analysis.get('presentation', {}).get('screen_suspicion_pct') or 0.0)
        if (
            row_analysis.get('quality', {}).get('fruit_present') is True
            and row_candidate == candidate
            and row_confidence >= max(64.0, AUTO_IDENTITY_CONFIDENCE - 8.0)
            and row_screen < AUTO_SCREEN_BLOCK
        ):
            stable.append(row)

    if len(stable) < 2:
        event['pending_switch'] = True
        event['candidate_frames'] = len(stable) + 1
        return sample, event

    prefix = candidate[:3].upper()
    new_sample = FruitSample(
        sample_id=f'{prefix}-{secrets.token_hex(3).upper()}',
        fruit_type=candidate,
        source='auto-camera-switch',
        status='collecting',
    )
    db.add(new_sample)
    db.flush()
    for row in stable:
        row.sample_id = new_sample.sample_id
        db.add(row)
    db.commit()
    db.refresh(new_sample)
    event.update({
        'sample_changed': True,
        'new_sample_id': new_sample.sample_id,
        'moved_previous_candidate_frames': len(stable),
    })
    return new_sample, event


async def _store(file: UploadFile, sample_id: str, angle: str, ground_truth: str | None, max_bytes: int, db: Session):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(404, 'Sample not found')
    if file.content_type not in ALLOWED:
        raise HTTPException(415, 'Only JPEG, PNG and WEBP images are supported')
    raw = await file.read()
    if len(raw) > max_bytes:
        raise HTTPException(413, f'Image must be under {max_bytes // (1024*1024)} MB')

    ext = ALLOWED[file.content_type]
    filename = f'{sample_id}_{angle}_{secrets.token_hex(5)}{ext}'
    path = UPLOAD_DIR / filename
    path.write_bytes(raw)
    try:
        with Image.open(path) as im:
            width, height = im.size
        analysis = _relative_artifacts(analyze_image(path, sample.fruit_type))
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(400, f'Image analysis failed: {exc}')

    sample, auto_event = _route_detected_fruit(db, sample, analysis)
    sample_id = sample.sample_id

    record = FruitImage(
        sample_id=sample_id,
        angle=angle,
        filename=filename,
        original_name=file.filename,
        ground_truth=ground_truth or None,
        url=f'/uploads/{filename}',
        width=width,
        height=height,
        analysis=analysis,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    fusion = compute_fusion(db, sample)
    if angle.startswith('live-'):
        _trim_stream(db, sample_id)

    validation = (fusion.components or {}).get('validation', {})
    payload = {
        'id': record.id,
        'sample_id': sample_id,
        'fruit_type': sample.fruit_type,
        'angle': angle,
        'ground_truth': record.ground_truth,
        'url': record.url,
        'analysis': analysis,
        'auto_detection': auto_event,
        'physical_validation': validation,
        'uploaded_at': record.uploaded_at.isoformat(),
        'fusion': {
            'freshness_score': fusion.freshness_score,
            'sensor_score': fusion.sensor_score,
            'vision_score': fusion.vision_score,
            'label': fusion.label,
            'confidence': fusion.confidence,
            'risk': fusion.risk,
            'verdict_ready': bool(validation.get('verdict_ready')),
        },
    }
    await manager.broadcast(sample_id, {'type': 'vision-frame', 'data': payload})
    return payload


@router.post('/upload')
async def upload_image(sample_id: str = Form(...), angle: str = Form('unknown'), ground_truth: str | None = Form(None), file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await _store(file, sample_id, angle, ground_truth, 12 * 1024 * 1024, db)


@router.post('/stream-frame')
async def stream_frame(sample_id: str = Form(...), view: str = Form('front'), ground_truth: str | None = Form(None), file: UploadFile = File(...), db: Session = Depends(get_db)):
    safe_view = view.lower() if view.lower() in {'front', 'back', 'left', 'right', 'top'} else 'front'
    return await _store(file, sample_id, f'live-{safe_view}', ground_truth, 4 * 1024 * 1024, db)
