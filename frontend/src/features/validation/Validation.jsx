import { useState } from "react";
import { createValidationRun } from "../../api";
import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { fmt, titleCase } from "../../shared/format";

function Metric({ name, value, status }) {
  return (
    <div>
      <span>{name}</span>
      {value == null ? (
        <StatusChip>{status || "NOT YET VALIDATED"}</StatusChip>
      ) : (
        <strong>{fmt(value)}%</strong>
      )}
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
            {matrix.labels.map((label) => (
              <th key={label}>{titleCase(label)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.labels.map((label, rowIndex) => (
            <tr key={label}>
              <th>{titleCase(label)}</th>
              {matrix.rows[rowIndex].map((value, colIndex) => (
                <td key={`${label}-${matrix.labels[colIndex]}`}>{value}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Validation({ summary, reload }) {
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const metrics = summary?.metrics || {};
  const metricStatus = metrics.status || "NOT YET VALIDATED";
  const hasMetrics = metrics.sample_count > 0;

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
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">DATASET & VALIDATION</span>
        <h1>Measure performance only from human-labelled inspections.</h1>
        <p>
          Public datasets support reference comparison. FreshFusion validation
          metrics are derived only from comparable human ground-truth inspection
          snapshots and remain preliminary until an independent held-out protocol
          is completed.
        </p>
        <div className="buttonRow">
          <button className="secondary" onClick={reload}>
            Refresh dataset status
          </button>
          <button
            className="primary"
            disabled={!summary || saving}
            onClick={saveRun}
          >
            {saving ? "Saving…" : "Save validation snapshot"}
          </button>
        </div>
      </div>

      {message && <div className="notice">{message}</div>}
      {!summary && (
        <div className="notice">
          Backend required to inspect local reference files, labels and model
          artifacts. No counts or results are assumed.
        </div>
      )}

      <div className="twoPanels">
        <Panel title="FreshFusion validation data">
          <Facts
            items={[
              ["Labelled camera images", summary?.labelled_images],
              [
                "Human-labelled inspections",
                summary?.human_labelled_inspections,
              ],
              [
                "Ground-truth review records",
                summary?.human_ground_truth_records,
              ],
              ["Comparable metric samples", metrics.sample_count],
              [
                "Represented classes",
                metrics.represented_classes?.join(", ") || "None",
              ],
              [
                "Model deployment",
                summary ? titleCase(summary.model?.status) : "Unknown",
              ],
              [
                "Reference index",
                summary
                  ? summary.reference_index?.ready
                    ? "Available"
                    : "Not built"
                  : "Unknown",
              ],
              ["Indexed examples", summary?.reference_index?.samples],
            ]}
          />
          <p className="footnote">{summary?.label_policy}</p>
          <p className="footnote">{summary?.model?.note}</p>
        </Panel>

        <Panel title="Validation metrics" eyebrow="LATEST GROUND-TRUTH SNAPSHOTS">
          <div className="validationStatusRow">
            <StatusChip tone={hasMetrics ? "warning" : "neutral"}>
              {metricStatus}
            </StatusChip>
            {metrics.protocol_ready && (
              <StatusChip tone="good">MINIMUM DEMO COVERAGE REACHED</StatusChip>
            )}
          </div>
          <div className="metricPlaceholders">
            <Metric
              name="Accuracy"
              value={metrics.accuracy}
              status={metricStatus}
            />
            <Metric
              name="Macro Precision"
              value={metrics.precision}
              status={metricStatus}
            />
            <Metric
              name="Macro Recall"
              value={metrics.recall}
              status={metricStatus}
            />
            <Metric name="Macro F1" value={metrics.f1} status={metricStatus} />
          </div>
          <p className="footnote">
            {metrics.note ||
              "No held-out FreshFusion evaluation is available. Split by physical fruit/sample, not neighbouring camera frames."}
          </p>
        </Panel>
      </div>

      <Panel title="Confusion matrix" eyebrow="ACTUAL HUMAN LABEL → SYSTEM PREDICTION">
        {hasMetrics ? (
          <ConfusionMatrix matrix={metrics.confusion_matrix} />
        ) : (
          <p className="muted">
            Add ground truth to conclusive inspections to generate a real matrix.
          </p>
        )}
      </Panel>

      <Panel title="Per-class performance">
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
        ) : (
          <p className="muted">Per-class metrics appear after comparable ground-truth inspections exist.</p>
        )}
      </Panel>

      <div className="twoPanels">
        {summary?.datasets?.map((dataset) => (
          <Panel
            key={dataset.id}
            title={dataset.name}
            eyebrow={titleCase(dataset.purpose)}
          >
            <Facts
              items={[
                ["License (source metadata)", dataset.license],
                ["Supported reference fruits", dataset.supports.join(", ")],
                [
                  "Published classes",
                  dataset.labels?.join(", ") || "Fruit identity classes",
                ],
              ]}
            />
            <p>{dataset.note}</p>
            <a href={dataset.url} target="_blank" rel="noreferrer">
              Open dataset source
            </a>
          </Panel>
        ))}
      </div>

      <Panel title="Validation protocol">
        <p>
          One physical fruit inspection counts as one validation sample. The
          latest human ground-truth review is compared with the decision snapshot
          stored at review time. Multiple camera angles of the same fruit are not
          counted as independent samples.
        </p>
        <p className="footnote">
          A persisted validation run freezes the current records and metrics for
          later comparison. Even when 20+ samples are available, the UI keeps
          results labelled preliminary until an independent sample-level held-out
          test protocol is performed.
        </p>
        {summary?.latest_persisted_run && (
          <p className="footnote">
            Latest saved run: {summary.latest_persisted_run.run_id} ·{" "}
            {summary.latest_persisted_run.sample_count} samples ·{" "}
            {summary.latest_persisted_run.created_at}
          </p>
        )}
      </Panel>
    </div>
  );
}
