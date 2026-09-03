from __future__ import annotations

import json
import math

from ..config import BASE_DIR

INDEX_PATH = BASE_DIR / "models" / "public_reference_index.json"
_index_cache = None
_index_mtime = None

FEATURE_NAMES = [
    "red",
    "yellow",
    "green",
    "brown",
    "dark",
    "roughness",
    "edge_density",
    "entropy",
    "aspect_ratio",
    "circularity",
]


def _vector(analysis: dict) -> list[float]:
    color = analysis.get("color", {})
    texture = analysis.get("texture", {})
    shape = analysis.get("identity", {}).get("shape", {})
    return [
        float(color.get("red_pct", 0.0)) / 100.0,
        float(color.get("yellow_pct", 0.0)) / 100.0,
        float(color.get("green_pct", 0.0)) / 100.0,
        float(color.get("brown_pct", 0.0)) / 100.0,
        float(color.get("dark_pct", 0.0)) / 100.0,
        float(texture.get("roughness_index", 0.0)) / 100.0,
        float(texture.get("edge_density_pct", 0.0)) / 100.0,
        min(1.5, float(texture.get("entropy", 0.0)) / 8.0),
        min(2.0, float(shape.get("aspect_ratio", 1.0)) / 3.0),
        float(shape.get("circularity", 0.0)),
    ]


def _load_index():
    global _index_cache, _index_mtime
    if not INDEX_PATH.exists():
        return None
    mtime = INDEX_PATH.stat().st_mtime
    if _index_cache is None or _index_mtime != mtime:
        _index_cache = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        _index_mtime = mtime
    return _index_cache


def _candidate_rows(analysis: dict, fruit_type: str | None = None) -> list[tuple[float, str, dict, float]]:
    index = _load_index()
    if not index:
        return []

    fruit = (fruit_type or "").strip().lower()
    query = _vector(analysis)
    candidates = []
    for label, row in index.get("classes", {}).items():
        row_fruit = str(row.get("fruit", "")).lower()
        if fruit and fruit not in {"auto", "fruit", "unknown"} and row_fruit != fruit:
            continue
        mean = [float(v) for v in row.get("mean", [])]
        std = [max(0.04, float(v)) for v in row.get("std", [])]
        if len(mean) != len(query) or len(std) != len(query):
            continue
        z = [(query[i] - mean[i]) / std[i] for i in range(len(query))]
        distance = math.sqrt(sum(value * value for value in z) / len(z))
        similarity = max(0.0, min(100.0, math.exp(-distance / 2.2) * 100.0))
        candidates.append((similarity, label, row, distance))
    candidates.sort(reverse=True, key=lambda item: item[0])
    return candidates


def infer_fruit_identity(analysis: dict, supported: tuple[str, ...] = ("Apple", "Banana")) -> dict:
    """Infer fruit family from the cached public freshness reference index.

    This is a supporting identity signal, not a trained FreshFusion classifier.
    It is intentionally kept separate from freshness-stage matching.
    """
    if analysis.get("quality", {}).get("fruit_present") is False:
        return {"status": "no_fruit", "fruit": "Unknown", "confidence": 0.0, "scores": {}}

    candidates = _candidate_rows(analysis, "Auto")
    if not candidates:
        return {"status": "index_not_built", "fruit": "Unknown", "confidence": 0.0, "scores": {}}

    allowed = {name.lower(): name for name in supported}
    grouped: dict[str, list[float]] = {name: [] for name in allowed}
    for similarity, _label, row, _distance in candidates:
        fruit = str(row.get("fruit") or "").lower()
        if fruit in grouped:
            grouped[fruit].append(float(similarity))

    scores = {}
    for fruit, values in grouped.items():
        if not values:
            continue
        values.sort(reverse=True)
        # The best published stage should dominate identity, with a small
        # stabilising contribution from the second-best stage.
        score = values[0] * 0.82 + (values[1] if len(values) > 1 else values[0]) * 0.18
        scores[allowed[fruit]] = round(score, 1)

    if not scores:
        return {"status": "fruit_not_indexed", "fruit": "Unknown", "confidence": 0.0, "scores": {}}

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_fruit, best_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    margin = best_score - second_score

    if best_score < 24.0 or margin < 3.0:
        fruit = "Unknown"
        confidence = max(0.0, min(58.0, 35.0 + margin * 3.0))
    else:
        fruit = best_fruit
        confidence = max(58.0, min(94.0, 52.0 + margin * 2.3 + max(0.0, best_score - 35.0) * 0.35))

    return {
        "status": "ready",
        "fruit": fruit,
        "confidence": round(confidence, 1),
        "scores": scores,
        "margin": round(margin, 1),
        "method": "cached public-reference fruit-family similarity",
        "note": "Supporting identity signal from published freshness classes; not FreshFusion model accuracy.",
    }


def match_reference(analysis: dict, fruit_type: str | None) -> dict:
    quality = analysis.get("quality", {})
    if quality.get("fruit_present") is False:
        return {"status": "no_fruit", "match": None, "similarity": None}

    index = _load_index()
    if not index:
        return {
            "status": "index_not_built",
            "match": None,
            "similarity": None,
            "note": "Run ai/sync_public_reference.py once to build the compact reference index from the public freshness dataset.",
        }

    candidates = _candidate_rows(analysis, fruit_type)
    if not candidates:
        return {
            "status": "fruit_not_indexed",
            "match": None,
            "similarity": None,
            "fruit_type": fruit_type,
        }

    best = candidates[0]
    top = [
        {
            "label": label,
            "similarity": round(score, 1),
            "fruit": row.get("fruit"),
            "stage": row.get("stage"),
            "reference_samples": row.get("count"),
        }
        for score, label, row, _ in candidates[:3]
    ]
    return {
        "status": "ready",
        "match": best[1],
        "similarity": round(best[0], 1),
        "fruit": best[2].get("fruit"),
        "stage": best[2].get("stage"),
        "reference_samples": best[2].get("count"),
        "source": index.get("source"),
        "top_matches": top,
        "note": "Similarity is a compact handcrafted-feature reference comparison, not a substitute for a validated trained freshness model.",
    }
