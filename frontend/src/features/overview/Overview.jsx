import {
  ArrowRight,
  Camera,
  Cpu,
  Database,
  Plus,
  ScanSearch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Panel, StatusChip } from "../../shared/Panel";

function signalState(ok, online) {
  if (ok) return "Ready";
  return online ? "Waiting" : "Offline";
}

export default function Overview({ session, onStart, navigate, validation }) {
  const evidence = session.report?.evidence;
  const signals = [
    ["Camera evidence", evidence?.camera?.recent],
    ["ESP32 telemetry", evidence?.sensors?.physical_present],
    ["Reference index", validation?.reference_index?.ready],
  ];

  return (
    <div className="featurePage overviewPage">
      <section className="overviewHero">
        <div className="overviewHeroCopy">
          <div className="heroKicker">
            <Sparkles size={15} />
            <span>Evidence-grounded multimodal inspection</span>
          </div>
          <span className="eyebrow">START HERE</span>
          <h1>From a fruit to an evidence-backed assessment.</h1>
          <p>
            FreshFusion combines phone vision, chamber telemetry, published
            references and an evidence critic before it releases an experimental
            freshness assessment.
          </p>
          <div className="heroActions">
            <button
              className="primary heroPrimary"
              onClick={onStart}
              disabled={session.busy || !session.online}
            >
              <Plus size={17} /> Start new inspection
            </button>
            <button
              className="secondary heroSecondary"
              onClick={() => navigate("investigation")}
            >
              <ScanSearch size={16} /> Explore investigation
            </button>
          </div>
          <div className="heroTrustRow">
            <span><ShieldCheck size={14} /> Deterministic gating</span>
            <span>Human verification</span>
            <span>Local Gemma explanation</span>
          </div>
        </div>

        <div className="overviewHeroVisual" aria-label="FreshFusion system readiness">
          <div className="heroVisualGlow" />
          <div className="heroVisualHeader">
            <div>
              <span className="eyebrow">SYSTEM READINESS</span>
              <strong>{session.online ? "FreshFusion online" : "Backend required"}</strong>
            </div>
            <StatusChip tone={session.online ? "good" : "neutral"}>
              {session.online ? "CONNECTED" : "OFFLINE"}
            </StatusChip>
          </div>

          <div className="signalOrbit">
            <div className="orbitCore">
              <span>FF</span>
              <small>Investigation</small>
            </div>
            <div className="orbitRing orbitRingOne" />
            <div className="orbitRing orbitRingTwo" />
          </div>

          <div className="heroSignalList">
            {signals.map(([label, ok]) => (
              <div key={label}>
                <span>{label}</span>
                <b className={ok ? "ready" : "waiting"}>
                  {signalState(ok, session.online)}
                </b>
              </div>
            ))}
          </div>
        </div>
      </section>

      {!session.online && (
        <div className="notice premiumNotice">
          <b>Explore the workflow now. Connect the backend to collect evidence.</b>
          <p>
            No demonstration measurements are generated. Run
            <code>.\start_freshfusion.ps1</code> from the repository root for the
            complete phone + ESP32 system.
          </p>
        </div>
      )}

      <div className="sourceGrid premiumSourceGrid">
        {[
          [Camera, "Phone camera", "Visual evidence", "Color, texture, defects and changed physical viewpoints", "cameraSource"],
          [Cpu, "ESP32 sensors", "Environmental evidence", "Temperature, humidity and uncalibrated MQ135 raw response", "sensorSource"],
          [Database, "Public reference", "Context evidence", "Local feature similarity against published reference classes", "referenceSourceCard"],
        ].map(([Icon, title, eyebrow, note, className]) => (
          <Panel key={title} title={title} eyebrow={eyebrow} className={`sourcePanel ${className}`}>
            <div className="sourceIcon"><Icon size={22} /></div>
            <p>{note}</p>
          </Panel>
        ))}
      </div>

      <Panel
        title="The investigation workflow"
        eyebrow="HOW EVIDENCE BECOMES AN ASSESSMENT"
        className="workflowPanel"
      >
        <div className="flowStages">
          {[
            ["01", "Intake", "One inspection per physical fruit."],
            ["02", "Collect", "Changed views + fresh chamber readings."],
            ["03", "Analyze", "Vision · Sensor · Reference · Multi-view"],
            ["04", "Challenge", "Critic checks missing, stale and conflicting evidence."],
            ["05", "Decide", "Deterministic fusion releases or blocks responsibly."],
            ["06", "Verify", "Human accepts, disagrees or adds ground truth."],
          ].map(([n, title, note], i) => (
            <div className="flowStage" key={n}>
              <span>{n}</span>
              <h3>{title}</h3>
              <p>{note}</p>
              {i < 5 && <ArrowRight size={16} />}
            </div>
          ))}
        </div>
        <p className="footnote">
          Core decision modules remain deterministic. Gemma is used only for
          structured human-readable explanation, not for the numerical verdict.
        </p>
      </Panel>

      <div className="twoPanels overviewBottomGrid">
        <Panel title="Current prototype status" eyebrow="LIVE SOURCES" className="statusPanel">
          <div className="connectionList">
            {[
              ["Backend", session.online],
              ["Camera · selected inspection", evidence?.camera?.recent],
              ["ESP32 · recent physical data", evidence?.sensors?.physical_present],
              ["Reference index", validation?.reference_index?.ready],
            ].map(([label, ok]) => (
              <div key={label}>
                <span>{label}</span>
                <StatusChip tone={ok ? "good" : "neutral"}>
                  {ok
                    ? "Available"
                    : session.online
                      ? "Waiting / unavailable"
                      : "Backend required"}
                </StatusChip>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Prototype scope" eyebrow="SUPPORTED NOW" className="scopePanel">
          <div className="chipRow">
            <StatusChip>Apple</StatusChip>
            <StatusChip>Banana</StatusChip>
            <StatusChip tone="warning">Experimental prototype</StatusChip>
          </div>
          <p>
            Identity uses OpenCV rules and reference features. MQ135 is raw
            relative evidence, reference similarity is not accuracy, and
            monocular physical verification remains probabilistic.
          </p>
          <button className="secondary" onClick={() => navigate("investigation")}>
            Explore the analysts <ArrowRight size={15} />
          </button>
        </Panel>
      </div>
    </div>
  );
}
