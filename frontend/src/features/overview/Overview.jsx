import { ArrowRight, Camera, Cpu, Database, Plus } from "lucide-react";
import { Panel, StatusChip } from "../../shared/Panel";

export default function Overview({ session, onStart, navigate, validation }) {
  const evidence = session.report?.evidence;
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">START HERE</span>
        <h1>From a fruit to an evidence-backed assessment.</h1>
        <p>
          FreshFusion investigates fruit quality using phone images, chamber
          sensors and published visual references. Follow the evidence,
          challenge the hypothesis, then record a human observation.
        </p>
        <button
          className="primary"
          onClick={onStart}
          disabled={session.busy || !session.online}
        >
          <Plus size={16} /> Start new inspection
        </button>
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
            "Color, texture, visible defects and changed views",
          ],
          [
            Cpu,
            "ESP32 sensors",
            "Temperature, humidity and uncalibrated MQ135 raw",
          ],
          [
            Database,
            "Public reference",
            "Cached feature similarity to published classes",
          ],
        ].map(([Icon, title, note]) => (
          <Panel key={title} title={title}>
            <Icon size={25} />
            <p>{note}</p>
          </Panel>
        ))}
      </div>
      <Panel
        title="The investigation workflow"
        eyebrow="HOW EVIDENCE BECOMES AN ASSESSMENT"
      >
        <div className="flowStages">
          {[
            ["01", "Intake", "Create one inspection per physical fruit."],
            [
              "02",
              "Collect evidence",
              "Capture changed views and current chamber readings.",
            ],
            ["03", "Four analysts", "Vision · Sensor · Reference · Multi-view"],
            [
              "04",
              "Evidence critic",
              "Check missing, inconsistent and stale evidence.",
            ],
            [
              "05",
              "Fusion / confidence",
              "Release an experimental result only when eligible.",
            ],
            [
              "06",
              "Human verification",
              "Accept, disagree or add independent ground truth.",
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
          These are deterministic software modules. An LLM explanation layer is
          future work; no LLM agents or trained identity model are claimed.
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
            <StatusChip tone="warning">Experimental prototype</StatusChip>
          </div>
          <p>
            Identity uses OpenCV rules and reference features. Raw gas is not
            ppm, similarity is not accuracy, and physical-fruit checks are
            probabilistic.
          </p>
          <button
            className="secondary"
            onClick={() => navigate("investigation")}
          >
            Explore the analysts <ArrowRight size={15} />
          </button>
        </Panel>
      </div>
    </div>
  );
}
