"""Adapters over existing outputs; no alternative vision or fusion algorithms."""

def summarize_analysts(evidence, fusion):
    analysis = evidence["camera"]["analysis"]
    vision = fusion["components"].get("vision", {})
    return {
        "vision": {"method": "OpenCV + Apple/Banana identity heuristics; ML-ready",
                   "identity": analysis.get("identity", {}), "usable_images": vision.get("usable_images", 0),
                   "healthy_surface_estimate_pct": analysis.get("defects", {}).get("healthy_surface_estimate_pct"),
                   "defects": analysis.get("defects", {}), "warnings": analysis.get("issues", []),
                   "provisional_score": vision.get("provisional_vision_score"), "ai": analysis.get("ai", {})},
        "sensor": evidence["sensors"],
        "reference": evidence["reference"],
        "multiview": evidence["physical_validation"],
    }
