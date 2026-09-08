import { useState } from "react";
import { CheckCircle2, CircleX, Tag } from "lucide-react";
import { verifyAssessment } from "../../api";
import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { dateTime, titleCase } from "../../shared/format";

export default function HumanVerification({ sampleId, report, onSaved }) {
  const [label, setLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const decision = report?.decision;
  const reviews = report?.human_verifications || [];

  const save = async (action) => {
    setBusy(true);
    setMessage(null);
    try {
      await verifyAssessment(sampleId, {
        action,
        ground_truth: label || null,
        notes,
        reviewer,
      });
      setMessage({
        type: "success",
        text: "Human observation saved as separate audit evidence.",
      });
      setNotes("");
      if (action === "ground_truth") setLabel("");
      await onSaved();
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel
      title="Human verification"
      eyebrow="INDEPENDENT OBSERVATION · APPEND-ONLY AUDIT TRAIL"
    >
      <div className="reviewSummary">
        <div>
          <p>
            Human review never overwrites the system result. Accept, challenge or
            add an observed ground-truth stage while preserving the assessment
            that existed at review time.
          </p>
          <div className="chipRow">
            <StatusChip tone={decision?.verdict_ready ? "good" : "warning"}>
              {decision?.verdict_ready ? "ASSESSMENT AVAILABLE" : "VERDICT LOCKED"}
            </StatusChip>
            <StatusChip>{reviews.length} review{reviews.length === 1 ? "" : "s"}</StatusChip>
          </div>
        </div>
        <Facts
          items={[
            ["Current system state", decision?.status],
            ["Current label", decision?.verdict_ready ? titleCase(decision.label) : "Not released"],
            ["Current confidence", decision?.verdict_ready && decision.confidence != null ? `${decision.confidence}%` : "Not released"],
          ]}
        />
      </div>

      <div className="reviewFields">
        <label>
          Reviewer (optional)
          <input
            value={reviewer}
            maxLength={100}
            onChange={(e) => setReviewer(e.target.value)}
            placeholder="Name or team initials"
          />
        </label>
        <label>
          Observed ground truth
          <select value={label} onChange={(e) => setLabel(e.target.value)}>
            <option value="">Choose a label</option>
            {["fresh", "ripe", "overripe", "spoiled"].map((x) => (
              <option key={x} value={x}>
                {x[0].toUpperCase() + x.slice(1)}
              </option>
            ))}
          </select>
        </label>
        <label className="wide">
          Observation notes
          <textarea
            value={notes}
            maxLength={2000}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Record visible condition, disagreement reason, storage context or labelling protocol."
          />
          <small>{notes.length}/2000 characters</small>
        </label>
      </div>

      <div className="reviewActionGrid">
        <button
          className="reviewAction"
          disabled={busy || !sampleId || !decision?.verdict_ready}
          onClick={() => save("accept")}
        >
          <CheckCircle2 size={19} />
          <span>
            <b>Accept assessment</b>
            <small>Confirms this inspection was reviewed; it is not an accuracy claim.</small>
          </span>
        </button>
        <button
          className="reviewAction"
          disabled={busy || !sampleId || !report}
          onClick={() => save("incorrect")}
        >
          <CircleX size={19} />
          <span>
            <b>Mark incorrect</b>
            <small>Preserves a disagreement for later error analysis.</small>
          </span>
        </button>
        <button
          className="reviewAction"
          disabled={busy || !sampleId || !label}
          onClick={() => save("ground_truth")}
        >
          <Tag size={19} />
          <span>
            <b>Add ground truth</b>
            <small>Stores your observed Fresh / Ripe / Overripe / Spoiled stage.</small>
          </span>
        </button>
      </div>

      {message && (
        <div
          role="status"
          className={`reviewMessage ${message.type === "error" ? "error" : "success"}`}
        >
          {message.text}
        </div>
      )}

      <div className="reviewAuditHeader">
        <h3>Recent human audit trail</h3>
        <span>Newest first</span>
      </div>
      <div className="reviewList">
        {reviews.slice(0, 8).map((row) => (
          <div key={row.id}>
            <StatusChip>{row.action.replaceAll("_", " ")}</StatusChip>
            <b>{row.ground_truth ? titleCase(row.ground_truth) : "Assessment reviewed"}</b>
            <span>{dateTime(row.created_at)}</span>
            {row.reviewer && <span>Reviewer: {row.reviewer}</span>}
            {row.notes && <p>{row.notes}</p>}
          </div>
        ))}
        {!reviews.length && (
          <p className="muted">No human review has been recorded for this inspection.</p>
        )}
      </div>
      <p className="footnote">
        Ground truth remains separate from public reference labels and does not
        automatically label every camera frame from the same inspection.
      </p>
    </Panel>
  );
}
