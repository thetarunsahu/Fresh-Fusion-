from ..fusion import evaluate_fusion
from .agreement import build_agreement
from .evidence import collect_evidence, sample_info
from .analysts import summarize_analysts
from .confidence import decision_from_fusion


def investigate(db, sample):
    # Re-evaluate age-dependent gates on reads; never trust a stale stored verdict.
    fusion = evaluate_fusion(db, sample)
    evidence, timeline, verifications = collect_evidence(db, sample, fusion)
    decision = decision_from_fusion(fusion)
    analysts = summarize_analysts(evidence, fusion)
    critic = fusion["components"]["critic"]
    agreement = build_agreement(analysts, critic, decision)
    return {
        "inspection_id": sample.sample_id,
        "sample": sample_info(sample),
        "status": decision["status"],
        "evidence": evidence,
        "analysts": analysts,
        "agreement": agreement,
        "critic": critic,
        "decision": decision,
        "timeline": timeline,
        "timeline_note": (
            "Newest 200 frames, 200 readings and 100 stored fusion results; rolling preview retention may "
            "remove older frames. Analysis events share their frame timestamp."
        ),
        "human_verifications": verifications,
    }
