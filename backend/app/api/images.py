import os
import secrets
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from ..config import UPLOAD_DIR
from ..database import get_db
from ..models import FruitImage, FruitSample, HumanVerification
from ..realtime import manager
from ..services.fusion import compute_fusion
from ..services.image_analysis import analyze_image
from ..services.fruit_identity_extension import enhance_identity
from ..services.inspection_control import active_sample, set_active
from ..services.sensor_assessment import utc_iso

router = APIRouter(prefix='/images', tags=['images'])
ALLOWED = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
STREAM_KEEP = max(10, int(os.getenv('STREAM_KEEP', '30')))
AUTO_IDENTITY_CONFIDENCE = float(os.getenv('AUTO_IDENTITY_CONFIDENCE', '72'))
AUTO_SCREEN_BLOCK = float(os.getenv('AUTO_SCREEN_BLOCK', '65'))
IDENTITY_BOOTSTRAP_FRAMES = max(3, int(os.getenv('IDENTITY_BOOTSTRAP_FRAMES', '3')))


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
        .filter(FruitImage.sample_id == sample_id, FruitImage.angle.like('live-%'), FruitImage.ground_truth.is_(None))
        .order_by(FruitImage.uploaded_at.desc())
        .offset(STREAM_KEEP).all())
    protected = {(review.assessment or {}).get('evidence_image_id') for review in db.query(HumanVerification).filter_by(sample_id=sample_id)}
    for row in stale:
        if row.id in protected:
            continue
        _delete_image_files(row)
        db.delete(row)
    if stale:
        db.commit()


def _identity(analysis: dict) -> tuple[str, float]:
    identity = analysis.get('identity', {})
    return str(identity.get('fruit') or 'Unknown'), float(identity.get('confidence') or 0.0)


def _required_identity_confidence(candidate: str) -> float:
    # Tomato remains slightly stricter because red apples can overlap in RGB
    # appearance. Stability comes mainly from temporal consensus below.
    return max(AUTO_IDENTITY_CONFIDENCE, 82.0) if candidate == 'Tomato' else AUTO_IDENTITY_CONFIDENCE


def _recent_identity_votes(db: Session, sample_id: str, limit: int = 6) -> list[dict]:
    rows = (db.query(FruitImage)
        .filter(FruitImage.sample_id == sample_id, FruitImage.angle.like('live-%'))
        .order_by(FruitImage.uploaded_at.desc(), FruitImage.id.desc())
        .limit(limit).all())
    votes = []
    for row in rows:
        row_analysis = row.analysis or {}
        fruit, confidence = _identity(row_analysis)
        screen = float(row_analysis.get('presentation', {}).get('screen_suspicion_pct') or 0.0)
        threshold = max(64.0, _required_identity_confidence(fruit) - 8.0)
        if (
            row_analysis.get('quality', {}).get('fruit_present') is True
            and fruit in {'Apple', 'Banana', 'Tomato'}
            and confidence >= threshold
            and screen < AUTO_SCREEN_BLOCK
        ):
            votes.append({'fruit': fruit, 'confidence': confidence})
    return votes


def _identity_consensus(candidate: str, confidence: float, history: list[dict]) -> dict:
    window = [{'fruit': candidate, 'confidence': confidence}, *history][:5]
    counts = Counter(item['fruit'] for item in window)
    candidate_count = counts.get(candidate, 0)
    other_count = sum(value for key, value in counts.items() if key != candidate)
    matching = [item['confidence'] for item in window if item['fruit'] == candidate]
    average = sum(matching) / max(len(matching), 1)
    return {
        'stable': candidate_count >= IDENTITY_BOOTSTRAP_FRAMES and candidate_count > other_count,
        'candidate_frames': candidate_count,
        'required_frames': IDENTITY_BOOTSTRAP_FRAMES,
        'average_confidence': round(average, 1),
        'recent_votes': [item['fruit'] for item in window],
    }


