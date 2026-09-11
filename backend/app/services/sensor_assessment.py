"""DHT11 + 12-bit MQ135 evidence assessment.

The MQ135 signal is treated as an uncalibrated electrical response. FreshFusion
can record an empty-chamber baseline and compare later fruit readings against it,
but neither the delta nor the experimental sensor score is a gas concentration,
food-safety measurement, or validated shelf-life estimate.
"""
from datetime import datetime, timezone
from math import isfinite
import os

SENSOR_MAX_AGE = 45
ADC_MAX = 4095.0  # 2**12 - 1; firmware explicitly selects 12-bit ADC resolution.
# Prototype readiness gate only. This is configurable because MQ135 warm-up and
# burn-in depend on the actual module and operating protocol; it is not a
# calibration constant.
SENSOR_WARMUP_SECONDS = max(0, int(os.getenv("MQ135_WARMUP_SECONDS", "120")))
BASELINE_PHASES = {"baseline", "empty", "empty_chamber", "clean_air"}
FRUIT_PHASES = {"fruit", "sample", "measurement", "inspect", "inspection"}

GAS_NOTE = (
    "MQ135 is used as a raw/relative 12-bit electrical response, not calibrated ppm. "
    "When an empty-chamber baseline is explicitly recorded, FreshFusion reports the "
    "raw delta from that local baseline. Baseline delta, trend and the experimental "
    "42-point gas penalty are not universal fruit standards and must be calibrated "
    "with the FreshFusion labelled dataset before scientific or shelf-life claims."
)


def utc_iso(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.astimezone(timezone.utc).isoformat()


def age_seconds(value):
    if value is None:
        return float("inf")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - value).total_seconds()


def sensor_source(row):
    if str(row.device_id or "").upper().startswith(("SIM", "TEST")):
        return "simulator"
    return (row.extra_metrics or {}).get("source", "hardware")


def measurement_phase(row):
    extra = row.extra_metrics or {}
    phase = str(extra.get("measurement_phase") or extra.get("phase") or "fruit").strip().lower()
    if phase in BASELINE_PHASES:
        return "baseline"
    if phase in FRUIT_PHASES:
        return "fruit"
    return phase or "fruit"


def valid_measurements(row):
    return all(
        value is not None and isfinite(value) and low <= value <= high
        for value, low, high in [
            (row.temperature, 0, 50),
            (row.humidity, 0, 100),
            (row.mq135_raw, 0, ADC_MAX),
        ]
    )


def warmup_state(row):
    if row is None or row.uptime_ms is None:
        return {"state": "unknown", "ready": None, "uptime_seconds": None, "required_seconds": SENSOR_WARMUP_SECONDS}
    uptime_seconds = max(0.0, float(row.uptime_ms) / 1000.0)
    ready = uptime_seconds >= SENSOR_WARMUP_SECONDS
    return {
        "state": "ready" if ready else "warming",
        "ready": ready,
        "uptime_seconds": round(uptime_seconds, 1),
        "required_seconds": SENSOR_WARMUP_SECONDS,
    }


def _hardware_valid(rows):
    return [row for row in rows if sensor_source(row) == "hardware" and valid_measurements(row)]


def eligible_sensors(rows):
    eligible = []
    for row in rows:
        if sensor_source(row) != "hardware" or measurement_phase(row) == "baseline" or not valid_measurements(row):
            continue
        if not (-5 <= age_seconds(row.captured_at) <= SENSOR_MAX_AGE):
            continue
        warmup = warmup_state(row)
        if warmup["ready"] is False:
            continue
        eligible.append(row)
    return eligible


def _mean(rows, name):
    return sum(float(getattr(row, name)) for row in rows) / len(rows)


def _baseline_summary(rows):
    baseline_rows = [row for row in _hardware_valid(rows) if measurement_phase(row) == "baseline"]
    if not baseline_rows:
        return {
            "available": False,
            "count": 0,
            "mq135_raw_mean": None,
            "mq135_raw_min": None,
            "mq135_raw_max": None,
            "spread": None,
            "stable": None,
            "captured_at": None,
        }
    values = [float(row.mq135_raw) for row in baseline_rows]
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    # Operational stability check only; not a sensor-accuracy specification.
    allowed_spread = max(50.0, mean * 0.08)
    newest = max(baseline_rows, key=lambda row: row.captured_at or datetime.min)
    return {
        "available": True,
        "count": len(values),
        "mq135_raw_mean": round(mean, 2),
        "mq135_raw_min": round(min(values), 2),
        "mq135_raw_max": round(max(values), 2),
        "spread": round(spread, 2),
        "stable": spread <= allowed_spread if len(values) >= 3 else None,
        "captured_at": utc_iso(newest.captured_at),
    }


def _trend_summary(rows):
    fruit_rows = [row for row in _hardware_valid(rows) if measurement_phase(row) != "baseline"]
    fruit_rows = sorted(
        [row for row in fruit_rows if row.captured_at is not None],
        key=lambda row: row.captured_at,
    )[-12:]
    if len(fruit_rows) < 3:
        return {"available": False, "direction": "insufficient_data", "delta_raw": None, "raw_per_minute": None, "readings": len(fruit_rows)}
    first, last = fruit_rows[0], fruit_rows[-1]
    t0 = first.captured_at.replace(tzinfo=timezone.utc) if first.captured_at.tzinfo is None else first.captured_at.astimezone(timezone.utc)
    t1 = last.captured_at.replace(tzinfo=timezone.utc) if last.captured_at.tzinfo is None else last.captured_at.astimezone(timezone.utc)
    minutes = max((t1 - t0).total_seconds() / 60.0, 1 / 60)
    delta = float(last.mq135_raw) - float(first.mq135_raw)
    rate = delta / minutes
    # Neutral band prevents tiny ADC noise from being described as a meaningful change.
    if abs(rate) < 5:
        direction = "stable"
    else:
        direction = "rising" if rate > 0 else "falling"
    return {
        "available": True,
        "direction": direction,
        "delta_raw": round(delta, 2),
        "raw_per_minute": round(rate, 2),
        "readings": len(fruit_rows),
        "window_seconds": round(minutes * 60, 1),
    }


