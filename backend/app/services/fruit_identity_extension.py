"""Conservative extensions for fruit identity support.

The base image analyser was originally tuned for Apple/Banana. This module adds
stability cues for red/round Apples, ripe/browned Bananas and Tomato
compatibility using already-computed shape and colour features. It does not
claim that a single RGB frame is definitive; stream routing still requires
temporal consensus.
"""

from __future__ import annotations


def _f(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def enhance_identity(analysis: dict, requested_fruit: str | None) -> dict:
    identity = dict(analysis.get("identity") or {})
    supported = list(identity.get("supported") or [])
    for fruit in ("Apple", "Banana", "Tomato"):
        if fruit not in supported:
            supported.append(fruit)
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
    dark = _f(color.get("dark_pct"))
    circularity = _f(shape.get("circularity"))
    aspect = _f(shape.get("aspect_ratio"), 99.0)
    solidity = _f(shape.get("solidity"))

    requested = str(requested_fruit or "Auto").strip().lower()
    current = str(identity.get("fruit") or "Unknown")
    current_confidence = _f(identity.get("confidence"))

    # Apple robustness ------------------------------------------------------
    # The older detector can mistake a red/yellow patch on a round Apple for an
    # elongated banana blob when segmentation changes slightly between frames.
    # Use the GLOBAL fruit silhouette as a counter-check. This specifically
    # protects round, compact red Apples from Banana/Apple frame oscillation.
    apple_round = _clamp01((0.78 - max(0.0, circularity - 0.78)) / 0.78) if circularity > 0 else 0.0
    apple_circularity = _clamp01((circularity - 0.38) / 0.38)
    apple_aspect = _clamp01((1.62 - aspect) / 0.55)
    apple_solidity = _clamp01((solidity - 0.58) / 0.36)
    apple_red = _clamp01(red / 42.0)
    apple_warm_skin = _clamp01((red + 0.20 * yellow + 0.10 * green) / 46.0)
    apple_score = max(
        0.0,
        apple_circularity * 0.28
        + apple_aspect * 0.28
        + apple_solidity * 0.14
        + apple_red * 0.20
        + apple_warm_skin * 0.10,
    )
    apple_confidence = round(min(96.0, apple_score * 100.0), 1)
    strong_apple = (
        aspect <= 1.52
        and circularity >= 0.43
        and solidity >= 0.66
        and red >= 10.0
        and apple_confidence >= 66.0
    )

    identity["apple_candidate"] = {
        "confidence": apple_confidence,
        "strong_candidate": strong_apple,
        "aspect_support": round(apple_aspect, 3),
        "circularity_support": round(apple_circularity, 3),
        "solidity_support": round(apple_solidity, 3),
        "red_support": round(apple_red, 3),
        "note": "Apple cue uses the global compact/round silhouette plus warm/red skin support to reduce frame-level Banana oscillation.",
    }

    if strong_apple and requested not in {"banana", "tomato"}:
        should_override = (
            current in {"Unknown", "Banana"}
            or current_confidence < apple_confidence + 8.0
            or requested == "apple"
        )
        if should_override:
            identity.update({
                "fruit": "Apple",
                "confidence": max(70.0, apple_confidence),
                "method": "compact Apple silhouette + warm/red skin evidence + temporal-consensus required",
                "note": "Apple identity is stabilized with global shape evidence so local yellow/brown patches do not repeatedly flip the frame to Banana.",
            })
            current = "Apple"
            current_confidence = _f(identity.get("confidence"))

    # Banana robustness -----------------------------------------------------
    # Ripe/overripe bananas often lose the yellow/green cue that the original
    # detector relied on. Their elongated silhouette remains useful, so combine
    # shape with yellow/green/brown skin evidence instead of requiring yellow.
    elongation = _clamp01((aspect - 1.28) / 1.05)
    low_roundness = _clamp01((0.74 - circularity) / 0.34)
    banana_solidity = _clamp01((solidity - 0.48) / 0.42)
    banana_skin = _clamp01((yellow + green + 0.72 * brown + 0.20 * dark) / 58.0)
    red_penalty = _clamp01((red - 18.0) / 34.0)
    banana_score = max(
        0.0,
        elongation * 0.46
        + low_roundness * 0.20
        + banana_solidity * 0.10
        + banana_skin * 0.24
        - red_penalty * 0.18,
    )
    banana_confidence = round(min(96.0, banana_score * 100.0), 1)
    strong_banana = (
        aspect >= 1.58
        and circularity <= 0.72
        and banana_confidence >= 70.0
    ) or (
        aspect >= 1.78
        and circularity <= 0.66
        and banana_confidence >= 64.0
    )

    identity["banana_candidate"] = {
        "confidence": banana_confidence,
        "strong_candidate": strong_banana,
        "elongation_support": round(elongation, 3),
        "roundness_support": round(low_roundness, 3),
        "skin_support": round(banana_skin, 3),
        "note": "Banana cue combines elongated silhouette with yellow/green/brown skin support; temporal consensus is still required.",
    }

    if strong_banana and requested not in {"apple", "tomato"}:
        should_override = (
            current in {"Unknown", "Apple"}
            or current_confidence < banana_confidence + 8.0
            or requested == "banana"
        )
        if should_override:
            identity.update({
                "fruit": "Banana",
                "confidence": max(72.0, banana_confidence),
                "method": "elongated Banana shape + skin evidence + temporal-consensus required",
                "note": "Banana identity uses global elongation plus skin evidence so ripe/browned bananas are not forced into the Apple fallback.",
            })
            current = "Banana"
            current_confidence = _f(identity.get("confidence"))

    # Tomato compatibility --------------------------------------------------
    round_score = _clamp01((circularity - 0.40) / 0.38)
    aspect_score = _clamp01((1.65 - aspect) / 0.50)
    solidity_score = _clamp01((solidity - 0.64) / 0.30)
    red_score = _clamp01(red / 48.0)
    green_support = _clamp01(green / 32.0)
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
    strong_round_tomato = (
        tomato_confidence >= 84.0
        and round_score >= 0.76
        and aspect_score >= 0.76
        and solidity_score >= 0.66
        and red >= 22.0
        and yellow < 30.0
    )

    identity["tomato_candidate"] = {
        "confidence": tomato_confidence,
        "strong_candidate": strong_round_tomato,
        "roundness": round(round_score, 3),
        "aspect_support": round(aspect_score, 3),
        "solidity_support": round(solidity_score, 3),
        "colour_support": round(colour_score, 3),
        "note": "Tomato compatibility heuristic; temporal consensus is required because red apples can overlap in RGB appearance.",
    }

    if requested == "tomato" and tomato_confidence >= 52.0:
        identity.update({
            "fruit": "Tomato",
            "confidence": max(64.0, tomato_confidence),
            "method": "operator-selected Tomato + shape/colour compatibility",
            "note": "Tomato identity is supported by operator selection plus visual compatibility; it is not a trained Tomato classifier.",
        })
    elif strong_round_tomato and requested not in {"apple", "banana"}:
        current = str(identity.get("fruit") or "Unknown")
        current_confidence = _f(identity.get("confidence"))
        # Auto Tomato is intentionally conservative; never override a strong
        # Apple decision from one frame. Temporal routing can still select Tomato
        # when repeated strong Tomato frames agree.
        if current == "Unknown" or current_confidence < 70.0:
            identity.update({
                "fruit": "Tomato",
                "confidence": tomato_confidence,
                "method": "strong Tomato shape/colour candidate + temporal-consensus required",
                "note": "Auto Tomato identity is provisional until repeated frames agree; it is not a validated trained classifier.",
            })

    analysis["identity"] = identity
    analysis["fruit_type"] = identity.get("fruit") if identity.get("fruit") != "Unknown" else analysis.get("fruit_type")
    return analysis
