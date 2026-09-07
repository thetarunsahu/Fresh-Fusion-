import { useState } from "react";
import { assetUrl } from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";
import { dateTime } from "../../shared/format";

export default function EvidenceTimeline({ report }) {
  const [kind, setKind] = useState("all");
  const events = (report?.timeline || []).filter(
    (row) => kind === "all" || row.kind === kind,
  );
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">EVIDENCE</span>
        <h1>Follow the inspection record.</h1>
        <p>
          Measurements, saved analysis and human observations in time order.
          Events come from stored records; missing stages are never invented.
        </p>
      </div>
      <Panel title="Evidence timeline">
        <div className="buttonRow">
          <label>
            Filter events{" "}
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {[
                "all",
                "intake",
                "camera",
                "vision",
                "sensor",
                "reference",
                "fusion",
                "human",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <StatusChip>{events.length} recorded events</StatusChip>
        </div>
        <p className="footnote">
          {report?.timeline_note ||
            "Select an inspection to load its recorded evidence."}
        </p>
        <ol className="evidenceTimeline">
          {events.map((row) => (
            <li key={row.id}>
              <div className="timelineMarker" />
              <time>{dateTime(row.at)}</time>
              <div>
                <StatusChip>{row.kind}</StatusChip>
                <h3>{row.title}</h3>
                <p>{row.detail}</p>
                {row.image_url && (
                  <a
                    href={assetUrl(row.image_url)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open evidence image
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>
        {!events.length && (
          <div className="emptyState">
            No recorded events for this selection. Start collecting evidence in
            Live Inspection.
          </div>
        )}
      </Panel>
    </div>
  );
}
