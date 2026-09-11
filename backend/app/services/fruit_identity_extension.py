"""Conservative extensions for fruit identity support.

The existing image analyser was originally tuned for Apple/Banana. This module
adds a Tomato compatibility check using already-computed shape and colour
features. It intentionally avoids pretending that a round red fruit can always
be distinguished from an apple with simple heuristics.
"""

from __future__ import annotations


def _f(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def enhance_identity(analysis: dict, requested_fruit: str | None) -> dict:
    identity = dict(analysis.get("identity") or {})
    supported = list(identity.get("supported") or [])
    if "Tomato" not in supported:
        supported.append("Tomato")
    identity["supported"] = supported

    if (analysis.get("quality") or {}).get("fruit_present") is not True:
        analysis["identity"] = identity
        return analysis

    color = analysis.get("color") or {}
    shape = identity.get("shape") or analysis.get("segmentation", {}).get("shape") or {}
    red = _f(color.get("red_pct"))
    green = _f(color.get("green_pct"))
    yellow = _f(color.get("yellow_pct"))
    brown = _f(color.get("brown_pct"))
    circularity = _f(shape.get("circularity"))
    aspect = _f(shape.get("aspect_ratio"), 99.0)
    solidity = _f(shape.get("solidity"))

    round_score = max(0.0, min(1.0, (circularity - 0.42) / 0.38))
    aspect_score = max(0.0, min(1.0, (1.75 - aspect) / 0.55))
    solidity_score = max(0.0, min(1.0, (solidity - 0.65) / 0.30))
    skin_score = max(0.0, min(1.0, (red + 0.35 * green + 0.15 * yellow) / 55.0))
    decay_penalty = min(0.22, brown / 100.0 * 0.4)
    tomato_score = max(0.0, round_score * 0.30 + aspect_score * 0.20 + solidity_score * 0.18 + skin_score * 0.32 - decay_penalty)
    tomato_confidence = round(min(91.0, tomato_score * 100.0), 1)

    requested = str(requested_fruit or "Auto").strip().lower()
    current = str(identity.get("fruit") or "Unknown")
    current_confidence = _f(identity.get("confidence"))

    identity["tomato_candidate"] = {
        "confidence": tomato_confidence,
        "roundness": round(round_score, 3),
        "aspect_support": round(aspect_score, 3),
        "solidity_support": round(solidity_score, 3),
        "colour_support": round(skin_score, 3),
        "note": "Tomato compatibility heuristic; a phone RGB image alone cannot always distinguish a round red tomato from an apple.",
    }

    # When the operator explicitly selected Tomato, prefer a compatible Tomato
    # identity instead of allowing the older Apple/Banana fallback to contradict
    # the selected inspection. This remains evidence, not ground truth.
    if requested == "tomato" and tomato_confidence >= 56.0:
        identity.update({
            "fruit": "Tomato",
            "confidence": max(60.0, tomato_confidence),
            "method": "operator-selected Tomato + shape/colour compatibility",
            "note": "Tomato identity is supported by operator selection plus visual compatibility; it is not a trained Tomato classifier.",
        })
    # Auto mode is deliberately conservative because red apples and tomatoes can
    # overlap in these handcrafted RGB features.
    elif requested in {"auto", "fruit", "unknown", ""} and tomato_confidence >= 86.0 and current_confidence < 68.0:
        identity.update({
            "fruit": "Tomato",
            "confidence": tomato_confidence,
            "method": "conservative Tomato shape/colour candidate",
            "note": "Auto Tomato identity is provisional until a trained multi-fruit identity model is validated.",
        })

    analysis["identity"] = identity
    analysis["fruit_type"] = identity.get("fruit") if identity.get("fruit") != "Unknown" else analysis.get("fruit_type")
    return analysis
