import { useMemo, useState } from "react";
import { Download, Search } from "lucide-react";
import { assetUrl } from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";
import { dateTime } from "../../shared/format";

const EVENT_KINDS = [
  "all",
  "intake",
  "camera",
  "vision",
  "sensor",
  "reference",
  "fusion",
  "human",
];

function safeFilePart(value) {
  return String(value || "inspection").replace(/[^a-z0-9_-]+/gi, "-");
}

function downloadText(filename, text, type) {
  const blob = new Blob([text], { type });
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(href);
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

export default function EvidenceTimeline({ report }) {
  const [kind, setKind] = useState("all");
  const [query, setQuery] = useState("");
  const [imagesOnly, setImagesOnly] = useState(false);
  const [oldestFirst, setOldestFirst] = useState(false);
  const allEvents = report?.timeline || [];

  const events = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = allEvents.filter((row) => {
      if (kind !== "all" && row.kind !== kind) return false;
      if (imagesOnly && !row.image_url) return false;
      if (!needle) return true;
      return [row.kind, row.title, row.detail, row.at]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
    return oldestFirst ? [...filtered].reverse() : filtered;
  }, [allEvents, kind, query, imagesOnly, oldestFirst]);

  const exportJson = () => {
    const payload = {
      inspection_id: report?.inspection_id || null,
      exported_at: new Date().toISOString(),
      filters: { kind, query, images_only: imagesOnly, oldest_first: oldestFirst },
      event_count: events.length,
      events,
    };
    downloadText(
      `${safeFilePart(report?.inspection_id)}-evidence.json`,
      JSON.stringify(payload, null, 2),
      "application/json",
    );
  };

  const exportCsv = () => {
    const lines = [
      ["id", "timestamp", "kind", "title", "detail", "image_url"]
        .map(csvCell)
        .join(","),
      ...events.map((row) =>
        [row.id, row.at, row.kind, row.title, row.detail, row.image_url || ""]
          .map(csvCell)
          .join(","),
      ),
    ];
    downloadText(
      `${safeFilePart(report?.inspection_id)}-evidence.csv`,
      lines.join("\r\n"),
      "text/csv;charset=utf-8",
    );
  };

  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">EVIDENCE</span>
        <h1>Follow the inspection record.</h1>
        <p>
          Search, filter and export stored measurements, analysis events and human
          observations. Exported files contain recorded events only; missing
          evidence is never invented.
        </p>
      </div>
      <Panel title="Evidence timeline" eyebrow={report?.inspection_id || "NO INSPECTION SELECTED"}>
        <div className="evidenceToolbar">
          <label className="filterField searchField">
            <span>Search evidence</span>
            <div className="inputWithIcon">
              <Search size={15} />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="sensor, front, review, conflict..."
              />
            </div>
          </label>
          <label className="filterField">
            <span>Event type</span>
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {EVENT_KINDS.map((x) => (
                <option key={x} value={x}>
                  {x === "all" ? "All events" : x}
                </option>
              ))}
            </select>
          </label>
          <label className="filterCheck">
            <input
              type="checkbox"
              checked={imagesOnly}
              onChange={(e) => setImagesOnly(e.target.checked)}
            />
            Images only
          </label>
          <label className="filterCheck">
            <input
              type="checkbox"
              checked={oldestFirst}
              onChange={(e) => setOldestFirst(e.target.checked)}
            />
            Oldest first
          </label>
        </div>

        <div className="evidenceSummaryBar">
          <div className="chipRow">
            <StatusChip>{events.length} shown</StatusChip>
            <StatusChip>{allEvents.length} total recorded</StatusChip>
          </div>
          <div className="buttonRow">
            <button className="secondary" onClick={exportCsv} disabled={!events.length}>
              <Download size={14} /> Export CSV
            </button>
            <button className="secondary" onClick={exportJson} disabled={!events.length}>
              <Download size={14} /> Export JSON
            </button>
          </div>
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
                    className="evidenceImageLink"
                    href={assetUrl(row.image_url)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <img src={assetUrl(row.image_url)} alt="Stored inspection evidence" />
                    <span>Open full evidence image</span>
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>
        {!events.length && (
          <div className="emptyState">
            {allEvents.length
              ? "No evidence matches the current filters."
              : "No recorded events for this inspection yet."}
          </div>
        )}
      </Panel>
    </div>
  );
}
