import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { titleCase } from "../../shared/format";

export default function Validation({ summary, reload }) {
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">DATASET & VALIDATION</span>
        <h1>Keep references separate from proof.</h1>
        <p>
          Published data provides a comparison baseline. FreshFusion needs
          independent, labelled chamber observations before reporting validated
          performance.
        </p>
        <button className="secondary" onClick={reload}>
          Refresh dataset status
        </button>
      </div>
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
              ["Reference classes", summary?.reference_index?.classes],
            ]}
          />
          <p className="footnote">{summary?.label_policy}</p>
          <p className="footnote">{summary?.model?.note}</p>
        </Panel>
        <Panel title="Validation metrics">
          <div className="metricPlaceholders">
            {["Accuracy", "Precision", "Recall", "F1", "Confusion Matrix"].map(
              (name) => (
                <div key={name}>
                  <span>{name}</span>
                  <StatusChip>NOT YET VALIDATED</StatusChip>
                </div>
              ),
            )}
          </div>
          <p className="footnote">
            No held-out FreshFusion evaluation is available. Split by physical
            fruit/sample, not neighbouring camera frames; evaluate vision-only,
            sensor-only and fusion on the same test set.
          </p>
        </Panel>
      </div>
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
      <Panel title="Next validation work">
        <p>
          This page is ready for a teammate to add a labelling review queue,
          sample-based split manifests and real held-out evaluation reports.
          Keep every metric tied to its dataset version, protocol and test
          samples.
        </p>
      </Panel>
    </div>
  );
}