def _route_detected_fruit(db: Session, sample: FruitSample, analysis: dict) -> tuple[FruitSample, dict]:
    candidate, confidence = _identity(analysis)
    screen_suspicion = float(analysis.get('presentation', {}).get('screen_suspicion_pct') or 0.0)
    current = (sample.fruit_type or 'Auto').strip().title()
    event = {
        'detected_fruit': candidate,
        'identity_confidence': confidence,
        'screen_suspicion_pct': screen_suspicion,
        'sample_changed': False,
        'previous_sample_id': sample.sample_id,
        'locked_identity': current if current in {'Apple', 'Banana', 'Tomato'} else None,
    }

    if analysis.get('quality', {}).get('fruit_present') is not True:
        event['routing_blocked'] = 'no_usable_fruit_region'
        return sample, event
    if screen_suspicion >= AUTO_SCREEN_BLOCK:
        event['routing_blocked'] = 'suspected_screen_or_photo'
        return sample, event

    threshold = _required_identity_confidence(candidate)
    if candidate not in {'Apple', 'Banana', 'Tomato'} or confidence < threshold:
        event['routing_blocked'] = 'identity_confidence_too_low'
        event['required_confidence'] = threshold
        return sample, event

    # Once an inspection has a fruit identity, keep it stable. A noisy frame must
    # never turn Banana -> Apple -> Banana inside the same inspection. If the user
    # physically changes fruit, start a new inspection instead of silently moving
    # evidence between samples.
    if current in {'Apple', 'Banana', 'Tomato'}:
        if current == candidate:
            event['stable_identity'] = current
        else:
            event['identity_conflict'] = True
            event['routing_blocked'] = 'inspection_identity_locked'
            event['message'] = f'Inspection is locked to {current}; current frame looks like {candidate}. Start a new inspection if the physical fruit changed.'
        return sample, event

    history = _recent_identity_votes(db, sample.sample_id, 6)
    consensus = _identity_consensus(candidate, confidence, history)
    event['identity_consensus'] = consensus

    # Auto mode is intentionally not decided from one frame. Three agreeing frames
    # are required before we write the fruit family into the sample.
    if not consensus['stable']:
        event['pending_identity'] = True
        return sample, event

    sample.fruit_type = candidate
    db.add(sample)
    db.commit()
    db.refresh(sample)
    event['auto_selected'] = True
    event['stable_identity'] = candidate
    return sample, event


async def _store(file: UploadFile, sample_id: str, angle: str, ground_truth: str | None, max_bytes: int, db: Session):
    sample = db.query(FruitSample).filter(FruitSample.sample_id == sample_id).first()
    if not sample:
        raise HTTPException(404, 'Sample not found')
    if angle not in {'unknown', 'front', 'back', 'left', 'right', 'top', 'live-front', 'live-back', 'live-left', 'live-right', 'live-top'}:
        raise HTTPException(422, 'Unsupported camera view')
    if ground_truth and ground_truth not in {'fresh', 'ripe', 'overripe', 'spoiled'}:
        raise HTTPException(422, 'Unsupported FreshFusion ground-truth label')
    capture_target = active_sample(db)
    if angle.startswith('live-') and capture_target and capture_target.sample_id != sample_id:
        raise HTTPException(409, 'Capture target changed. Select the active inspection on the phone or reopen its QR link.')
    if file.content_type not in ALLOWED:
        raise HTTPException(415, 'Only JPEG, PNG and WEBP images are supported')
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(413, f'Image must be under {max_bytes // (1024*1024)} MB')

    ext = ALLOWED[file.content_type]
    filename = f'{sample_id}_{angle}_{secrets.token_hex(5)}{ext}'
    path = UPLOAD_DIR / filename
    path.write_bytes(raw)
    try:
        with Image.open(path) as im:
            width, height = im.size
        analysis = await run_in_threadpool(analyze_image, path, sample.fruit_type)
        analysis = enhance_identity(analysis, sample.fruit_type)
        analysis = _relative_artifacts(analysis)
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

    fusion = await run_in_threadpool(compute_fusion, db, sample)
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
        'uploaded_at': utc_iso(record.uploaded_at),
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
