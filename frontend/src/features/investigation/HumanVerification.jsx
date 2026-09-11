import { useState } from "react";
import { verifyAssessment } from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";
import { dateTime } from "../../shared/format";

export default function HumanVerification({ sampleId, report, onSaved }) {
  const [label, setLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const save = async (action) => {
    if (action === "override" && (!label || notes.trim().length < 3)) {
      setMessage("Choose the observed label and add a short reason before overriding the system result.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      await verifyAssessment(sampleId, {
        action,
        ground_truth: label || null,
        notes,
        reviewer,
      });
      setMessage(
        action === "override"
          ? "Manual override saved with its reason and system-assessment snapshot."
          : "Human observation saved separately from the system assessment.",
      );
      await onSaved();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel title="Human verification" eyebrow="HUMAN OBSERVATION · AUDITABLE">
      <p>
        Human observations stay separate from the system result. Ground truth is used for validation; an override records an explicit human decision without rewriting the original FreshFusion evidence.
      </p>
      <div className="reviewFields">
        <label>
          Reviewer
          <input value={reviewer} maxLength={100} onChange={(e) => setReviewer(e.target.value)} placeholder="Name or team initials" />
        </label>
        <label>
          Observed ground truth
          <select value={label} onChange={(e) => setLabel(e.target.value)}>
            <option value="">Choose a label</option>
            {["fresh", "ripe", "overripe", "spoiled"].map((x) => <option key={x} value={x}>{x[0].toUpperCase() + x.slice(1)}</option>)}
          </select>
        </label>
        <label className="wide">
          Observation / override reason
          <textarea value={notes} maxLength={2000} onChange={(e) => setNotes(e.target.value)} placeholder="Record visible condition, disagreement, labelling protocol or why a manual override is necessary." />
        </label>
      </div>
      <div className="buttonRow">
        <button className="primary" disabled={busy || !sampleId || !report?.decision?.verdict_ready} onClick={() => save("accept")}>Accept system assessment</button>
        <button className="secondary" disabled={busy || !sampleId || !report} onClick={() => save("incorrect")}>Mark as incorrect</button>
        <button className="secondary" disabled={busy || !sampleId || !label} onClick={() => save("ground_truth")}>Add ground truth</button>
        <button className="secondary" disabled={busy || !sampleId || !label || notes.trim().length < 3} onClick={() => save("override")}>Manual override</button>
      </div>
      {message && <p role="status">{message}</p>}
      <div className="reviewList">
        {report?.human_verifications?.slice(0, 8).map((row) => (
          <div key={row.id}>
            <StatusChip tone={row.action === "override" ? "warning" : "neutral"}>{row.action.replaceAll("_", " ")}</StatusChip>
            <b>{row.ground_truth || "Assessment reviewed"}</b>
            <span>{row.reviewer ? `${row.reviewer} · ` : ""}{dateTime(row.created_at)}</span>
            {row.notes && <p>{row.notes}</p>}
          </div>
        ))}
      </div>
    </Panel>
  );
}
