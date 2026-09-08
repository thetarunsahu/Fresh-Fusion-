from __future__ import annotations

from typing import Any

BANDS = ("spoiled", "overripe", "ripe", "fresh")
BAND_INDEX = {name: index for index, name in enumerate(BANDS)}


def _score_band(score: Any) -> str | None:
    if score is None:
        return None
    value = float(score)
    if value >= 82:
        return "fresh"
    if value >= 62:
        return "ripe"
    if value >= 38:
        return "overripe"
    return "spoiled"


def _reference_label(match: dict[str, Any]) -> str | None:
    raw = str(match.get("match") or "").strip()
    return raw or None


def build_agreement(analysts: dict[str, Any], critic: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    vision = analysts.get("vision") or {}
    sensor = analysts.get("sensor") or {}
    reference = analysts.get("reference") or {}
    multiview = analysts.get("multiview") or {}

    vision_band = _score_band(vision.get("provisional_score"))
    sensor_band = _score_band(sensor.get("score"))
    ref_match = reference.get("match") or {}

    matrix = [
        {
            "source": "Vision",
            "role": "freshness-bearing",
            "signal": vision_band,
            "available": vision_band is not None,
            "detail": "Derived from the current experimental vision score bands.",
        },
        {
            "source": "Sensor",
            "role": "freshness-bearing",
            "signal": sensor_band,
            "available": sensor_band is not None,
            "detail": "Derived from the current experimental sensor score bands.",
        },
        {
            "source": "Reference",
            "role": "contextual",
            "signal": _reference_label(ref_match),
            "available": ref_match.get("status") == "ready" or bool(ref_match.get("match")),
            "detail": "Published reference label/similarity; not counted as model probability or validated truth.",
        },
        {
            "source": "Multi-view",
            "role": "physical-evidence gate",
            "signal": multiview.get("status"),
            "available": bool(multiview),
            "detail": "Checks physical-view consistency; it does not vote on freshness stage.",
        },
    ]

    votes = [band for band in (vision_band, sensor_band) if band is not None]
    relationship = "INSUFFICIENT"
    if len(votes) >= 2:
        distance = abs(BAND_INDEX[votes[0]] - BAND_INDEX[votes[1]])
        relationship = "ALIGNED" if distance == 0 else "NEARBY" if distance == 1 else "CONFLICTING"

    contradictions = critic.get("contradictions") or []
    missing = critic.get("missing_evidence") or []
    if contradictions:
        status = "CONFLICTING"
    elif relationship == "ALIGNED" and not missing:
        status = "ALIGNED"
    elif relationship in {"ALIGNED", "NEARBY"}:
        status = "PARTIAL"
    else:
        status = "INSUFFICIENT"

    summary_map = {
        "ALIGNED": "Available freshness-bearing signals agree and the critic reports no blocking missing evidence.",
        "PARTIAL": "Available freshness-bearing signals are compatible, but more evidence or critic checks remain.",
        "CONFLICTING": "At least one critic contradiction or materially opposing freshness signal is present.",
        "INSUFFICIENT": "Not enough comparable freshness-bearing evidence is available to assess agreement.",
    }

    return {
        "status": status,
        "freshness_relationship": relationship,
        "freshness_votes": {"vision": vision_band, "sensor": sensor_band},
        "counted_sources": len(votes),
        "matrix": matrix,
        "summary": summary_map[status],
        "decision_ready": bool(decision.get("verdict_ready")),
        "note": (
            "Only vision and sensor scores are compared as freshness-bearing signals here. "
            "Reference evidence is contextual and multi-view evidence is a physical gate, so the matrix does not pretend all sources are equivalent votes."
        ),
    }
