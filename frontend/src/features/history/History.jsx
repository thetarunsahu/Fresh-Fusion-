import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { dateTime, titleCase } from "../../shared/format";

const PAGE_SIZE = 8;

export default function History({ samples, onOpen }) {
  const [query, setQuery] = useState("");
  const [fruit, setFruit] = useState("all");
  const [verdict, setVerdict] = useState("all");
  const [reviewed, setReviewed] = useState("all");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);

  const fruits = useMemo(
    () => [...new Set(samples.map((sample) => sample.fruit_type).filter(Boolean))].sort(),
    [samples],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = samples.filter((sample) => {
      if (fruit !== "all" && sample.fruit_type !== fruit) return false;
      if (verdict === "released" && !sample.last_recorded_verdict_ready) return false;
      if (verdict === "locked" && sample.last_recorded_verdict_ready) return false;
      if (reviewed === "reviewed" && !(sample.human_review_count > 0)) return false;
      if (reviewed === "unreviewed" && sample.human_review_count > 0) return false;
      if (!needle) return true;
      return [
        sample.sample_id,
        sample.fruit_type,
        sample.status,
        sample.verification_state,
        sample.latest_ground_truth,
        sample.last_review_action,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
    rows.sort((a, b) => {
      const left = new Date(a.created_at || 0).getTime();
      const right = new Date(b.created_at || 0).getTime();
      return sort === "oldest" ? left - right : right - left;
    });
    return rows;
  }, [samples, query, fruit, verdict, reviewed, sort]);

  useEffect(() => setPage(1), [query, fruit, verdict, reviewed, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">HISTORY</span>
        <h1>Every inspection keeps its evidence.</h1>
        <p>
          Search previous samples without changing the chamber's active capture
          target. Historical verdicts describe stored state; reopening an
          investigation rechecks current evidence age.
        </p>
      </div>

      <Panel title="Find inspections" eyebrow={`${filtered.length} OF ${samples.length} SHOWN`}>
        <div className="historyToolbar">
          <label className="filterField searchField">
            <span>Search</span>
            <div className="inputWithIcon">
              <Search size={15} />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Sample ID, fruit, status, ground truth..."
              />
            </div>
          </label>
          <label className="filterField">
            <span>Fruit</span>
            <select value={fruit} onChange={(e) => setFruit(e.target.value)}>
              <option value="all">All fruits</option>
              {fruits.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
          <label className="filterField">
            <span>Verdict</span>
            <select value={verdict} onChange={(e) => setVerdict(e.target.value)}>
              <option value="all">All verdict states</option>
              <option value="released">Released</option>
              <option value="locked">Locked / incomplete</option>
            </select>
          </label>
          <label className="filterField">
            <span>Human review</span>
            <select value={reviewed} onChange={(e) => setReviewed(e.target.value)}>
              <option value="all">All review states</option>
              <option value="reviewed">Reviewed</option>
              <option value="unreviewed">Not reviewed</option>
            </select>
          </label>
          <label className="filterField">
            <span>Sort</span>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
          </label>
        </div>
      </Panel>

      <div className="historyGrid">
        {visible.map((sample) => (
          <Panel
            key={sample.sample_id}
            title={sample.fruit_type}
            eyebrow={sample.sample_id}
          >
            <div className="historyCardTopline">
              <p>{dateTime(sample.created_at)}</p>
              <div className="chipRow">
                <StatusChip>{titleCase(sample.status)}</StatusChip>
                {sample.human_review_count > 0 && (
                  <StatusChip tone="good">{sample.human_review_count} human review{sample.human_review_count === 1 ? "" : "s"}</StatusChip>
                )}
              </div>
            </div>
            <Facts
              items={[
                ["Stored camera frames", sample.camera_frames],
                ["Sensor readings", sample.sensor_readings],
                ["Last physical check", titleCase(sample.verification_state)],
                [
                  "Last recorded verdict",
                  sample.last_recorded_verdict_ready
                    ? "Released (historical)"
                    : "Locked / not assessed",
                ],
                ["Human ground truth", titleCase(sample.latest_ground_truth) || "Not supplied"],
                ["Last reviewed", dateTime(sample.last_reviewed_at)],
                ["Last assessed", dateTime(sample.last_assessed_at)],
              ]}
            />
            <div className="buttonRow">
              <button
                className="primary"
                onClick={() => onOpen(sample, "investigation")}
              >
                Open investigation
              </button>
              <button
                className="secondary"
                onClick={() => onOpen(sample, "evidence")}
              >
                View evidence
              </button>
            </div>
          </Panel>
        ))}
      </div>

      {filtered.length > PAGE_SIZE && (
        <div className="paginationBar" aria-label="History pagination">
          <button
            className="secondary"
            disabled={safePage <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            Previous
          </button>
          <span>Page {safePage} of {pageCount}</span>
          <button
            className="secondary"
            disabled={safePage >= pageCount}
            onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
          >
            Next
          </button>
        </div>
      )}

      {!samples.length && (
        <Panel title="No inspections loaded">
          <p>
            Connect the backend and start an inspection. History shows persisted
            records, not demonstration samples.
          </p>
        </Panel>
      )}
      {samples.length > 0 && !filtered.length && (
        <Panel title="No matching inspections">
          <p>Change the filters or search text to see other persisted inspections.</p>
        </Panel>
      )}
    </div>
  );
}