def _stuck_signal(rows):
    recent = [row for row in _hardware_valid(rows) if measurement_phase(row) != "baseline"]
    recent = sorted(
        [row for row in recent if row.captured_at is not None],
        key=lambda row: row.captured_at,
    )[-5:]
    if len(recent) < 5:
        return {"checked": False, "suspected": False, "spread": None}
    values = [float(row.mq135_raw) for row in recent]
    spread = max(values) - min(values)
    duration = (recent[-1].captured_at - recent[0].captured_at).total_seconds()
    suspected = duration >= 8 and spread <= 2.0
    return {"checked": True, "suspected": suspected, "spread": round(spread, 2)}


def _evidence_quality(*, latest, baseline, stuck, eligible_count):
    problems = []
    if latest is None:
        return {"level": "weak", "reasons": ["No sensor reading available."]}
    if age_seconds(latest.captured_at) > SENSOR_MAX_AGE:
        problems.append("Sensor reading is stale.")
    if sensor_source(latest) != "hardware":
        problems.append("Latest reading is simulator data.")
    warmup = warmup_state(latest)
    if warmup["ready"] is False:
        problems.append("Sensor warm-up gate is not complete.")
    if stuck.get("suspected"):
        problems.append("MQ135 signal appears unusually flat across recent readings.")
    if baseline.get("stable") is False:
        problems.append("Empty-chamber baseline is unstable.")
    if eligible_count == 0:
        problems.append("No recent eligible hardware reading is available.")
    if problems:
        return {"level": "weak", "reasons": problems}
    if not baseline.get("available") or baseline.get("stable") is None:
        return {"level": "moderate", "reasons": ["Sensor evidence is usable, but a stable empty-chamber baseline has not yet been established."]}
    return {"level": "strong", "reasons": ["Recent hardware telemetry and an operationally stable baseline are available."]}


def serialize_sensor(row):
    return {
        "id": row.id,
        "sample_id": row.sample_id,
        "device_id": row.device_id,
        "source": sensor_source(row),
        "measurement_phase": measurement_phase(row),
        "temperature": row.temperature,
        "humidity": row.humidity,
        "mq135_raw": row.mq135_raw,
        "relative_gas_response": round(row.mq135_raw / ADC_MAX, 4) if valid_measurements(row) else None,
        "gas_ppm": row.gas_ppm,
        "voc_index": row.voc_index,
        "rssi": row.rssi,
        "uptime_ms": row.uptime_ms,
        "warmup": warmup_state(row),
        "extra_metrics": row.extra_metrics or {},
        "captured_at": utc_iso(row.captured_at),
    }


def assess_sensors(rows):
    eligible = eligible_sensors(rows)
    latest = rows[0] if rows else None
    latest_age = age_seconds(latest.captured_at) if latest else None
    baseline = _baseline_summary(rows)
    trend = _trend_summary(rows)
    stuck = _stuck_signal(rows)
    latest_serialized = serialize_sensor(latest) if latest else None

    baseline_delta = None
    baseline_delta_pct = None
    if latest and baseline["available"] and valid_measurements(latest) and measurement_phase(latest) != "baseline":
        baseline_delta = float(latest.mq135_raw) - float(baseline["mq135_raw_mean"])
        if baseline["mq135_raw_mean"]:
            baseline_delta_pct = baseline_delta / float(baseline["mq135_raw_mean"]) * 100

    quality = _evidence_quality(
        latest=latest,
        baseline=baseline,
        stuck=stuck,
        eligible_count=len(eligible),
    )

    result = {
        "latest": latest_serialized,
        "physical_present": bool(eligible),
        "eligible_readings": len(eligible),
        "age_seconds": round(latest_age, 1) if latest_age is not None and isfinite(latest_age) else None,
        "freshness_window_seconds": SENSOR_MAX_AGE,
        "warmup": warmup_state(latest),
        "health": {
            "stuck_signal": stuck,
            "baseline_stable": baseline.get("stable"),
            "evidence_quality": quality,
        },
        "baseline": baseline,
        "baseline_delta_raw": round(baseline_delta, 2) if baseline_delta is not None else None,
        "baseline_delta_pct": round(baseline_delta_pct, 2) if baseline_delta_pct is not None else None,
        "trend": trend,
        "score": None,
        "components": {},
        "note": GAS_NOTE,
    }

    if eligible:
        raw = _mean(eligible, "mq135_raw")
        components = {
            "temperature_penalty": abs(_mean(eligible, "temperature") - 24) * 2.5,
            "humidity_penalty": abs(_mean(eligible, "humidity") - 60) * 0.65,
            "gas_penalty": raw / ADC_MAX * 42,
            "relative_gas_response": raw / ADC_MAX,
            "mq135_raw_mean": raw,
        }
        result["score"] = round(
            max(
                0,
                min(
                    100,
                    100
                    - sum(
                        components[key]
                        for key in ("temperature_penalty", "humidity_penalty", "gas_penalty")
                    ),
                ),
            ),
            2,
        )
        result["components"] = {key: round(value, 4) for key, value in components.items()}
        result["components"]["gas_note"] = GAS_NOTE

    return result
