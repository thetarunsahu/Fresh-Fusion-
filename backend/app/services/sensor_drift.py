from __future__ import annotations

from statistics import median

from ..models import SensorReading
from .sensor_assessment import measurement_phase, sensor_source, valid_measurements


def assess_historical_drift(db, sample_id: str, sensor_evidence: dict) -> dict:
    latest = sensor_evidence.get("latest") or {}
    device_id = latest.get("device_id")
    current_baseline = (sensor_evidence.get("baseline") or {}).get("mq135_raw_mean")
    if not device_id or current_baseline is None:
        return {"checked": False, "suspected": False, "reason": "Current device and stable baseline are required."}

    rows = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device_id, SensorReading.sample_id != sample_id)
        .order_by(SensorReading.captured_at.desc())
        .limit(800)
        .all()
    )
    sessions = {}
    for row in rows:
        if sensor_source(row) != "hardware" or measurement_phase(row) != "baseline" or not valid_measurements(row):
            continue
        sessions.setdefault(row.sample_id, []).append(float(row.mq135_raw))
    session_means = [sum(values) / len(values) for values in sessions.values() if len(values) >= 3]
    if len(session_means) < 2:
        return {"checked": False, "suspected": False, "historical_sessions": len(session_means), "reason": "Need at least two prior baseline sessions for drift comparison."}

    reference = float(median(session_means))
    delta = float(current_baseline) - reference
    delta_pct = (delta / reference * 100.0) if reference else None
    threshold = max(80.0, abs(reference) * 0.15)
    suspected = abs(delta) > threshold
    return {
        "checked": True,
        "suspected": suspected,
        "historical_sessions": len(session_means),
        "historical_baseline_median": round(reference, 2),
        "current_baseline_mean": round(float(current_baseline), 2),
        "delta_raw": round(delta, 2),
        "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
        "threshold_raw": round(threshold, 2),
        "reason": "Current empty-chamber baseline differs materially from prior sessions." if suspected else "Current baseline is within the operational historical drift band.",
        "note": "This is an operational drift warning, not a laboratory calibration certificate.",
    }
