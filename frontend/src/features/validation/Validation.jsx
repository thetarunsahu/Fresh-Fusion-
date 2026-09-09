import { useState } from "react";
import { createValidationRun } from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";
import { fmt, titleCase } from "../../shared/format";

function Metric({ name, value, status }) {
  return (
    <div>
      <span>{name}</span>
      {value == null ? <StatusChip>{status || "NOT YET VALIDATED"}</StatusChip> : <strong>{fmt(value)}%</strong>}
    </div>
  );
}

function ConfusionMatrix({ matrix }) {
  if (!matrix?.labels?.length || !matrix?.rows?.length) return null;
  return (
    <div className="confusionWrap">
      <table className="confusionMatrix">
        <thead>
          <tr>
            <th>Actual ↓ / Predicted →</th>
            {matrix.labels.map((label) => <th key={label}>{titleCase(label)}</th>)}
          </tr>
        </thead>
        <tbody>
          {matrix.labels.map((label, rowIndex) => (
            <tr key={label}>
              <th>{titleCase(label)}</th>
              {matrix.rows[rowIndex].map((value, colIndex) => (
                <td key={`${label}-${matrix.labels[colIndex]}`} className={rowIndex === colIndex ? "matrixHit" : ""}>{value}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatCard({ label, value, warning = false }) {
  return (
    <article className="ffValidationStat">
      <span>{label}</span>
      <strong className={warning ? "warning" : ""}>{value ?? "—"}</strong>
    </article>
  );
}

export default function Validation({ summary, reload }) {
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const metrics = summary?.evaluation || {};
  const metricStatus = metrics.status || "NOT YET VALIDATED";
  const hasMetrics = (metrics.sample_count || 0) > 0;

  async function saveRun() {
    setSaving(true);
    setMessage("");
    try {
      const run = await createValidationRun("manual-ui");
      setMessage(`Validation snapshot ${run.run_id} saved with ${run.sample_count} comparable inspections.`);
      await reload();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="featurePage validationFigmaPage">
      <div className="pageIntro ffValidationIntro">
        <span className="eyebrow">FRESHFUSION WORKSPACE</span>
        <h1>Dataset & Validation</h1>
        <p>Ground truth, frozen validation runs and transparent experimental metrics—no fabricated accuracy.</p>
        <div className="buttonRow">
          <button className="secondary" onClick={reload}>Refresh status</button>
          <button className="primary" disabled={!summary || saving} onClick={saveRun}>
            {saving ? "Saving…" : "Save validation snapshot"}
          </button>
        </div>
      </div>

      {message && <div className="notice">{message}</div>}
      {!summary && <div className="notice">Backend required. No validation counts or results are assumed.</div>}

      <section className="ffValidationStats">
        <StatCard label="HUMAN GT RECORDS" value={summary?.human_ground_truth_records} />
        <StatCard label="LABELLED INSPECTIONS" value={summary?.human_labelled_inspections} />
        <StatCard label="COMPARABLE SAMPLES" value={metrics.sample_count} />
        <StatCard label="MODEL STATUS" value={summary ? titleCase(summary.model?.status).toUpperCase() : "UNKNOWN"} warning={summary?.model?.status !== "deployed"} />
      </section>

      <section className="ffValidationGrid">
        <Panel title="Observational metrics" eyebrow="LATEST VALIDATION SNAPSHOT">
          <div className="validationStatusRow">
            <StatusChip tone={hasMetrics ? "warning" : "neutral"}>{metricStatus}</StatusChip>
            {metrics.protocol_ready && <StatusChip tone="good">MINIMUM DEMO COVERAGE REACHED</StatusChip>}
          </div>
          <div className="metricPlaceholders">
            <Metric name="Accuracy" value={metrics.accuracy} status={metricStatus} />
            <Metric name="Macro Precision" value={metrics.precision} status={metricStatus} />
            <Metric name="Macro Recall" value={metrics.recall} status={metricStatus} />
            <Metric name="Macro F1" value={metrics.f1} status={metricStatus} />
          </div>
          <p className="footnote">{metrics.note || "Metrics appear only after comparable human-ground-truth inspections exist."}</p>
        </Panel>

        <Panel title="Confusion matrix" eyebrow="ACTUAL HUMAN LABEL → SYSTEM PREDICTION">
          {hasMetrics ? <ConfusionMatrix matrix={metrics.confusion_matrix} /> : (
            <div className="emptyState">Add ground truth to conclusive inspections to generate a real matrix.</div>
          )}
        </Panel>
      </section>

      <Panel title="Frozen snapshots keep the evidence trail auditable." eyebrow="VALIDATION RUNS" className="validationRunsPanel">
        <div className="ffRunSummary">
          <span>Current protocol</span>
          <b>latest-ground-truth-per-inspection</b>
          <StatusChip tone={hasMetrics ? "warning" : "neutral"}>{hasMetrics ? "PRELIMINARY" : "WAITING FOR DATA"}</StatusChip>
        </div>
        {summary?.latest_persisted_run ? (
          <div className="ffValidationRunRow">
            <b>{summary.latest_persisted_run.run_id}</b>
            <span>{summary.latest_persisted_run.sample_count} comparable samples</span>
            <span>{summary.latest_persisted_run.created_at}</span>
            <StatusChip tone="warning">PRELIMINARY</StatusChip>
          </div>
        ) : (
          <p className="muted">No frozen validation run has been saved yet.</p>
        )}
      </Panel>

      <section className="ffValidationDetails">
        <Panel title="Per-class performance" eyebrow="HUMAN LABELLED ONLY">
          {hasMetrics ? (
            <div className="classMetricGrid">
              {Object.entries(metrics.per_class || {}).map(([label, values]) => (
                <div className="classMetricCard" key={label}>
                  <span className="eyebrow">{titleCase(label)}</span>
                  <strong>{values.support ?? 0} samples</strong>
                  <small>Precision: {values.precision == null ? "—" : `${fmt(values.precision)}%`}</small>
                  <small>Recall: {values.recall == null ? "—" : `${fmt(values.recall)}%`}</small>
                  <small>F1: {values.f1 == null ? "—" : `${fmt(values.f1)}%`}</small>
                </div>
              ))}
            </div>
          ) : <p className="muted">Per-class metrics appear after comparable ground-truth inspections exist.</p>}
        </Panel>

        <Panel title="Validation boundary" eyebrow="SCIENTIFIC GUARDRAIL">
          <p>One physical fruit inspection counts as one validation sample. Multiple camera angles of the same fruit are not independent samples.</p>
          <p className="footnote">Even after minimum demo coverage is reached, results remain preliminary until an independent sample-level held-out protocol is performed.</p>
          <div className="chipRow">
            <StatusChip>Reference index: {summary?.reference_index?.ready ? "Available" : "Not built"}</StatusChip>
            <StatusChip>{summary?.reference_index?.samples ?? 0} indexed examples</StatusChip>
          </div>
        </Panel>
      </section>
    </div>
  );
}
