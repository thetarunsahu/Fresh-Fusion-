from __future__ import annotations

SUPPORTED_FRUITS = {"apple", "banana", "tomato"}

_ACTIONS = {
    "fresh": ("Normal sale / storage", "low"),
    "ripe": ("Priority sale", "moderate"),
    "overripe": ("Quick sale / processing", "high"),
    "spoiled": ("Remove / reject", "high"),
    "spoiled-suspected": ("Remove from normal stock and verify", "high"),
}

_FRUIT_NOTES = {
    "apple": "Keep visual bruising separate from freshness: a damaged apple can still be fresh.",
    "banana": "Use colour and surface change as supporting evidence; green coverage can indicate an earlier ripening stage rather than spoilage.",
    "tomato": "Treat tomato recommendations as manual-fruit workflow support until tomato identity and freshness models are validated.",
}


def normalize_label(label: str | None) -> str:
    value = str(label or "").lower().strip().replace("_", "-")
    if value.startswith("spoiled"):
        return "spoiled-suspected" if "suspected" in value else "spoiled"
    return value


def recommendation(fruit: str | None, label: str | None, *, verdict_ready: bool, visible_damage_pct: float | None = None) -> dict:
    fruit_key = str(fruit or "").lower().strip()
    if fruit_key not in SUPPORTED_FRUITS:
        return {
            "supported": False,
            "action": "Select a supported fruit or inspect manually",
            "risk": "unverified",
            "reason": "Current product rules support Apple, Banana and Tomato only.",
            "fruit_note": None,
            "damage_note": None,
        }
    if not verdict_ready:
        return {
            "supported": True,
            "action": "Collect more evidence",
            "risk": "pending",
            "reason": "FreshFusion has not released a verified freshness assessment yet.",
            "fruit_note": _FRUIT_NOTES[fruit_key],
            "damage_note": None,
        }
    state = normalize_label(label)
    action, risk = _ACTIONS.get(state, ("Inspect again", "unverified"))
    damage_note = None
    if visible_damage_pct is not None and visible_damage_pct >= 12 and state in {"fresh", "ripe"}:
        damage_note = "Visible surface damage is elevated, but damage alone is not treated as spoilage. Review the affected area separately."
    return {
        "supported": True,
        "action": action,
        "risk": risk,
        "reason": f"Action follows the current verified freshness state: {state or 'unknown'}.",
        "fruit_note": _FRUIT_NOTES[fruit_key],
        "damage_note": damage_note,
        "rule_status": "operational heuristic; validate with FreshFusion ground truth before commercial calibration",
    }


def score_breakdown(fusion: dict) -> dict:
    sensor_score = fusion.get("sensor_score")
    vision_score = fusion.get("vision_score")
    components = fusion.get("components") or {}
    validation = components.get("validation", {})
    vision_components = components.get("vision", {})
    ready = validation.get("verdict_ready") is True
    sensor_weight = 0.48
    vision_weight = 0.52

    provisional_vision = vision_score
    if provisional_vision is None:
        provisional_vision = vision_components.get("provisional_vision_score")

    provisional_score = None
    provisional_basis = []
    if provisional_vision is not None and sensor_score is not None:
        provisional_score = round(float(sensor_score) * sensor_weight + float(provisional_vision) * vision_weight, 2)
        provisional_basis = ["sensor", "vision"]
    elif provisional_vision is not None:
        provisional_score = round(float(provisional_vision), 2)
        provisional_basis = ["vision"]
    elif sensor_score is not None:
        provisional_score = round(float(sensor_score), 2)
        provisional_basis = ["sensor"]

    sensor_contribution = round(float(sensor_score) * sensor_weight, 2) if ready and sensor_score is not None else None
    vision_contribution = round(float(vision_score) * vision_weight, 2) if ready and vision_score is not None else None
    return {
        "released": ready,
        "final_score": fusion.get("freshness_score") if ready else None,
        "provisional_score": provisional_score,
        "provisional_basis": provisional_basis,
        "formula": "sensor_score × 0.48 + vision_score × 0.52",
        "sensor": {"score": sensor_score, "weight": sensor_weight, "contribution": sensor_contribution},
        "vision": {
            "score": vision_score,
            "provisional_score": provisional_vision,
            "weight": vision_weight,
            "contribution": vision_contribution,
        },
        "physical_verification": {
            "status": validation.get("status"),
            "views_count": validation.get("views_count"),
            "required_views": validation.get("required_views", 3),
            "confidence": validation.get("confidence"),
        },
        "note": (
            "Provisional score is shown for operator visibility while evidence is still being collected. "
            "It is not the released freshness verdict. Final score remains locked until evidence gates pass. "
            "Prototype weights are not validated scientific constants."
        ),
    }
