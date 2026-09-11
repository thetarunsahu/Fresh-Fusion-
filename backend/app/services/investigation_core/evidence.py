from ...models import FruitImage, SensorReading, FusionResult, HumanVerification, InspectionEvent
from ..sensor_assessment import assess_sensors, utc_iso, age_seconds, sensor_source
from ..datasets import reference_index_status

def sample_info(sample):
    return {"sample_id": sample.sample_id, "fruit_type": sample.fruit_type, "variety": sample.variety,
            "status": sample.status, "created_at": utc_iso(sample.created_at)}

def verification_info(row):
    return {"id": row.id, "action": row.action, "ground_truth": row.ground_truth,
            "reviewer": row.reviewer, "notes": row.notes, "assessment": row.assessment, "created_at": utc_iso(row.created_at)}

def collect_evidence(db, sample, fusion):
    images = db.query(FruitImage).filter_by(sample_id=sample.sample_id).order_by(FruitImage.uploaded_at.desc()).all()
    sensors = db.query(SensorReading).filter_by(sample_id=sample.sample_id).order_by(SensorReading.captured_at.desc()).limit(200).all()
    results = db.query(FusionResult).filter_by(sample_id=sample.sample_id).order_by(FusionResult.created_at.desc()).limit(100).all()
    reviews = db.query(HumanVerification).filter_by(sample_id=sample.sample_id).order_by(HumanVerification.created_at.desc()).all()
    assistant_events = db.query(InspectionEvent).filter_by(sample_id=sample.sample_id).order_by(InspectionEvent.created_at.desc()).limit(100).all()
    image = images[0] if images else None
    analysis = (image.analysis or {}) if image else {}
    evidence = {
        "camera": {"frames": len(images), "latest_image_id": image.id if image else None,
                   "latest_at": utc_iso(image.uploaded_at) if image else None,
                   "recent": bool(image and -5 <= age_seconds(image.uploaded_at) <= 20),
                   "analysis": analysis, "latest_url": image.url if image else None},
        "sensors": assess_sensors(sensors[:20]),
        "reference": {"index": reference_index_status(), "match": analysis.get("reference_match", {})},
        "physical_validation": fusion["components"]["validation"],
    }
    events = [{"id": "created", "at": utc_iso(sample.created_at), "kind": "intake", "title": "Inspection created", "detail": sample.fruit_type}]
    for row in images[:200]:
        stored = row.analysis or {}
        events.append({"id": f"image-{row.id}", "at": utc_iso(row.uploaded_at), "kind": "camera",
                       "title": f"{row.angle.removeprefix('live-').title()} frame stored",
                       "detail": "Fruit-like region detected" if stored.get("quality", {}).get("fruit_present") else "No usable fruit detected",
                       "image_url": row.url})
        identity = stored.get("identity", {})
        if identity.get("fruit") not in {None, "Unknown"}:
            events.append({"id": f"identity-{row.id}", "at": utc_iso(row.uploaded_at), "kind": "vision", "title": f"{identity['fruit']} visual identity recorded",
                           "detail": "Derived from the analysis saved with this frame; not an independent event timestamp."})
        match = stored.get("reference_match", {})
        if match.get("status") == "ready":
            events.append({"id": f"reference-{row.id}", "at": utc_iso(row.uploaded_at), "kind": "reference", "title": f"Reference match: {match.get('match')}",
                           "detail": "Derived from stored frame analysis. Similarity is not model accuracy."})
    for row in sensors:
        events.append({"id": f"sensor-{row.id}", "at": utc_iso(row.captured_at), "kind": "sensor",
                       "title": f"{sensor_source(row).title()} telemetry received", "detail": row.device_id})
    for row in results:
        validation = (row.components or {}).get("validation", {})
        events.append({"id": f"fusion-{row.id}", "at": utc_iso(row.created_at), "kind": "fusion", "title": "Fusion assessment recorded",
                       "detail": f"{row.label}; physical check: {validation.get('status', 'legacy result without current verification gate')}"})
    for row in assistant_events:
        events.append({"id": f"assistant-{row.id}", "at": utc_iso(row.created_at), "kind": "assistant",
                       "title": row.message, "detail": f"Severity: {row.severity}; event: {row.event_type}"})
    for row in reviews:
        events.append({"id": f"review-{row.id}", "at": utc_iso(row.created_at), "kind": "human", "title": "Human verification recorded",
                       "detail": f"{row.action}: {row.ground_truth or row.notes or 'assessment reviewed'}"})
    events.sort(key=lambda event: (event["at"], event["id"]), reverse=True)
    return evidence, events, [verification_info(row) for row in reviews]
