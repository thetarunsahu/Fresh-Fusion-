from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import FusionResult, InspectionEvent

ALERT_COOLDOWN_SECONDS = 90


def event_info(row: InspectionEvent) -> dict:
    return {
        "id": row.id,
        "event_type": row.event_type,
        "severity": row.severity,
        "message": row.message,
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def record_event(db: Session, sample_id: str, event_type: str, message: str, *, severity: str = "info", payload: dict | None = None, dedupe_key: str | None = None, cooldown_seconds: int = ALERT_COOLDOWN_SECONDS) -> InspectionEvent | None:
    if dedupe_key:
        cutoff = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
        existing = (
            db.query(InspectionEvent)
            .filter(InspectionEvent.sample_id == sample_id, InspectionEvent.dedupe_key == dedupe_key, InspectionEvent.created_at >= cutoff)
            .order_by(InspectionEvent.created_at.desc())
            .first()
        )
        if existing:
            return None
    row = InspectionEvent(
        sample_id=sample_id,
        event_type=event_type,
        severity=severity,
        dedupe_key=dedupe_key,
        message=message,
        payload=payload or {},
    )
    db.add(row)
    return row


def previous_result(db: Session, sample_id: str, *, exclude_id: int | None = None) -> FusionResult | None:
    query = db.query(FusionResult).filter(FusionResult.sample_id == sample_id)
    if exclude_id is not None:
        query = query.filter(FusionResult.id != exclude_id)
    return query.order_by(FusionResult.created_at.desc(), FusionResult.id.desc()).first()


def record_assessment_changes(db: Session, current: FusionResult) -> list[InspectionEvent]:
    created = []
    previous = previous_result(db, current.sample_id, exclude_id=current.id)
    current_validation = (current.components or {}).get("validation", {})
    if previous:
        previous_validation = (previous.components or {}).get("validation", {})
        if current_validation.get("verdict_ready") and previous_validation.get("verdict_ready") and current.label != previous.label:
            severity = "critical" if str(current.label).startswith("spoiled") else "warning"
            row = record_event(
                db,
                current.sample_id,
                "freshness_class_changed",
                f"Condition changed from {previous.label} to {current.label}.",
                severity=severity,
                payload={"previous": previous.label, "current": current.label, "previous_score": previous.freshness_score, "current_score": current.freshness_score},
                dedupe_key=f"class:{previous.label}:{current.label}",
            )
            if row: created.append(row)
        if current_validation.get("verdict_ready") and previous_validation.get("verdict_ready"):
            drop = float(previous.freshness_score) - float(current.freshness_score)
            if drop >= 8:
                row = record_event(
                    db,
                    current.sample_id,
                    "score_deterioration",
                    f"Freshness score dropped by {drop:.1f} points since the previous assessment.",
                    severity="warning" if drop < 18 else "critical",
                    payload={"drop": round(drop, 2), "previous_score": previous.freshness_score, "current_score": current.freshness_score},
                    dedupe_key="score_drop",
                )
                if row: created.append(row)
    sensor = (current.components or {}).get("sensor_evidence", {})
    trend = sensor.get("trend") if isinstance(sensor, dict) else None
    if isinstance(trend, dict) and trend.get("direction") == "rising":
        rate = trend.get("raw_per_minute")
        row = record_event(
            db,
            current.sample_id,
            "gas_trend_rising",
            "Gas response is rising compared with recent readings.",
            severity="warning",
            payload={"raw_per_minute": rate, "delta_raw": trend.get("delta_raw")},
            dedupe_key="gas_trend_rising",
        )
        if row: created.append(row)
    return created


def recent_events(db: Session, sample_id: str, limit: int = 50) -> list[dict]:
    rows = (
        db.query(InspectionEvent)
        .filter(InspectionEvent.sample_id == sample_id)
        .order_by(InspectionEvent.created_at.desc(), InspectionEvent.id.desc())
        .limit(limit)
        .all()
    )
    return [event_info(row) for row in rows]
