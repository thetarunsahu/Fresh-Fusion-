from sqlalchemy.orm import Session
from ..models import FruitImage, FruitSample, FusionResult, SensorReading


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def compute_fusion(db: Session, sample: FruitSample) -> FusionResult:
    sensors = db.query(SensorReading).filter(SensorReading.sample_id == sample.sample_id).order_by(SensorReading.captured_at.desc()).limit(20).all()
    images = db.query(FruitImage).filter(FruitImage.sample_id == sample.sample_id).order_by(FruitImage.uploaded_at.desc()).all()

    sensor_score = None
    sensor_components = {}
    if sensors:
        def avg(name, fallback):
            vals = [getattr(x, name) for x in sensors if getattr(x, name) is not None]
            return sum(vals) / len(vals) if vals else fallback
        temperature = avg("temperature", 24.0)
        humidity = avg("humidity", 60.0)
        voc = avg("voc_index", None)
        gas_ppm = avg("gas_ppm", 0.0)
        temp_penalty = abs(temperature - 24.0) * 2.5
        humidity_penalty = abs(humidity - 60.0) * 0.65
        gas_signal = voc if voc is not None else (gas_ppm / 10.0)
        gas_penalty = min(42.0, max(0.0, gas_signal) * 0.45)
        sensor_score = _clamp(100.0 - temp_penalty - humidity_penalty - gas_penalty)
        sensor_components = {
            "temperature_penalty": round(temp_penalty, 2),
            "humidity_penalty": round(humidity_penalty, 2),
            "gas_penalty": round(gas_penalty, 2),
        }

    vision_score = None
    vision_components = {}
    valid_images = [i for i in images if i.analysis]
    if valid_images:
        healthy_values, brown_values, dark_values = [], [], []
        for image in valid_images:
            color = image.analysis.get("color", {})
            defects = image.analysis.get("defects", {})
            healthy_values.append(float(defects.get("healthy_surface_estimate_pct", 70.0)))
            brown_values.append(float(color.get("brown_pct", 0.0)))
            dark_values.append(float(color.get("dark_pct", 0.0)))
        healthy = sum(healthy_values) / len(healthy_values)
        brown = sum(brown_values) / len(brown_values)
        dark = sum(dark_values) / len(dark_values)
        coverage = min(1.0, len({i.angle for i in valid_images}) / 5.0)
        vision_score = _clamp(healthy - brown * 0.20 - dark * 0.35)
        vision_components = {"healthy_surface": round(healthy,2), "brown_pct": round(brown,2), "dark_pct": round(dark,2), "angles": len({i.angle for i in valid_images}), "coverage_pct": round(coverage*100,1)}

    available = [x for x in (sensor_score, vision_score) if x is not None]
    if not available:
        score = 50.0
        confidence = 0.15
    elif sensor_score is not None and vision_score is not None:
        score = sensor_score * 0.48 + vision_score * 0.52
        coverage = min(1.0, len({i.angle for i in valid_images}) / 5.0) if valid_images else 0.0
        confidence = 0.68 + coverage * 0.18
    else:
        score = available[0]
        confidence = 0.52

    if score >= 82:
        label, risk = "fresh", "low"
    elif score >= 62:
        label, risk = "ripe", "low-medium"
    elif score >= 38:
        label, risk = "overripe", "medium-high"
    else:
        label, risk = "spoiled-suspected", "high"

    result = FusionResult(
        sample_id=sample.sample_id,
        freshness_score=round(score, 2),
        sensor_score=round(sensor_score, 2) if sensor_score is not None else None,
        vision_score=round(vision_score, 2) if vision_score is not None else None,
        label=label,
        confidence=round(confidence * 100, 1),
        risk=risk,
        explanation="Experimental multimodal score combining recent sensor telemetry and multi-angle image-derived visual features. Calibrate weights against labelled fruit data before scientific use.",
        components={"sensor": sensor_components, "vision": vision_components},
    )
    sample.status = label
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
