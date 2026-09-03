from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import median

import cv2
import numpy as np
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..models import FruitImage, FruitSample, SensorReading

VIEWS = {"front", "back", "left", "right", "top"}


def _view_name(angle: str) -> str:
    value = (angle or "unknown").lower()
    return value[5:] if value.startswith("live-") else value


def _hamming_hex(a: str | None, b: str | None) -> int | None:
    if not a or not b:
        return None
    try:
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except Exception:
        return None


def _recent_sensor_present(sensors: list[SensorReading], max_age_seconds: float = 45.0) -> bool:
    if not sensors:
        return False
    newest = max((row.captured_at for row in sensors if row.captured_at is not None), default=None)
    if newest is None:
        return False
    try:
        age = (datetime.utcnow() - newest).total_seconds()
        return -5.0 <= age <= max_age_seconds
    except Exception:
        return True


def _artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = UPLOAD_DIR / Path(str(value)).name
    return path if path.exists() else None


def _fruit_crop(row: FruitImage) -> np.ndarray | None:
    image_path = UPLOAD_DIR / row.filename
    if not image_path.exists():
        return None
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None

    mask_path = _artifact_path((row.analysis or {}).get("artifacts", {}).get("mask"))
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) if mask_path else None
    if mask is None or mask.shape != image.shape:
        mask = np.ones_like(image, dtype=np.uint8) * 255

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    pad_x = max(3, int(w * 0.06))
    pad_y = max(3, int(h * 0.06))
    x0, y0 = max(0, x - pad_x), max(0, y - pad_y)
    x1, y1 = min(image.shape[1], x + w + pad_x), min(image.shape[0], y + h + pad_y)
    crop = image[y0:y1, x0:x1].copy()
    crop_mask = mask[y0:y1, x0:x1]
    if crop.size == 0:
        return None

    selected = crop[crop_mask > 0]
    fill = int(np.median(selected)) if selected.size else int(np.median(crop))
    crop[crop_mask == 0] = fill

    scale = min(1.0, 520.0 / max(crop.shape))
    if scale < 1.0:
        crop = cv2.resize(
            crop,
            (max(1, int(crop.shape[1] * scale)), max(1, int(crop.shape[0] * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return crop


def _planar_pair_score(a: FruitImage, b: FruitImage) -> float | None:
    first = _fruit_crop(a)
    second = _fruit_crop(b)
    if first is None or second is None:
        return None

    orb = cv2.ORB_create(nfeatures=900, fastThreshold=8, edgeThreshold=15)
    kp1, des1 = orb.detectAndCompute(first, None)
    kp2, des2 = orb.detectAndCompute(second, None)
    if des1 is None or des2 is None or len(kp1) < 14 or len(kp2) < 14:
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(des1, des2, k=2)
    good = []
    for pair in pairs:
        if len(pair) != 2:
            continue
        m, n = pair
        if m.distance < 0.74 * n.distance:
            good.append(m)
    if len(good) < 12:
        return None

    src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    _homography, inliers = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    if inliers is None:
        return None
    inlier_ratio = float(inliers.ravel().sum()) / max(len(good), 1)
    support = min(1.0, len(good) / 45.0)
    return round(max(0.0, min(100.0, inlier_ratio * (0.72 + 0.28 * support) * 100.0)), 1)


def evaluate_physical_evidence(
    db: Session,
    sample: FruitSample,
    images: list[FruitImage] | None = None,
    sensors: list[SensorReading] | None = None,
) -> dict:
    """Estimate whether current evidence is consistent with a real 3D fruit.

    This is a gate, not a guaranteed anti-spoof claim. FreshFusion combines
    display-artifact suspicion, multi-view appearance diversity, planar
    homography consistency, identity consistency and recent ESP32 telemetry.
    """

    if images is None:
        images = (
            db.query(FruitImage)
            .filter(FruitImage.sample_id == sample.sample_id)
            .order_by(FruitImage.uploaded_at.desc())
            .limit(30)
            .all()
        )
    if sensors is None:
        sensors = (
            db.query(SensorReading)
            .filter(SensorReading.sample_id == sample.sample_id)
            .order_by(SensorReading.captured_at.desc())
            .limit(20)
            .all()
        )

    sensor_present = _recent_sensor_present(sensors)
    expected = (sample.fruit_type or "").strip().lower()
    usable: list[FruitImage] = []
    for row in images:
        analysis = row.analysis or {}
        if analysis.get("quality", {}).get("fruit_present") is not True:
            continue
        identity = analysis.get("identity", {})
        detected = str(identity.get("fruit") or "Unknown").lower()
        confidence = float(identity.get("confidence") or 0.0)
        if expected in {"apple", "banana"} and detected not in {"unknown", "", expected} and confidence >= 58.0:
            continue
        usable.append(row)

    if not usable:
        return {
            "status": "no_fruit",
            "physical_likely": False,
            "vision_verified": False,
            "verdict_ready": False,
            "confidence": 0.0,
            "frames": 0,
            "views": [],
            "views_count": 0,
            "required_views": 3,
            "screen_suspicion_pct": 0.0,
            "appearance_diversity_pct": 0.0,
            "planar_consistency_pct": 0.0,
            "identity_consistency_pct": 0.0,
            "sensor_present": sensor_present,
            "message": "Place one real fruit inside the camera guide before FreshFusion can verify physical evidence.",
        }

    latest_by_view: dict[str, FruitImage] = {}
    for row in usable:
        view = _view_name(row.angle)
        if view in VIEWS and view not in latest_by_view:
            latest_by_view[view] = row

    selected = list(latest_by_view.values()) or usable[:5]
    views = sorted(latest_by_view)

    screen_scores = [
        float((row.analysis or {}).get("presentation", {}).get("screen_suspicion_pct") or 0.0)
        for row in selected
    ]
    screen_avg = sum(screen_scores) / max(len(screen_scores), 1)
    screen_peak = max(screen_scores) if screen_scores else 0.0

    identities = []
    for row in selected:
        identity = (row.analysis or {}).get("identity", {})
        fruit = str(identity.get("fruit") or "Unknown")
        if fruit != "Unknown" and float(identity.get("confidence") or 0.0) >= 58.0:
            identities.append(fruit)
    identity_consistency = 0.0
    if identities:
        majority = max(set(identities), key=identities.count)
        identity_consistency = identities.count(majority) / len(identities)

    hashes = [(row.analysis or {}).get("presentation", {}).get("fruit_fingerprint") for row in selected]
    hashes = [value for value in hashes if value]
    distances: list[int] = []
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            value = _hamming_hex(hashes[i], hashes[j])
            if value is not None:
                distances.append(value)
    diversity = (median(distances) / 64.0 * 100.0) if distances else 0.0

    selected_views = list(latest_by_view.values())
    planar_scores: list[float] = []
    for i in range(len(selected_views)):
        for j in range(i + 1, len(selected_views)):
            score = _planar_pair_score(selected_views[i], selected_views[j])
            if score is not None:
                planar_scores.append(score)
    planar_consistency = float(median(planar_scores)) if planar_scores else 0.0
    planar_peak = max(planar_scores) if planar_scores else 0.0

    enough_frames = len(usable) >= 4
    enough_views = len(views) >= 3
    identity_stable = identity_consistency >= 0.66

    strong_single_frame_screen = screen_avg >= 55.0 or screen_peak >= 82.0
    screen_plus_planar = screen_avg >= 35.0 and planar_consistency >= 64.0 and len(planar_scores) >= 1
    screen_suspected = strong_single_frame_screen or screen_plus_planar
    repeated_flat_reference = enough_views and (
        (len(planar_scores) >= 2 and planar_consistency >= 72.0)
        or (diversity < 7.0 and len(planar_scores) >= 1 and planar_peak >= 58.0)
    )

    if screen_suspected:
        status = "suspected_2d_display"
        physical_likely = False
        confidence = min(98.0, 58.0 + max(screen_avg, screen_peak) * 0.30 + planar_consistency * 0.16)
        message = "A screen/display presentation is suspected from rectangular UI/display artifacts and/or planar viewpoint consistency. Freshness verdict is blocked. Scan the physical fruit directly."
    elif repeated_flat_reference:
        status = "suspected_flat_reference"
        physical_likely = False
        confidence = min(96.0, 68.0 + planar_consistency * 0.30)
        message = "Different labelled views are still well explained by a flat planar image. This is consistent with a printed photo or screen image. Scan a real 3D fruit and move around it."
    elif enough_frames and enough_views and identity_stable and (
        diversity >= 8.0 or (planar_scores and planar_consistency < 50.0) or len(views) >= 4
    ):
        status = "physical_fruit_likely"
        physical_likely = True
        confidence = min(
            96.0,
            58.0 + len(views) * 6.5 + min(17.0, diversity * 0.55) + min(8.0, max(0.0, 55.0 - planar_consistency) * 0.16) - screen_avg * 0.10,
        )
        message = "Multi-view evidence is consistent with a physical 3D fruit. This is a probabilistic monocular check, not a depth-sensor proof."
    else:
        status = "collecting_physical_evidence"
        physical_likely = False
        confidence = min(67.0, 12.0 + len(views) * 11.0 + min(15.0, diversity * 0.35))
        missing = max(0, 3 - len(views))
        message = (
            f"Collect {missing} more distinct viewpoint{'s' if missing != 1 else ''} of the real fruit. Use Front, Left/Right and Back/Top while physically moving around the fruit."
            if missing
            else "Keep moving around the real fruit so FreshFusion can verify non-planar 3D appearance change."
        )

    vision_verified = physical_likely
    verdict_ready = physical_likely and sensor_present
    if physical_likely and not sensor_present:
        message += " Physical vision is verified; final multimodal verdict is waiting for recent ESP32 telemetry."

    return {
        "status": status,
        "physical_likely": physical_likely,
        "vision_verified": vision_verified,
        "verdict_ready": verdict_ready,
        "confidence": round(max(0.0, min(100.0, confidence)), 1),
        "frames": len(usable),
        "views": views,
        "views_count": len(views),
        "required_views": 3,
        "screen_suspicion_pct": round(screen_avg, 1),
        "screen_suspicion_peak_pct": round(screen_peak, 1),
        "appearance_diversity_pct": round(diversity, 1),
        "planar_consistency_pct": round(planar_consistency, 1),
        "planar_pairs": len(planar_scores),
        "identity_consistency_pct": round(identity_consistency * 100.0, 1),
        "sensor_present": sensor_present,
        "sensor_freshness_window_seconds": 45,
        "message": message,
        "note": "Monocular anti-spoofing is probabilistic. Stronger production verification would use depth/stereo/NIR or a controlled mechanical multi-view rig.",
    }
