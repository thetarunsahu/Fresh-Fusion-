"""Adapters over existing outputs; no alternative vision or fusion algorithms."""


def summarize_analysts(evidence, fusion, sample=None):
    analysis = evidence["camera"]["analysis"]
    vision = fusion["components"].get("vision", {})
    raw_identity = dict(analysis.get("identity", {}) or {})

    # The per-frame classifier is allowed to be noisy, but product-facing UI must
    # not flicker Apple/Banana on every camera frame. Once Auto routing has chosen
    # an inspection fruit, expose that stable inspection identity as the primary
    # analyst identity and keep the raw frame result separately for diagnostics.
    inspection_fruit = str(getattr(sample, "fruit_type", "") or "").strip().title()
    stable_supported = inspection_fruit in {"Apple", "Banana", "Tomato"}
    display_identity = dict(raw_identity)
    if stable_supported:
        display_identity["raw_frame_fruit"] = raw_identity.get("fruit")
        display_identity["raw_frame_confidence"] = raw_identity.get("confidence")
        display_identity["fruit"] = inspection_fruit
        display_identity["stabilized"] = True
        display_identity["stabilization_note"] = (
            "Primary identity follows the temporally stabilized inspection identity; "
            "the latest raw frame classification is retained for diagnostics only."
        )

    return {
        "vision": {
            "method": "OpenCV + temporal fruit-identity stabilization; ML-ready",
            "identity": display_identity,
            "raw_identity": raw_identity,
            "usable_images": vision.get("usable_images", 0),
            "healthy_surface_estimate_pct": analysis.get("defects", {}).get("healthy_surface_estimate_pct"),
            "defects": analysis.get("defects", {}),
            "warnings": analysis.get("issues", []),
            "provisional_score": vision.get("provisional_vision_score"),
            "ai": analysis.get("ai", {}),
        },
        "sensor": evidence["sensors"],
        "reference": evidence["reference"],
        "multiview": evidence["physical_validation"],
    }
