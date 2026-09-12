"""Version metadata for reproducible FreshFusion decisions.

These are software/protocol identifiers, not claims of scientific validation.
Override with environment variables when deploying a new calibrated release.
"""

from __future__ import annotations

import os
from pathlib import Path
import hashlib

from .ai import MODEL_PATH, LABELS_PATH

RULE_VERSION = os.getenv("FRESHFUSION_RULE_VERSION", "rules-2026.09-p0")
RECOMMENDATION_VERSION = os.getenv("FRESHFUSION_RECOMMENDATION_VERSION", "recommendations-2026.09-p0")
CALIBRATION_VERSION = os.getenv("FRESHFUSION_CALIBRATION_VERSION", "UNCALIBRATED")
DATASET_VERSION = os.getenv("FRESHFUSION_DATASET_VERSION", "freshfusion-ground-truth-v0")
SPLIT_VERSION = "sample-split-v1"


def _sha256(path: Path):
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def decision_provenance():
    model_present = MODEL_PATH.exists() and LABELS_PATH.exists()
    return {
        "rule_version": RULE_VERSION,
        "recommendation_version": RECOMMENDATION_VERSION,
        "calibration_version": CALIBRATION_VERSION,
        "dataset_version": DATASET_VERSION,
        "split_version": SPLIT_VERSION,
        "model": {
            "status": "artifact-present-unverified" if model_present else "not-deployed",
            "path": str(MODEL_PATH) if MODEL_PATH.exists() else None,
            "sha256": _sha256(MODEL_PATH) if MODEL_PATH.exists() else None,
        },
        "scientific_status": "calibration-pending" if CALIBRATION_VERSION == "UNCALIBRATED" else "configured",
    }
