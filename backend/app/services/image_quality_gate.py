from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

from ..config import UPLOAD_DIR

REQUIRED_VIEW_COUNT = 3


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


def _multiple_regions(image) -> int:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    candidate = ((sat > 32) & (val > 25)).astype(np.uint8) * 255
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8), iterations=1)
    contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame_area = max(float(image.shape[0] * image.shape[1]), 1.0)
    return sum(1 for contour in contours if 0.035 <= cv2.contourArea(contour) / frame_area <= 0.70)


def _frame_check(row) -> dict:
    analysis = row.analysis or {}
    quality = analysis.get("quality", {})
    segmentation = analysis.get("segmentation", {})
    texture = analysis.get("texture", {})
    path = UPLOAD_DIR / row.filename
    image = cv2.imread(str(path)) if path.exists() else None
    brightness = None
    blur_variance = texture.get("laplacian_variance")
    multiple_regions = None
    if image is not None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        if blur_variance is None:
            blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        multiple_regions = _multiple_regions(image)
    coverage = float(segmentation.get("coverage_pct", quality.get("coverage_pct", 0.0)) or 0.0)
    center_offset = float(segmentation.get("center_offset", quality.get("center_offset", 1.0)) or 1.0)
    too_dark = brightness is not None and brightness < 42
    too_bright = brightness is not None and brightness > 225
    blurry = blur_variance is not None and float(blur_variance) < 45
    badly_framed = coverage < 5 or coverage > 78 or center_offset > 0.58
    multiple_fruit_suspected = multiple_regions is not None and multiple_regions >= 2
    reasons = []
    if quality.get("fruit_present") is not True: reasons.append("No centered fruit detected")
    if blurry: reasons.append("Image appears blurred")
    if too_dark: reasons.append("Lighting is too dark")
    if too_bright: reasons.append("Lighting is overexposed")
    if badly_framed: reasons.append("Fruit framing is not suitable")
    if multiple_fruit_suspected: reasons.append("Multiple fruit-like regions may be present")
    return {
        "image_id": row.id,
        "view": _view_name(row.angle),
        "usable": not reasons,
        "blur_variance": round(float(blur_variance), 2) if blur_variance is not None else None,
        "brightness_mean": round(brightness, 1) if brightness is not None else None,
        "coverage_pct": round(coverage, 1),
        "center_offset": round(center_offset, 3),
        "multiple_regions": multiple_regions,
        "multiple_fruit_suspected": multiple_fruit_suspected,
        "reasons": reasons,
        "fingerprint": analysis.get("presentation", {}).get("fruit_fingerprint"),
    }


def evaluate_image_quality(images: list) -> dict:
    latest_by_view = {}
    for row in images:
        view = _view_name(row.angle)
        if view in {"front", "left", "right", "back", "top"} and view not in latest_by_view:
            latest_by_view[view] = row
    selected = list(latest_by_view.values())[:5]
    frames = [_frame_check(row) for row in selected]
    usable = [frame for frame in frames if frame["usable"]]
    duplicate_pairs = []
    for i in range(len(frames)):
        for j in range(i + 1, len(frames)):
            distance = _hamming_hex(frames[i].get("fingerprint"), frames[j].get("fingerprint"))
            if distance is not None and distance <= 3:
                duplicate_pairs.append([frames[i]["view"], frames[j]["view"]])
    issues = []
    if len(latest_by_view) < REQUIRED_VIEW_COUNT:
        issues.append(f"Need {REQUIRED_VIEW_COUNT - len(latest_by_view)} more distinct view(s)")
    if len(usable) < min(REQUIRED_VIEW_COUNT, len(frames)):
        issues.append("One or more captured views fail image-quality checks")
    if duplicate_pairs:
        issues.append("Two captured views look nearly identical; change viewpoint and recapture")
    if any(frame["multiple_fruit_suspected"] for frame in frames):
        issues.append("Multiple fruit-like regions detected; inspect one fruit at a time")
    blocking = bool(issues)
    return {
        "blocking": blocking,
        "status": "ready" if not blocking and len(usable) >= REQUIRED_VIEW_COUNT else "needs_attention",
        "required_views": REQUIRED_VIEW_COUNT,
        "captured_views": sorted(latest_by_view),
        "usable_views": [frame["view"] for frame in usable],
        "duplicate_pairs": duplicate_pairs,
        "frames": frames,
        "issues": issues,
        "note": "Blur, lighting, framing, duplicate-view and multiple-region checks are operational image-quality gates, not biological freshness measurements.",
    }
