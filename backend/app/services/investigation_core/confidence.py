"""Present the existing deterministic score without manufacturing certainty."""

def decision_from_fusion(fusion):
    validation = fusion["components"]["validation"]
    critic = fusion["components"]["critic"]
    ready = validation.get("verdict_ready") is True
    if ready:
        status = "AWAITING HUMAN VERIFICATION"
    elif critic["contradictions"]:
        status = "PHYSICAL FRUIT NOT VERIFIED" if validation["status"].startswith("suspected_") else "CONFLICTING EVIDENCE"
    elif validation.get("status") == "no_fruit":
        status = "INCONCLUSIVE"
    elif not validation.get("sensor_present"):
        status = "WAITING FOR ESP32"
    else:
        status = "MORE EVIDENCE REQUIRED"
    reasons = critic["contradictions"] + critic["missing_evidence"]
    return {"status": status, "verdict_ready": ready, "label": fusion["label"] if ready else None,
            "freshness_score": fusion["freshness_score"] if ready else None,
            "confidence": fusion["confidence"] if ready else None,
            "risk": fusion["risk"] if ready else "unverified",
            "reason": " ".join(reasons) if reasons else "Experimental multimodal assessment; please verify against the physical fruit.",
            "confidence_method": "Deterministic view-coverage/evidence score; not validated prediction accuracy."}
