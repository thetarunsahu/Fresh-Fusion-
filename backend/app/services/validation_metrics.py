"""Validation derived only from FreshFusion human ground truth.

Metrics are calculated from verified prediction/ground-truth pairs. Public
reference labels are never treated as FreshFusion ground truth. Dataset split
assignment is deterministic at the physical-fruit key level so repeated views or
repeated inspections of the same declared fruit specimen cannot cross splits.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from sqlalchemy.orm import Session

from ..models import FruitSample, FusionResult, HumanVerification, InspectionProfile

LABELS = ["fresh", "ripe", "overripe", "spoiled"]
SPLIT_SALT = "freshfusion-sample-split-v1"


def normalize_label(value):
    key = str(value or "").strip().lower().replace("_", "-")
    if key in {"spoiled-suspected", "spoiled"}:
        return "spoiled"
    return key if key in LABELS else None


def specimen_key(sample_id: str, profile: InspectionProfile | None) -> str:
    protocol = (profile.protocol or {}) if profile else {}
    declared = str(protocol.get("fruit_instance_id") or "").strip()
    return declared or sample_id


def split_for_key(key: str) -> str:
    digest = hashlib.sha256(f"{SPLIT_SALT}:{key}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def _latest_ground_truth(db: Session):
    rows = (
        db.query(HumanVerification)
        .filter(HumanVerification.ground_truth.isnot(None))
        .order_by(HumanVerification.created_at.desc(), HumanVerification.id.desc())
        .all()
    )
    chosen = {}
    for row in rows:
        if row.sample_id not in chosen and normalize_label(row.ground_truth):
            chosen[row.sample_id] = row
    return chosen


def _prediction_for_review(db: Session, review: HumanVerification):
    assessment = review.assessment or {}
    if assessment.get("verdict_ready") is True:
        label = normalize_label(assessment.get("label"))
        if label:
            return label, "verification_snapshot"

    query = db.query(FusionResult).filter(FusionResult.sample_id == review.sample_id)
    if review.created_at is not None:
        query = query.filter(FusionResult.created_at <= review.created_at)
    rows = query.order_by(FusionResult.created_at.desc(), FusionResult.id.desc()).limit(20).all()
    for row in rows:
        validation = (row.components or {}).get("validation", {})
        label = normalize_label(row.label)
        if validation.get("verdict_ready") is True and label:
            return label, "preceding_verified_fusion"
    return None, None


def validation_pairs(db: Session):
    reviews = _latest_ground_truth(db)
    profiles = {row.sample_id: row for row in db.query(InspectionProfile).all()}
    samples = {row.sample_id: row for row in db.query(FruitSample).filter(FruitSample.sample_id.in_(list(reviews) or ["__none__"])).all()}
    pairs = []
    for sample_id, review in reviews.items():
        truth = normalize_label(review.ground_truth)
        prediction, prediction_source = _prediction_for_review(db, review)
        profile = profiles.get(sample_id)
        key = specimen_key(sample_id, profile)
        sample = samples.get(sample_id)
        pairs.append({
            "sample_id": sample_id,
            "fruit_instance_id": key,
            "fruit_type": sample.fruit_type if sample else None,
            "ground_truth": truth,
            "prediction": prediction,
            "prediction_source": prediction_source,
            "split": split_for_key(key),
            "reviewed_at": review.created_at.isoformat() if review.created_at else None,
            "usable_for_metrics": bool(truth and prediction),
        })
    return pairs


def _safe_div(a, b):
    return a / b if b else 0.0


def compute_metrics(db: Session):
    pairs = validation_pairs(db)
    usable = [row for row in pairs if row["usable_for_metrics"]]
    matrix = {truth: {pred: 0 for pred in LABELS} for truth in LABELS}
    for row in usable:
        matrix[row["ground_truth"]][row["prediction"]] += 1

    correct = sum(matrix[label][label] for label in LABELS)
    total = len(usable)
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[t][label] for t in LABELS if t != label)
        fn = sum(matrix[label][p] for p in LABELS if p != label)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        support = sum(matrix[label].values())
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    macro_precision = sum(x["precision"] for x in per_class.values()) / len(LABELS)
    macro_recall = sum(x["recall"] for x in per_class.values()) / len(LABELS)
    macro_f1 = sum(x["f1"] for x in per_class.values()) / len(LABELS)
    fruit_breakdown = defaultdict(lambda: {"total": 0, "correct": 0})
    for row in usable:
        fruit = row.get("fruit_type") or "Unknown"
        fruit_breakdown[fruit]["total"] += 1
        fruit_breakdown[fruit]["correct"] += int(row["ground_truth"] == row["prediction"])

    status = "NOT YET VALIDATED" if total == 0 else "PRELIMINARY"
    claim_ready = total >= 20 and all(per_class[label]["support"] >= 3 for label in LABELS)
    if claim_ready:
        status = "VALIDATION DATA AVAILABLE"

    return {
        "status": status,
        "claim_ready": claim_ready,
        "sample_count": total,
        "ground_truth_records": len(pairs),
        "unmatched_ground_truth": len(pairs) - total,
        "accuracy": round(_safe_div(correct, total), 4) if total else None,
        "macro_precision": round(macro_precision, 4) if total else None,
        "macro_recall": round(macro_recall, 4) if total else None,
        "macro_f1": round(macro_f1, 4) if total else None,
        "confusion_matrix": matrix if total else None,
        "per_class": per_class if total else None,
        "fruit_breakdown": {
            fruit: {**values, "accuracy": round(_safe_div(values["correct"], values["total"]), 4)}
            for fruit, values in fruit_breakdown.items()
        } if total else {},
        "policy": "Metrics use the latest human ground truth per inspection and only a verified prediction available at or before that review. Public reference labels are excluded.",
        "claim_policy": "Treat metrics as preliminary until at least 20 matched samples exist with at least 3 ground-truth examples in every freshness class.",
        "pairs": pairs,
    }


def split_manifest(db: Session):
    profiles = {row.sample_id: row for row in db.query(InspectionProfile).all()}
    samples = db.query(FruitSample).order_by(FruitSample.created_at.asc()).all()
    rows = []
    for sample in samples:
        key = specimen_key(sample.sample_id, profiles.get(sample.sample_id))
        rows.append({
            "sample_id": sample.sample_id,
            "fruit_instance_id": key,
            "fruit_type": sample.fruit_type,
            "split": split_for_key(key),
        })
    counts = {name: sum(1 for row in rows if row["split"] == name) for name in ("train", "validation", "test")}
    return {
        "version": "sample-split-v1",
        "strategy": "deterministic SHA-256 split by fruit_instance_id (fallback: sample_id), 70/15/15",
        "counts": counts,
        "rows": rows,
    }
