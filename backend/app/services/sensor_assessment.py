"""Current DHT11 + 12-bit MQ135 electrical evidence; no ppm calibration."""
from datetime import datetime, timezone
from math import isfinite

SENSOR_MAX_AGE = 45
ADC_MAX = 4095.0  # 2**12 - 1; firmware explicitly selects 12-bit ADC resolution.
GAS_NOTE = (
    "MQ135 ADC fraction = raw / 4095 (12-bit electrical range), not calibrated ppm. "
    "Its contribution uses the existing experimental 42-point gas penalty cap; "
    "neither that weight nor freshness thresholds are empirically calibrated. "
    "No clean-air baseline, concentration or sensor accuracy is inferred."
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

def valid_measurements(row):
    return all(
        value is not None and isfinite(value) and low <= value <= high
        for value, low, high in [(row.temperature, 0, 50), (row.humidity, 0, 100), (row.mq135_raw, 0, ADC_MAX)]
    )

def eligible_sensors(rows):
    return [row for row in rows if sensor_source(row) == "hardware" and valid_measurements(row)
            and -5 <= age_seconds(row.captured_at) <= SENSOR_MAX_AGE]

def serialize_sensor(row):
    return {"id": row.id, "sample_id": row.sample_id, "device_id": row.device_id,
            "source": sensor_source(row), "temperature": row.temperature, "humidity": row.humidity,
            "mq135_raw": row.mq135_raw, "relative_gas_response": round(row.mq135_raw / ADC_MAX, 4) if valid_measurements(row) else None,
            "gas_ppm": row.gas_ppm, "voc_index": row.voc_index, "rssi": row.rssi,
            "captured_at": utc_iso(row.captured_at)}

def assess_sensors(rows):
    eligible = eligible_sensors(rows)
    latest = rows[0] if rows else None
    latest_age = age_seconds(latest.captured_at) if latest else None
    result = {"latest": serialize_sensor(latest) if latest else None, "physical_present": bool(eligible),
              "eligible_readings": len(eligible), "age_seconds": round(latest_age, 1) if latest_age is not None and isfinite(latest_age) else None,
              "freshness_window_seconds": SENSOR_MAX_AGE, "score": None, "components": {}, "note": GAS_NOTE}
    if eligible:
        mean = lambda name: sum(getattr(row, name) for row in eligible) / len(eligible)
        raw = mean("mq135_raw")
        components = {"temperature_penalty": abs(mean("temperature") - 24) * 2.5,
                      "humidity_penalty": abs(mean("humidity") - 60) * .65,
                      "gas_penalty": raw / ADC_MAX * 42,
                      "relative_gas_response": raw / ADC_MAX, "mq135_raw_mean": raw}
        result["score"] = round(max(0, min(100, 100 - sum(components[k] for k in ("temperature_penalty", "humidity_penalty", "gas_penalty")))), 2)
        result["components"] = {key: round(value, 4) for key, value in components.items()}
        result["components"]["gas_note"] = GAS_NOTE
    return result
