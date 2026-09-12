"""Empirical calibration summaries from FreshFusion's own labelled inspections.

This module never invents universal thresholds. It summarizes observed
FreshFusion chamber data only when human ground truth exists. The summaries are
for calibration work and do not automatically change the production verdict.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from sqlalchemy.orm import Session

from ..models import FruitImage, FruitSample, HumanVerification, SensorReading
from .sensor_assessment import assess_sensors
from .validation_metrics import normalize_label

MIN_CLASS_SAMPLES = 5


def _quartiles(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return None
    n = len(values)
    def at(frac):
        idx = (n - 1) * frac
        lo = int(idx)
        hi = min(n - 1, lo + 1)
        part = idx - lo
        return values[lo] * (1 - part) + values[hi] * part
    return {
        "min": round(values[0], 2),
        "q1": round(at(0.25), 2),
        "median": round(median(values), 2),
        "q3": round(at(0.75), 2),
        "max": round(values[-1], 2),
    }


def calibration_summary(db: Session):
    reviews = (
        db.query(HumanVerification)
        .filter(HumanVerification.ground_truth.isnot(None))
        .order_by(HumanVerification.created_at.desc(), HumanVerification.id.desc())
        .all()
    )
    latest = {}
    for row in reviews:
        if row.sample_id not in latest and normalize_label(row.ground_truth):
            latest[row.sample_id] = row

    samples = {row.sample_id: row for row in db.query(FruitSample).all()}
    grouped = defaultdict(lambda: defaultdict(list))
    usable_records = 0

    for sample_id, review in latest.items():
        sample = samples.get(sample_id)
        if not sample:
            continue
        label = normalize_label(review.ground_truth)
        fruit = str(sample.fruit_type or "Unknown").title()
        sensors = (
            db.query(SensorReading)
            .filter(SensorReading.sample_id == sample_id)
            .order_by(SensorReading.captured_at.desc())
            .limit(40)
            .all()
        )
        sensor = assess_sensors(sensors)
        image = (
            db.query(FruitImage)
            .filter(FruitImage.sample_id == sample_id)
            .order_by(FruitImage.uploaded_at.desc())
            .first()
        )
        analysis = (image.analysis or {}) if image else {}
        defects = analysis.get("defects") or {}
        color = analysis.get("color") or {}
        latest_sensor = sensor.get("latest") or {}
        record = {
            "sample_id": sample_id,
            "mq135_baseline_delta_raw": sensor.get("baseline_delta_raw"),
            "temperature": latest_sensor.get("temperature"),
            "humidity": latest_sensor.get("humidity"),
            "visible_damage_pct": defects.get("visible_damage_estimate_pct"),
            "brown_pct": color.get("brown_pct"),
            "dark_pct": color.get("dark_pct"),
        }
        grouped[fruit][label].append(record)
        usable_records += 1

    output = {}
    for fruit, classes in grouped.items():
        output[fruit] = {}
        for label, rows in classes.items():
            output[fruit][label] = {
                "samples": len(rows),
                "ready_for_band_estimation": len(rows) >= MIN_CLASS_SAMPLES,
                "mq135_baseline_delta_raw": _quartiles([r["mq135_baseline_delta_raw"] for r in rows]),
                "temperature": _quartiles([r["temperature"] for r in rows]),
                "humidity": _quartiles([r["humidity"] for r in rows]),
                "visible_damage_pct": _quartiles([r["visible_damage_pct"] for r in rows]),
                "brown_pct": _quartiles([r["brown_pct"] for r in rows]),
                "dark_pct": _quartiles([r["dark_pct"] for r in rows]),
            }

    required = ["fresh", "ripe", "overripe", "spoiled"]
    fruit_readiness = {}
    for fruit in ("Apple", "Banana", "Tomato"):
        classes = output.get(fruit, {})
        fruit_readiness[fruit] = {
            "ready": all((classes.get(label) or {}).get("samples", 0) >= MIN_CLASS_SAMPLES for label in required),
            "class_counts": {label: (classes.get(label) or {}).get("samples", 0) for label in required},
        }

    return {
        "status": "DATA AVAILABLE" if usable_records else "NO LABELLED CALIBRATION DATA",
        "minimum_samples_per_class": MIN_CLASS_SAMPLES,
        "records": usable_records,
        "fruit_readiness": fruit_readiness,
        "distributions": output,
        "note": "Observed ranges come only from FreshFusion's own chamber measurements paired with human labels. They are not universal fruit standards and are not activated as decision thresholds automatically.",
    }
