from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import HumanVerification, ValidationRun

LABELS = ("fresh", "ripe", "overripe", "spoiled")


def _normalize_prediction(value: Any) -> str | None:
    label = str(value or "").strip().lower()
    if label == "spoiled-suspected":
        label = "spoiled"
    return label if label in LABELS else None


def _latest_ground_truth_rows(db: Session) -> list[HumanVerification]:
    rows = (
        db.query(HumanVerification)
        .filter(HumanVerification.ground_truth.isnot(None))
        .order_by(HumanVerification.created_at.desc(), HumanVerification.id.desc())
        .all()
    )
    latest: dict[str, HumanVerification] = {}
    for row in rows:
        latest.setdefault(row.sample_id, row)
    return list(latest.values())


def _class_metrics(matrix: dict[str, dict[str, int]], label: str) -> dict[str, float | int | None]:
    tp = matrix[label][label]
    fp = sum(matrix[truth][label] for truth in LABELS if truth != label)
    fn = sum(matrix[label][pred] for pred in LABELS if pred != label)
    support = sum(matrix[label].values())
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None if precision is None or recall is None else 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision * 100, 2) if precision is not None else None,
        "recall": round(recall * 100, 2) if recall is not None else None,
        "f1": round(f1 * 100, 2) if f1 is not None else None,
        "support": support,
    }


def current_validation_snapshot(db: Session) -> dict[str, Any]:
    rows = _latest_ground_truth_rows(db)
    records: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []

    for row in rows:
        assessment = row.assessment or {}
        truth = str(row.ground_truth or "").strip().lower()
        prediction = _normalize_prediction(assessment.get("label"))
        if truth not in LABELS:
            excluded.append({"sample_id": row.sample_id, "reason": "unsupported ground-truth label"})
            continue
        if not assessment.get("verdict_ready"):
            excluded.append({"sample_id": row.sample_id, "reason": "assessment was locked when ground truth was recorded"})
            continue
        if prediction is None:
            excluded.append({"sample_id": row.sample_id, "reason": "no comparable FreshFusion prediction in review snapshot"})
            continue
        records.append(
            {
                "sample_id": row.sample_id,
                "ground_truth": truth,
                "prediction": prediction,
                "review_id": row.id,
                "reviewed_at": row.created_at.isoformat() if row.created_at else None,
                "confidence": assessment.get("confidence"),
                "freshness_score": assessment.get("freshness_score"),
            }
        )

    matrix = {truth: {pred: 0 for pred in LABELS} for truth in LABELS}
    for item in records:
        matrix[item["ground_truth"]][item["prediction"]] += 1

    total = len(records)
    correct = sum(matrix[label][label] for label in LABELS)
    accuracy = round(correct / total * 100, 2) if total else None

    per_class = {label: _class_metrics(matrix, label) for label in LABELS}
    available_precision = [m["precision"] for m in per_class.values() if m["precision"] is not None]
    available_recall = [m["recall"] for m in per_class.values() if m["recall"] is not None]
    available_f1 = [m["f1"] for m in per_class.values() if m["f1"] is not None]

    macro_precision = round(sum(available_precision) / len(available_precision), 2) if available_precision else None
    macro_recall = round(sum(available_recall) / len(available_recall), 2) if available_recall else None
    macro_f1 = round(sum(available_f1) / len(available_f1), 2) if available_f1 else None

    represented_classes = [label for label in LABELS if sum(matrix[label].values()) > 0]
    protocol_ready = total >= 20 and len(represented_classes) == len(LABELS)

    status = "NOT YET VALIDATED" if total == 0 else "PRELIMINARY"
    note = (
        "No comparable human-ground-truth inspections exist yet."
        if total == 0
        else "Metrics are preliminary observational results, not a held-out scientific validation. "
             "Use one physical fruit per sample and preserve an independent test set before making accuracy claims."
    )

    return {
        "status": status,
        "protocol_ready": protocol_ready,
        "sample_count": total,
        "represented_classes": represented_classes,
        "required_labels": list(LABELS),
        "accuracy": accuracy,
        "precision": macro_precision,
        "recall": macro_recall,
        "f1": macro_f1,
        "confusion_matrix": {
            "labels": list(LABELS),
            "rows": [[matrix[truth][pred] for pred in LABELS] for truth in LABELS],
        },
        "per_class": per_class,
        "records": records,
        "excluded": excluded,
        "note": note,
        "protocol": {
            "unit": "physical fruit inspection",
            "ground_truth_policy": "latest human ground-truth review per inspection",
            "prediction_policy": "decision snapshot stored with that review",
            "minimum_demo_target": 20,
            "scientific_validation_requirement": "independent sample-level held-out test set",
        },
    }


def persist_validation_run(db: Session, name: str = "manual") -> ValidationRun:
    snapshot = current_validation_snapshot(db)
    run = ValidationRun(
        run_id=f"VAL-{datetime.utcnow():%Y%m%d}-{secrets.token_hex(3).upper()}",
        name=(name or "manual")[:120],
        protocol="latest-ground-truth-per-inspection",
        sample_count=snapshot["sample_count"],
        metrics={
            key: snapshot[key]
            for key in (
                "status",
                "protocol_ready",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "confusion_matrix",
                "per_class",
                "note",
            )
        },
        dataset_snapshot={
            "represented_classes": snapshot["represented_classes"],
            "records": snapshot["records"],
            "excluded": snapshot["excluded"],
            "protocol": snapshot["protocol"],
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def serialize_validation_run(row: ValidationRun) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "name": row.name,
        "protocol": row.protocol,
        "sample_count": row.sample_count,
        "metrics": row.metrics or {},
        "dataset_snapshot": row.dataset_snapshot or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
