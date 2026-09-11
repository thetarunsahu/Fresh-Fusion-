import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import WorkspaceLayout from "./layout/WorkspaceLayout";
import useInspection from "./hooks/useInspection";
import Overview from "./features/overview/Overview";
import OperatorDashboard from "./features/operator/OperatorDashboard";
import LiveInspection from "./features/inspection/LiveInspection";
import Investigation from "./features/investigation/Investigation";
import EvidenceTimeline from "./features/evidence/EvidenceTimeline";
import Validation from "./features/validation/Validation";
import History from "./features/history/History";
import { fuse, validationSummary } from "./api";
import { StatusChip } from "./shared/Panel";
import "./workspace.css";

const routes = new Set([
  "overview",
  "operator",
  "inspection",
  "investigation",
  "evidence",
  "validation",
  "history",
]);
const currentPage = () =>
  routes.has(location.hash.slice(1)) ? location.hash.slice(1) : "overview";

export default function App() {
  const [page, setPage] = useState(currentPage);
  const [fruit, setFruit] = useState("Auto");
  const [validation, setValidation] = useState(null);
  const session = useInspection(page === "inspection");
  const navigate = (id) => {
    location.hash = id;
    setPage(id);
    window.scrollTo(0, 0);
  };
  useEffect(() => {
    const change = () => setPage(currentPage());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  const loadValidation = useCallback(async () => {
    try {
      setValidation(await validationSummary());
    } catch {
      setValidation(null);
    }
  }, []);
  useEffect(() => {
    if (session.online) loadValidation();
    else setValidation(null);
  }, [session.online, page, loadValidation]);
  const start = async () => {
    if (await session.create(fruit)) navigate("inspection");
  };
  const recompute = async () => {
    try {
      await fuse(session.sample.sample_id);
      await session.refresh();
    } catch (error) {
      session.setErr(error.message);
    }
  };
  const isActive = session.sample?.sample_id === session.active?.sample_id;
  const toolbar = (
    <>
      <div className="selectedInspection">
        <span className="eyebrow">SELECTED INSPECTION</span>
        <b>
          {session.sample
            ? `${session.sample.fruit_type} · ${session.sample.sample_id}`
            : "No inspection selected"}
        </b>
        <StatusChip tone={session.online ? "good" : "neutral"}>
          {session.online ? "Backend online" : "Backend disconnected"}
        </StatusChip>
      </div>
      <div className="toolbarActions">
        <label className="srOnly" htmlFor="new-fruit">
          Fruit for new inspection
        </label>
        <select
          id="new-fruit"
          value={fruit}
          onChange={(e) => setFruit(e.target.value)}
        >
          <option value="Auto">Auto identity</option>
          <option>Apple</option>
          <option>Banana</option>
          <option>Tomato</option>
        </select>
        <button
          className="primary"
          onClick={start}
          disabled={!session.online || session.busy}
        >
          <Plus size={15} /> New inspection
        </button>
        <button
          className="secondary"
          disabled={!session.online || !session.sample}
          onClick={recompute}
        >
          <RefreshCw size={15} /> Recompute
        </button>
      </div>
    </>
  );
  return (
    <WorkspaceLayout page={page} navigate={navigate} toolbar={toolbar}>
      {session.err && (
        <div role="alert" className="workspaceError">
          {session.err}
        </div>
      )}
      {session.sample && page !== "overview" && (
        <div className="captureBanner">
          <span>
            {isActive
              ? `Capture target: ${session.active?.sample_id}`
              : `Reviewing history. Capture target remains ${session.active?.sample_id || "unselected"}.`}
          </span>
          {!isActive && (
            <button
              className="secondary"
              onClick={session.activate}
              disabled={!session.online}
            >
              Use this inspection for capture
            </button>
          )}
          <a
            href={`/phone.html${session.sample ? `?sample_id=${encodeURIComponent(session.sample.sample_id)}` : ""}`}
            target="_blank"
            rel="noreferrer"
          >
            Open phone camera page
          </a>
        </div>
      )}
      {page === "overview" && (
        <Overview
          session={session}
          onStart={start}
          navigate={navigate}
          validation={validation}
        />
      )}
      {page === "operator" && (
        <OperatorDashboard session={session} navigate={navigate} />
      )}
      {page === "inspection" && (
        <LiveInspection
          key={session.sample?.sample_id || "none"}
          session={session}
        />
      )}
      {page === "investigation" && <Investigation session={session} />}
      {page === "evidence" && (
        <EvidenceTimeline
          key={session.sample?.sample_id || "none"}
          report={session.report}
        />
      )}
      {page === "validation" && (
        <Validation summary={validation} reload={loadValidation} />
      )}
      {page === "history" && (
        <History
          samples={session.recent}
          onOpen={(sample, destination) => {
            session.selectSample(sample);
            navigate(destination);
          }}
        />
      )}
    </WorkspaceLayout>
  );
}
