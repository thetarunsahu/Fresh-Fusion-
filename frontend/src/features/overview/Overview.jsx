import { ArrowRight, Camera, Cpu, Database, Plus, Store } from "lucide-react";
import { Panel, StatusChip } from "../../shared/Panel";

export default function Overview({ session, onStart, navigate, validation }) {
  const evidence = session.report?.evidence;
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">START HERE</span>
        <h1>From fruit measurements to an actionable quality decision.</h1>
        <p>
          FreshFusion combines camera evidence, chamber sensors and reference
          evidence, challenges the result, and then translates the assessment
          into a simple operator action.
        </p>
        <div className="buttonRow">
          <button
            className="primary"
            onClick={onStart}
            disabled={session.busy || !session.online}
          >
            <Plus size={16} /> Start new inspection
          </button>
          <button className="secondary" onClick={() => navigate("operator")}>
            <Store size={15} /> Open operator view
          </button>
        </div>
      </div>
      {!session.online && (
        <div className="notice">
          <b>
            Explore the workflow now. Connect the backend to collect evidence.
          </b>
          <p>
            The frontend works on its own for orientation; no demonstration data
            is generated. Run <code>.\start_freshfusion.ps1</code> from the
            repository root for the complete phone + ESP32 system, or follow the
            README for separate backend startup.
          </p>
        </div>
      )}
      <div className="sourceGrid">
        {[
          [
            Camera,
            "Phone camera",
            "Three changed views for color, texture, visible defects and view consistency",
          ],
          [
            Cpu,
            "ESP32 sensors",
            "Temperature, humidity and uncalibrated MQ135 raw / relative response",
          ],
          [
            Database,
            "Reference evidence",
            "Cached feature similarity to published classes; similarity is not accuracy",
          ],
        ].map(([Icon, title, note]) => (
          <Panel key={title} title={title}>
            <Icon size={25} />
            <p>{note}</p>
          </Panel>
        ))}
      </div>
      <Panel
        title="The product workflow"
        eyebrow="HOW EVIDENCE BECOMES AN ACTION"
      >
        <div className="flowStages">
          {[
            ["01", "Intake", "Create one inspection per physical fruit."],
            [
              "02",
              "Collect evidence",
              "Capture 3 changed views and current chamber readings.",
            ],
            ["03", "Independent analysis", "Vision · Sensor · Reference · Multi-view"],
            [
              "04",
              "Evidence critic",
              "Check missing, inconsistent, stale or suspicious evidence.",
            ],
            [
              "05",
              "Decision",
              "Release an experimental result only when evidence is eligible.",
            ],
            [
              "06",
              "Operator action",
              "Translate the result into sale, storage, reinspection or rejection guidance.",
            ],
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
          The proactive assistant explains backend evidence and recommendations;
          it does not independently decide freshness. Internal texture is not
          measured by the current prototype.
        </p>
      </Panel>
      <div className="twoPanels">
        <Panel title="Current prototype status">
          <div className="connectionList">
            {[
              ["Backend", session.online],
              ["Camera · selected inspection", evidence?.camera?.recent],
              [
                "ESP32 · recent physical data",
                evidence?.sensors?.physical_present,
              ],
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
        <Panel title="Supported now">
          <div className="chipRow">
            <StatusChip>Apple</StatusChip>
            <StatusChip>Banana</StatusChip>
            <StatusChip>Tomato · manual selection</StatusChip>
            <StatusChip tone="warning">Experimental prototype</StatusChip>
          </div>
          <p>
            Automatic identity is currently optimized for Apple and Banana.
            Tomato can be selected manually for inspection, but fruit-specific
            reference ranges and validated quality thresholds still require real
            data collection. Raw gas is not ppm, and physical-fruit checks are
            probabilistic.
          </p>
          <button
            className="secondary"
            onClick={() => navigate("operator")}
          >
            See the operator decision <ArrowRight size={15} />
          </button>
        </Panel>
      </div>
    </div>
  );
}
