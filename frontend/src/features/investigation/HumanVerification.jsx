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
        "Human observation saved separately from the system assessment.",
      );
      await onSaved();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Panel
      title="Human verification"
      eyebrow="YOUR OBSERVATION IS SEPARATE EVIDENCE"
    >
      <p>
        Accepting a result does not validate model accuracy. Ground truth is a
        human observation for this inspection; it does not rewrite public
        reference labels or automatically label every image.
      </p>
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
            placeholder="Record visible condition, disagreements or the labelling protocol."
          />
        </label>
      </div>
      <div className="buttonRow">
        <button
          className="primary"
          disabled={busy || !sampleId || !report?.decision?.verdict_ready}
          onClick={() => save("accept")}
        >
          Accept system assessment
        </button>
        <button
          className="secondary"
          disabled={busy || !sampleId || !report}
          onClick={() => save("incorrect")}
        >
          Mark as incorrect
        </button>
        <button
          className="secondary"
          disabled={busy || !sampleId || !label}
          onClick={() => save("ground_truth")}
        >
          Add ground truth
        </button>
      </div>
      {message && <p role="status">{message}</p>}
      <div className="reviewList">
        {report?.human_verifications?.slice(0, 5).map((row) => (
          <div key={row.id}>
            <StatusChip>{row.action.replaceAll("_", " ")}</StatusChip>
            <b>{row.ground_truth || "Assessment reviewed"}</b>
            <span>{dateTime(row.created_at)}</span>
            {row.notes && <p>{row.notes}</p>}
          </div>
        ))}
      </div>
    </Panel>
  );
}
