import os
import secrets
from collections import Counter
from datetime import datetime
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
from ..services.inspection_control import active_sample
from ..services.sensor_assessment import utc_iso

router = APIRouter(prefix='/images', tags=['images'])
ALLOWED = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
STREAM_KEEP = max(10, int(os.getenv('STREAM_KEEP', '30')))
AUTO_IDENTITY_CONFIDENCE = float(os.getenv('AUTO_IDENTITY_CONFIDENCE', '72'))
AUTO_SCREEN_BLOCK = float(os.getenv('AUTO_SCREEN_BLOCK', '65'))
IDENTITY_BOOTSTRAP_FRAMES = max(3, int(os.getenv('IDENTITY_BOOTSTRAP_FRAMES', '3')))
IDENTITY_SWITCH_FRAMES = max(3, int(os.getenv('IDENTITY_SWITCH_FRAMES', '3')))
IDENTITY_SWITCH_COOLDOWN_SECONDS = max(4.0, float(os.getenv('IDENTITY_SWITCH_COOLDOWN_SECONDS', '6')))


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
    return max(AUTO_IDENTITY_CONFIDENCE, 82.0) if candidate == 'Tomato' else AUTO_IDENTITY_CONFIDENCE


def _auto_origin(sample: FruitSample) -> bool:
    source = str(sample.source or '').strip().lower()
    return sample.sample_id.upper().startswith('AUT-') or source in {
        'auto', 'auto-camera', 'auto-camera-switch', 'auto-dashboard', 'automatic'
    }


def _recent_identity_votes(db: Session, sample_id: str, limit: int = 8) -> list[dict]:
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


def _identity_consensus(candidate: str, confidence: float, history: list[dict], required_frames: int) -> dict:
    window_size = max(5, required_frames + 2)
    window = [{'fruit': candidate, 'confidence': confidence}, *history][:window_size]
    counts = Counter(item['fruit'] for item in window)
    candidate_count = counts.get(candidate, 0)
    other_count = sum(value for key, value in counts.items() if key != candidate)
    matching = [item['confidence'] for item in window if item['fruit'] == candidate]
    average = sum(matching) / max(len(matching), 1)

    weighted_total = sum(max(0.05, float(item['confidence']) / 100.0) for item in window)
    weighted_candidate = sum(
        max(0.05, float(item['confidence']) / 100.0)
        for item in window if item['fruit'] == candidate
    )
    weighted_share = weighted_candidate / max(weighted_total, 1e-6)

    return {
        'stable': (
            candidate_count >= required_frames
            and candidate_count > other_count
            and weighted_share >= 0.58
        ),
        'candidate_frames': candidate_count,
        'required_frames': required_frames,
        'average_confidence': round(average, 1),
        'weighted_share_pct': round(weighted_share * 100.0, 1),
        'recent_votes': [item['fruit'] for item in window],
    }


def _seconds_since_identity_update(sample: FruitSample) -> float | None:
    updated = getattr(sample, 'updated_at', None)
    if not updated:
        return None
    try:
        return max(0.0, (datetime.utcnow() - updated).total_seconds())
    except Exception:
        return None


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
        'auto_origin': _auto_origin(sample),
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

    history = _recent_identity_votes(db, sample.sample_id, 8)

    if current in {'Apple', 'Banana', 'Tomato'}:
        if current == candidate:
            event['stable_identity'] = current
            return sample, event

        if not _auto_origin(sample):
            event['identity_conflict'] = True
            event['routing_blocked'] = 'operator_identity_locked'
            event['message'] = f'Inspection is locked to operator-selected {current}; current frame looks like {candidate}.'
            return sample, event

        correction = _identity_consensus(candidate, confidence, history, IDENTITY_SWITCH_FRAMES)
        event['identity_consensus'] = correction

        since_update = _seconds_since_identity_update(sample)
        if since_update is not None and since_update < IDENTITY_SWITCH_COOLDOWN_SECONDS:
            event['pending_correction'] = True
            event['identity_conflict'] = True
            event['routing_blocked'] = 'identity_switch_cooldown'
            event['message'] = (
                f'Current auto identity is {current}; checking {candidate} across more frames '
                f'before allowing another identity switch.'
            )
            return sample, event

        if not correction['stable'] or correction['average_confidence'] < max(70.0, threshold - 3.0):
            event['pending_correction'] = True
            event['identity_conflict'] = True
            event['message'] = (
                f'Current auto identity is {current}; {candidate} evidence is being checked '
                f"({correction['candidate_frames']}/{correction['required_frames']} consistent frames, "
                f"{correction['weighted_share_pct']}% weighted support)."
            )
            return sample, event

        previous = current
        sample.fruit_type = candidate
        sample.source = sample.source or 'auto-camera'
        db.add(sample)
        db.commit()
        db.refresh(sample)
        event.update({
            'identity_corrected': True,
            'previous_identity': previous,
            'stable_identity': candidate,
            'message': f'Auto identity corrected from {previous} to {candidate} after temporal consensus.',
        })
        return sample, event

    consensus = _identity_consensus(candidate, confidence, history, IDENTITY_BOOTSTRAP_FRAMES)
    event['identity_consensus'] = consensus

    if not consensus['stable']:
        event['pending_identity'] = True
        return sample, event

    sample.fruit_type = candidate
    sample.source = sample.source or 'auto-camera'
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

    # Preserve the raw per-frame classifier output for engineering diagnostics,
    # but publish the temporally stabilized inspection identity separately.
    analysis['identity_state'] = {
        'stable_fruit': sample.fruit_type if sample.fruit_type in {'Apple', 'Banana', 'Tomato'} else None,
        'raw_frame_fruit': (analysis.get('identity') or {}).get('fruit'),
        'raw_frame_confidence': (analysis.get('identity') or {}).get('confidence'),
        'pending_correction': bool(auto_event.get('pending_correction')),
        'identity_conflict': bool(auto_event.get('identity_conflict')),
        'consensus': auto_event.get('identity_consensus'),
    }

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
