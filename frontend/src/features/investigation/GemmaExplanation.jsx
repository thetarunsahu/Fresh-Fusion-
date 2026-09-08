import { useEffect, useState } from "react";
import {
  explainInvestigation,
  ollamaHealth,
  saveInvestigationSnapshot,
} from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";

export default function GemmaExplanation({ sampleId }) {
  const [health, setHealth] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let alive = true;
    setResult(null);
    setMessage("");
    if (!sampleId) {
      setHealth(null);
      return () => {
        alive = false;
      };
    }
    ollamaHealth()
      .then((value) => {
        if (alive) setHealth(value);
      })
      .catch((error) => {
        if (alive)
          setHealth({
            available: false,
            error: error.message,
          });
      });
    return () => {
      alive = false;
    };
  }, [sampleId]);

  async function generate() {
    if (!sampleId) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await explainInvestigation(sampleId);
      setResult(response);
      if (response.status !== "ready") {
        setMessage(
          response.status === "model-not-installed"
            ? "Gemma is not installed in Ollama."
            : "Ollama is unavailable. The deterministic FreshFusion verdict is unaffected.",
        );
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveSnapshot() {
    if (!sampleId) return;
    setSnapshotBusy(true);
    setMessage("");
    try {
      const response = await saveInvestigationSnapshot(sampleId, "manual-ui");
      setMessage(`Investigation snapshot #${response.id} saved.`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSnapshotBusy(false);
    }
  }

  const explanation = result?.explanation;
  const ready = health?.available && health?.model_installed !== false;

  return (
    <Panel title="Local Gemma explanation" eyebrow="OPTIONAL / EXPLANATION ONLY">
      <div className="gemmaHeader">
        <div>
          <StatusChip tone={ready ? "good" : health ? "warning" : "neutral"}>
            {!health
              ? "CHECKING OLLAMA"
              : ready
                ? "LOCAL MODEL READY"
                : "LOCAL MODEL UNAVAILABLE"}
          </StatusChip>
          <p>
            Gemma summarizes already-computed evidence. It cannot unlock, change,
            or invent the deterministic FreshFusion verdict.
          </p>
        </div>
        <div className="buttonRow">
          <button
            className="secondary"
            disabled={!sampleId || snapshotBusy}
            onClick={saveSnapshot}
          >
            {snapshotBusy ? "Saving…" : "Save evidence snapshot"}
          </button>
          <button
            className="primary"
            disabled={!sampleId || !ready || busy}
            onClick={generate}
          >
            {busy ? "Asking Gemma…" : "Explain with Gemma"}
          </button>
        </div>
      </div>

      {health?.error && <div className="notice">{health.error}</div>}
      {message && <div className="notice">{message}</div>}

      {explanation ? (
        <div className="gemmaResult">
          <div className="gemmaSummary">
            <span className="eyebrow">SUMMARY</span>
            <p>{explanation.summary}</p>
          </div>
          <div className="criticGrid">
            {[
              ["Supporting evidence", explanation.supporting_evidence],
              ["Contradictions", explanation.contradictions],
              ["Missing evidence", explanation.missing_evidence],
            ].map(([title, items]) => (
              <div key={title}>
                <h3>{title}</h3>
                {items?.length ? (
                  <ul className="findingList">
                    {items.map((item, index) => (
                      <li key={`${title}-${index}`}>{String(item)}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">None reported.</p>
                )}
              </div>
            ))}
          </div>
          <div className="gemmaNextStep">
            <span className="eyebrow">RECOMMENDED NEXT STEP</span>
            <p>{explanation.recommended_next_step}</p>
          </div>
          <p className="footnote">
            Model: {explanation.model || health?.model || "local Gemma"} · Role:
            explanation only
            {result?.snapshot_id ? ` · Saved snapshot #${result.snapshot_id}` : ""}
          </p>
        </div>
      ) : (
        <p className="muted">
          Generate an explanation after collecting evidence. No LLM call is made
          automatically.
        </p>
      )}
    </Panel>
  );
}
