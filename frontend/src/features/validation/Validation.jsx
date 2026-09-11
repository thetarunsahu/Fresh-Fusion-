import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { titleCase } from "../../shared/format";

const pct = (value) => value == null ? "--" : `${(Number(value) * 100).toFixed(1)}%`;

function Metric({ name, metric }) {
  const status = metric?.status || "NOT YET VALIDATED";
  const value = name === "Confusion Matrix" ? null : metric?.value;
  return (
    <div>
      <span>{name}</span>
      {value == null ? <StatusChip>{status}</StatusChip> : <><b className="validationMetricValue">{pct(value)}</b><StatusChip>{status}</StatusChip></>}
    </div>
  );
}

function ConfusionMatrix({ value }) {
  if (!value) return <p className="footnote">No matched verified prediction/ground-truth pairs yet.</p>;
  const labels = ["fresh", "ripe", "overripe", "spoiled"];
  return (
    <div className="ffConfusionWrap">
      <table className="ffConfusion">
        <thead><tr><th>Actual ↓ / Predicted →</th>{labels.map((label)=><th key={label}>{titleCase(label)}</th>)}</tr></thead>
        <tbody>{labels.map((truth)=><tr key={truth}><th>{titleCase(truth)}</th>{labels.map((pred)=><td key={pred}>{value?.[truth]?.[pred] ?? 0}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

export default function Validation({ summary, reload }) {
  const metrics = summary?.metrics || {};
  const real = summary?.validation || {};
  const calibration = summary?.calibration || {};
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">DATASET & VALIDATION</span>
        <h1>Separate reference data from proof.</h1>
        <p>FreshFusion only reports validation metrics from human ground truth paired with a verified system decision. Published reference labels never count as system accuracy.</p>
        <button className="secondary" onClick={reload}>Refresh validation</button>
      </div>

      {!summary && <div className="notice">Backend required. No validation result is assumed while the validation source is unavailable.</div>}

      <div className="twoPanels">
        <Panel title="FreshFusion validation data">
          <Facts items={[
            ["Labelled camera images", summary?.labelled_images],
            ["Human-labelled inspections", summary?.human_labelled_inspections],
            ["Ground-truth review records", summary?.human_ground_truth_records],
            ["Matched evaluation pairs", real?.sample_count],
            ["Unmatched ground truth", real?.unmatched_ground_truth],
            ["Claim readiness", summary ? (summary.claim_ready ? "Validation data available" : "Not ready for accuracy claims") : "Unknown"],
            ["Model deployment", summary ? titleCase(summary.model?.status) : "Unknown"],
            ["Reference index", summary ? (summary.reference_index?.ready ? "Available" : "Not built") : "Unknown"],
          ]}/>
          <p className="footnote">{summary?.label_policy}</p>
          <p className="footnote">{summary?.split_policy}</p>
          <p className="footnote">{real?.claim_policy}</p>
        </Panel>

        <Panel title="Validation metrics">
          <div className="metricPlaceholders">
            <Metric name="Accuracy" metric={metrics.accuracy}/>
            <Metric name="Precision" metric={metrics.precision}/>
            <Metric name="Recall" metric={metrics.recall}/>
            <Metric name="F1" metric={metrics.f1}/>
            <Metric name="Confusion Matrix" metric={metrics.confusion_matrix}/>
          </div>
          <p className="footnote">Status: <b>{real?.status || "NOT YET VALIDATED"}</b>. Metrics remain preliminary until the minimum ground-truth coverage policy is satisfied.</p>
        </Panel>
      </div>

      <Panel title="Fruit calibration readiness" eyebrow="FRESHFUSION CHAMBER DATA ONLY">
        <div className="ffPerClassGrid">
          {["Apple", "Banana", "Tomato"].map((fruit) => {
            const readiness = calibration?.fruit_readiness?.[fruit] || {};
            const counts = readiness.class_counts || {};
            return (
              <div key={fruit} className="ffPerClassCard">
                <b>{fruit}</b>
                <StatusChip tone={readiness.ready ? "good" : "neutral"}>{readiness.ready ? "BAND DATA READY" : "COLLECT MORE DATA"}</StatusChip>
                <span>Fresh {counts.fresh ?? 0}</span>
                <span>Ripe {counts.ripe ?? 0}</span>
                <span>Overripe {counts.overripe ?? 0}</span>
                <span>Spoiled {counts.spoiled ?? 0}</span>
                <small>Target: {calibration?.minimum_samples_per_class ?? 5}+ labelled inspections per class</small>
              </div>
            );
          })}
        </div>
        <p className="footnote">{calibration?.note || "No labelled calibration data collected yet. FreshFusion will not invent universal gas thresholds."}</p>
      </Panel>

      <Panel title="Confusion matrix"><ConfusionMatrix value={metrics.confusion_matrix?.value}/></Panel>

      {real?.per_class && (
        <Panel title="Per-class performance">
          <div className="ffPerClassGrid">
            {Object.entries(real.per_class).map(([label, row]) => (
              <div key={label} className="ffPerClassCard"><b>{titleCase(label)}</b><span>Precision {pct(row.precision)}</span><span>Recall {pct(row.recall)}</span><span>F1 {pct(row.f1)}</span><small>Support {row.support}</small></div>
            ))}
          </div>
        </Panel>
      )}

      {real?.fruit_breakdown && Object.keys(real.fruit_breakdown).length > 0 && (
        <Panel title="Fruit-wise evaluation">
          <div className="ffPerClassGrid">
            {Object.entries(real.fruit_breakdown).map(([fruit, row]) => <div key={fruit} className="ffPerClassCard"><b>{fruit}</b><span>Accuracy {pct(row.accuracy)}</span><small>{row.correct}/{row.total} matched</small></div>)}
          </div>
        </Panel>
      )}

      <div className="twoPanels">
        {summary?.datasets?.map((dataset) => (
          <Panel key={dataset.id} title={dataset.name} eyebrow={titleCase(dataset.purpose)}>
            <Facts items={[["License (source metadata)", dataset.license],["Supported reference fruits", dataset.supports.join(", ")],["Published classes", dataset.labels?.join(", ") || "Fruit identity classes"]]}/>
            <p>{dataset.note}</p><a href={dataset.url} target="_blank" rel="noreferrer">Open dataset source</a>
          </Panel>
        ))}
      </div>

      <Panel title="Collection protocol">
        <p>Give every physical fruit a stable specimen ID, keep all views and repeated inspections of that specimen in the same split, record empty-chamber baseline and sensor readings, then add human Fresh / Ripe / Overripe / Spoiled ground truth independently from the system prediction.</p>
      </Panel>
    </div>
  );
}
