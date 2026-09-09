import {
  ArrowRight,
  Bot,
  Camera,
  Plus,
  ScanSearch,
  ShieldCheck,
} from "lucide-react";
import { StatusChip } from "../../shared/Panel";
import { fmt, titleCase } from "../../shared/format";

function stateLabel(ok, online) {
  if (ok) return "Ready";
  return online ? "Waiting" : "Offline";
}

function MetricCard({ label, value, note, tone = "good" }) {
  return (
    <article className="ffMetricCard">
      <div className="ffMetricHead">
        <span>{label}</span>
        <i className={`ffMetricDot ${tone}`} aria-hidden="true" />
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

export default function Overview({ session, onStart, navigate, validation }) {
  const report = session.report;
  const evidence = report?.evidence;
  const cameraRecent = evidence?.camera?.recent === true;
  const sensorRecent = evidence?.sensors?.physical_present === true;
  const storedImage = session.data?.images?.[0] || null;
  const latestImage = cameraRecent ? storedImage : null;
  const storedSensor = session.data?.sensors?.at(-1) || {};
  const latestSensor = sensorRecent ? storedSensor : {};
  const vision = report?.analysts?.vision || {};
  const multi = report?.analysts?.multiview || {};
  const decision = report?.decision || {};
  const critic = report?.critic || {};
  const capturedViews = multi.views || [];
  const fruit =
    cameraRecent && vision.identity?.fruit && vision.identity.fruit !== "Unknown"
      ? vision.identity.fruit
      : session.sample?.fruit_type && session.sample.fruit_type !== "Auto"
        ? session.sample.fruit_type
        : "Waiting";

  const signals = [
    ["Camera evidence", cameraRecent],
    ["ESP32 telemetry", sensorRecent],
    ["Reference index", Boolean(validation?.reference_index?.ready)],
    ["RAG context", Boolean(report)],
  ];

  const metricCards = [
    [
      "Temperature",
      latestSensor.temperature == null ? "—" : `${fmt(latestSensor.temperature)} °C`,
      latestSensor.temperature == null ? "Waiting for recent hardware" : "Recent physical reading",
      latestSensor.temperature == null ? "neutral" : "good",
    ],
    [
      "Humidity",
      latestSensor.humidity == null ? "—" : `${fmt(latestSensor.humidity)}% RH`,
      latestSensor.humidity == null ? "Waiting for recent DHT11 data" : "Recent chamber state",
      latestSensor.humidity == null ? "neutral" : "good",
    ],
    [
      "MQ135 raw",
      latestSensor.mq135_raw == null ? "—" : `${fmt(latestSensor.mq135_raw, 0)} ADC`,
      latestSensor.mq135_raw == null ? "Waiting for recent hardware" : "Uncalibrated relative signal",
      latestSensor.mq135_raw == null ? "neutral" : "warning",
    ],
    ["Fruit identity", fruit, cameraRecent ? "Recent vision evidence" : "Selected inspection / waiting for camera", fruit === "Waiting" ? "neutral" : "good"],
    [
      "Assessment",
      decision.verdict_ready ? titleCase(decision.label) : "More evidence",
      decision.verdict_ready ? "Experimental assessment" : "Verdict currently locked",
      decision.verdict_ready ? "good" : "warning",
    ],
  ];

  const analystRows = [
    ["Vision Analyst", "Surface + identity", cameraRecent && vision.identity?.confidence != null ? `${fmt(vision.identity.confidence, 0)}%` : "Waiting"],
    ["Sensor Analyst", "Temp / RH / MQ135", sensorRecent ? "Valid" : "Waiting"],
    ["Reference Analyst", "Retrieved class context", report?.analysts?.reference?.index?.ready ? "Ready" : "Waiting"],
    ["Multi-view Analyst", "Physical consistency", `${capturedViews.length} / ${multi.required_views ?? 3}`],
  ];

  return (
    <div className="featurePage overviewPage ffOverviewPage">
      <div className="ffPageHeading">
        <span className="eyebrow">OVERVIEW</span>
        <h1>FreshFusion Investigation Workspace</h1>
      </div>

      <section className="ffOverviewHero">
        <div className="ffOverviewHeroCopy">
          <span className="eyebrow">EVIDENCE-GROUNDED MULTIMODAL INSPECTION</span>
          <h2>Inspect the fruit.<br />Challenge the evidence.</h2>
          <p>
            Phone vision, chamber telemetry, reference retrieval and deterministic
            critique before any experimental freshness assessment is released.
          </p>
          <div className="buttonRow">
            <button className="primary" onClick={onStart} disabled={session.busy || !session.online}>
              <Plus size={16} /> New inspection
            </button>
            <button className="secondary" onClick={() => navigate("investigation")}>
              <ScanSearch size={15} /> Explore investigation
            </button>
          </div>
        </div>
        <div className="ffReadinessCard">
          <div className="ffReadinessHead">
            <div>
              <span className="eyebrow">SYSTEM READINESS</span>
              <strong>{session.online ? "FreshFusion online" : "Backend required"}</strong>
            </div>
            <StatusChip tone={session.online ? "good" : "neutral"}>
              {session.online ? "CONNECTED" : "OFFLINE"}
            </StatusChip>
          </div>
          <div className="ffReadinessRows">
            {signals.map(([label, ok]) => (
              <div key={label}>
                <span>{label}</span>
                <b className={ok ? "ready" : "waiting"}>{stateLabel(ok, session.online)}</b>
              </div>
            ))}
          </div>
        </div>
      </section>

      {!session.online && (
        <div className="notice ffInlineNotice">
          No demonstration measurements are generated. Start the backend to collect real evidence.
        </div>
      )}

      <section className="ffMetricGrid">
        {metricCards.map(([label, value, note, tone]) => (
          <MetricCard key={label} label={label} value={value} note={note} tone={tone} />
        ))}
      </section>

      <section className="ffOverviewMainGrid">
        <article className="workspacePanel ffVisualCard">
          <span className="eyebrow">VISUAL EVIDENCE</span>
          <h2>What the camera sees now</h2>
          <div className="ffVisualBody">
            <div className="ffCameraPreview">
              {latestImage?.url ? (
                <img src={latestImage.url} alt="Current recent fruit evidence" />
              ) : (
                <div className="ffCameraEmpty">
                  <Camera size={28} />
                  <b>{storedImage?.url ? "Camera is not streaming" : "No current camera frame"}</b>
                  <span>
                    {storedImage?.url
                      ? "A stored frame exists, but it is hidden here so stale evidence is never presented as live. Open History & Evidence to review it."
                      : "Start a new inspection and capture a real view from the phone camera."}
                  </span>
                </div>
              )}
            </div>
            <div className="ffViewList">
              {["front", "left", "right", "back", "top"].map((view) => {
                const captured = capturedViews.includes(view);
                return (
                  <div key={view} className={captured ? "captured" : "needed"}>
                    <b>{titleCase(view)}</b>
                    <span>{captured ? (cameraRecent ? "captured" : "stored") : "needed"}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </article>

        <article className="workspacePanel ffAnalystSummary">
          <span className="eyebrow">INTELLIGENCE LAYERS</span>
          <h2>Independent analysis before fusion</h2>
          <div className="ffAnalystRows">
            {analystRows.map(([name, note, value]) => (
              <div key={name}>
                <span><b>{name}</b><small>{note}</small></span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="ffOverviewBottomGrid">
        <article className="workspacePanel ffCriticSummary">
          <div>
            <span className="eyebrow">EVIDENCE CRITIC</span>
            <h2>{critic.blocking ? "Verdict blocked — more physical evidence required" : "Evidence gate ready for assessment"}</h2>
            <p>{critic.missing_evidence?.length ? `Missing: ${critic.missing_evidence.join(" · ")}` : critic.warnings?.join(" · ") || "No recorded blocker for the selected inspection."}</p>
          </div>
          <StatusChip tone={critic.blocking ? "warning" : "good"}>
            {critic.blocking ? "MORE EVIDENCE" : "GATE PASSED"}
          </StatusChip>
        </article>

        <button className="ffCopilotTeaser" onClick={() => navigate("ai")}>
          <div>
            <Bot size={18} />
            <b>FreshFusion AI Copilot</b>
          </div>
          <p>Ask why a verdict is locked, what evidence is missing, or what the sensors contributed.</p>
          <div className="ffCopilotBadges">
            <span>Gemma 3</span><span>Ollama local</span><span>Evidence-grounded</span>
          </div>
        </button>
      </section>

      <div className="ffScopeNote">
        <ShieldCheck size={15} />
        <span>Experimental prototype · MQ135 remains raw/relative · Gemma explains evidence but does not decide the verdict.</span>
        <button className="textButton" onClick={() => navigate("system")}>System boundaries <ArrowRight size={13} /></button>
      </div>
    </div>
  );
}
