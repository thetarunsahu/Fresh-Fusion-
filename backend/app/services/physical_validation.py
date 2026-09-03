from __future__ import annotations

from datetime import datetime
from statistics import median

from sqlalchemy.orm import Session

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


def evaluate_physical_evidence(
    db: Session,
    sample: FruitSample,
    images: list[FruitImage] | None = None,
    sensors: list[SensorReading] | None = None,
) -> dict:
    """Estimate whether current evidence is consistent with a real 3D fruit.

    This is a gate, not a guaranteed anti-spoof claim. A monocular browser camera
    cannot prove physical liveness from one frame. FreshFusion combines display-
    artifact suspicion, repeated identity, multiple labelled viewpoints and
    appearance change across the fruit crop. Final multimodal verdicts also
    require recent ESP32 telemetry.
    """

    if images is None:
        images = (
            db.query(FruitImage)
            .filter(FruitImage.sample_id == sample.sample_id)
            .order_by(FruitImage.uploaded_at.desc())
            .limit(24)
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
            "screen_suspicion_pct": 0.0,
            "appearance_diversity_pct": 0.0,
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

    hashes = [
        (row.analysis or {}).get("presentation", {}).get("fruit_fingerprint")
        for row in selected
    ]
    hashes = [value for value in hashes if value]
    distances: list[int] = []
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            value = _hamming_hex(hashes[i], hashes[j])
            if value is not None:
                distances.append(value)
    diversity = (median(distances) / 64.0 * 100.0) if distances else 0.0

    enough_frames = len(usable) >= 4
    enough_views = len(views) >= 3
    screen_suspected = screen_avg >= 52.0 or screen_peak >= 78.0
    repeated_flat_reference = enough_views and len(hashes) >= 3 and diversity < 7.0
    identity_stable = identity_consistency >= 0.66

    if screen_suspected:
        status = "suspected_2d_display"
        physical_likely = False
        confidence = min(98.0, 55.0 + max(screen_avg, screen_peak) * 0.4)
        message = "A screen/photo presentation is suspected from strong rectangular/display artifacts. Freshness verdict is blocked. Scan the physical fruit directly."
    elif repeated_flat_reference:
        status = "suspected_flat_reference"
        physical_likely = False
        confidence = 72.0
        message = "The fruit appearance changes too little across different labelled views. This can happen when the camera is pointed at the same flat photo. Move around a real fruit and capture at least three genuine viewpoints."
    elif enough_frames and enough_views and identity_stable and (diversity >= 9.0 or len(views) >= 4):
        status = "physical_fruit_likely"
        physical_likely = True
        confidence = min(96.0, 58.0 + len(views) * 7.0 + min(18.0, diversity * 0.55) - screen_avg * 0.12)
        message = "Multi-view evidence is consistent with a physical 3D fruit. This is a probabilistic browser-camera check, not a depth-sensor proof."
    else:
        status = "collecting_physical_evidence"
        physical_likely = False
        confidence = min(65.0, 12.0 + len(views) * 11.0 + min(15.0, diversity * 0.35))
        missing = max(0, 3 - len(views))
        message = (
            f"Collect {missing} more distinct viewpoint{'s' if missing != 1 else ''} of the real fruit. Use Front, Left/Right and Back/Top while physically moving around the fruit."
            if missing
            else "Keep moving around the real fruit so FreshFusion can verify 3D appearance change."
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
        "identity_consistency_pct": round(identity_consistency * 100.0, 1),
        "sensor_present": sensor_present,
        "sensor_freshness_window_seconds": 45,
        "message": message,
        "note": "Monocular anti-spoofing is probabilistic. Stronger production verification would use depth/stereo/NIR or a controlled mechanical multi-view rig.",
    }
