"""Conservative extensions for fruit identity support.

The base image analyser was originally tuned for Apple/Banana. This module adds
Tomato compatibility using already-computed shape and colour features. It does
not claim that a single RGB frame can always distinguish a tomato from a red
apple, so auto mode requires a stronger cue set than manual Tomato mode.
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

    round_score = max(0.0, min(1.0, (circularity - 0.40) / 0.38))
    aspect_score = max(0.0, min(1.0, (1.65 - aspect) / 0.50))
    solidity_score = max(0.0, min(1.0, (solidity - 0.64) / 0.30))
    red_score = max(0.0, min(1.0, red / 48.0))
    green_support = max(0.0, min(1.0, green / 32.0))
    colour_score = min(1.0, red_score * 0.82 + green_support * 0.18)
    decay_penalty = min(0.20, brown / 100.0 * 0.35)

    tomato_score = max(
        0.0,
        round_score * 0.31
        + aspect_score * 0.22
        + solidity_score * 0.18
        + colour_score * 0.29
        - decay_penalty,
    )
    tomato_confidence = round(min(93.0, tomato_score * 100.0), 1)

    requested = str(requested_fruit or "Auto").strip().lower()
    current = str(identity.get("fruit") or "Unknown")
    current_confidence = _f(identity.get("confidence"))

    strong_round_tomato = (
        tomato_confidence >= 82.0
        and round_score >= 0.72
        and aspect_score >= 0.72
        and solidity_score >= 0.62
        and red >= 18.0
        and yellow < 35.0
    )

    identity["tomato_candidate"] = {
        "confidence": tomato_confidence,
        "strong_candidate": strong_round_tomato,
        "roundness": round(round_score, 3),
        "aspect_support": round(aspect_score, 3),
        "solidity_support": round(solidity_score, 3),
        "colour_support": round(colour_score, 3),
        "note": "Tomato compatibility heuristic; temporal consensus is required in auto mode because red apples can overlap in RGB appearance.",
    }

    # Explicit operator selection is a strong prior, but still requires the frame
    # to look compatible with a real tomato rather than blindly relabelling it.
    if requested == "tomato" and tomato_confidence >= 52.0:
        identity.update({
            "fruit": "Tomato",
            "confidence": max(64.0, tomato_confidence),
            "method": "operator-selected Tomato + shape/colour compatibility",
            "note": "Tomato identity is supported by operator selection plus visual compatibility; it is not a trained Tomato classifier.",
        })
    # Auto mode: permit a genuinely strong tomato cue set to override an Apple
    # fallback. The stream router still requires repeated-frame consensus before
    # changing the active fruit identity.
    elif requested in {"auto", "fruit", "unknown", ""} and strong_round_tomato:
        if current == "Unknown" or current_confidence < 76.0 or (
            current == "Apple" and tomato_confidence >= current_confidence - 2.0
        ):
            identity.update({
                "fruit": "Tomato",
                "confidence": tomato_confidence,
                "method": "strong Tomato shape/colour candidate + temporal-consensus required",
                "note": "Auto Tomato identity is provisional until repeated frames agree; it is not a validated trained classifier.",
            })

    analysis["identity"] = identity
    analysis["fruit_type"] = identity.get("fruit") if identity.get("fruit") != "Unknown" else analysis.get("fruit_type")
    return analysis
