import { useMemo, useState } from "react";
import {
  Camera,
  ChevronDown,
  MessageCircle,
  ShieldAlert,
  Sparkles,
  Thermometer,
  Droplets,
  Gauge,
  Eye,
  Wifi,
  WifiOff,
  Activity,
  CheckCircle2,
} from "lucide-react";
import CameraStream from "../../components/CameraStream";
import { captureSensorBaseline } from "../../api";
import "./product-live-inspection.css";

const fmt = (value, digits = 0) =>
  value == null || Number.isNaN(Number(value)) ? "--" : Number(value).toFixed(digits);

const title = (value) =>
  String(value || "")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

const currentViews = ["front", "left", "right"];

function actionFor(label, ready) {
  if (!ready) return { action: "Collect more evidence", risk: "Pending", tone: "pending" };
  const key = String(label || "").toLowerCase();
  if (key.includes("spoiled")) return { action: "Remove / reject", risk: "High", tone: "danger" };
  if (key.includes("overripe")) return { action: "Quick sale / processing", risk: "High", tone: "warning" };
  if (key.includes("ripe")) return { action: "Priority sale", risk: "Moderate", tone: "attention" };
  if (key.includes("fresh")) return { action: "Normal sale / storage", risk: "Low", tone: "good" };
  return { action: "Inspect again", risk: "Unknown", tone: "pending" };
}

function assistantMessage({
  ready,
  label,
  viewsCount,
  sensorPresent,
  critic,
  fruit,
  sensor,
}) {
  if (sensor?.warmup?.ready === false) {
    return {
      severity: "warning",
      changed: "The gas sensor is still warming up.",
      meaning: "Its current reading should not be used as reliable fruit evidence yet.",
      action: "Keep the chamber empty and wait until the sensor is ready.",
    };
  }
  if (sensor?.health?.stuck_signal?.suspected) {
    return {
      severity: "critical",
      changed: "The MQ135 signal has barely changed across several recent readings.",
      meaning: "The sensor may be stuck or the measurement setup may need checking.",
      action: "Check the sensor connection and chamber airflow, then collect fresh readings.",
    };
  }
  if (viewsCount < 3) {
    return {
      severity: "warning",
      changed: `Only ${viewsCount}/3 views are available.`,
      meaning: "There is not enough visual evidence to confirm the fruit condition yet.",
      action: "Capture the remaining view before relying on the result.",
    };
  }
  if (!sensorPresent) {
    return {
      severity: "warning",
      changed: "The camera evidence is available, but fresh sensor evidence is missing.",
      meaning: "The system cannot complete a reliable multimodal assessment yet.",
      action: "Wait for a fresh ESP32 reading and keep the fruit in the chamber.",
    };
  }
  if (!sensor?.baseline?.available) {
    return {
      severity: "info",
      changed: "No empty-chamber MQ135 baseline has been recorded for this inspection.",
      meaning: "FreshFusion can show the raw gas value, but it cannot yet show how far it has moved from your chamber baseline.",
      action: "Before inserting the fruit, record at least three empty-chamber baseline readings.",
    };
  }
  if (sensor?.baseline?.stable === false) {
    return {
      severity: "warning",
      changed: "The empty-chamber baseline is changing too much between readings.",
      meaning: "A moving baseline can make fruit-to-baseline comparisons misleading.",
      action: "Purge the chamber, keep it empty, and record a new stable baseline set.",
    };
  }
  if (critic?.blocking || critic?.status === "BLOCKED") {
    return {
      severity: "warning",
      changed: "The evidence check found a conflict or missing requirement.",
      meaning: "FreshFusion is holding the final result until the evidence is consistent.",
      action: "Follow the highlighted evidence request, then inspect again.",
    };
  }
  if (!ready) {
    return {
      severity: "info",
      changed: "Evidence is still being verified.",
      meaning: "The system does not have enough verified information for a final assessment.",
      action: "Keep the fruit steady and allow the camera and sensors to finish collecting evidence.",
    };
  }
  const state = title(label || "current condition");
  const recommendation = actionFor(label, true).action;
  const trend = sensor?.trend?.direction;
  const trendText = trend === "rising"
    ? " The gas-response trend is rising."
    : trend === "falling"
      ? " The gas-response trend is falling."
      : trend === "stable"
        ? " The recent gas-response trend is stable."
        : "";
  return {
    severity: "info",
    changed: `${fruit || "This fruit"} is currently assessed as ${state}.${trendText}`,
    meaning: "The result is based on the verified camera, sensor and supporting evidence available now.",
    action: `${recommendation}. Re-inspect if the fruit remains in storage and its condition changes.`,
  };
}

function SmallChip({ icon: Icon, label, value }) {
  return (
    <div className="ffEvidenceChip">
      <Icon size={14} />
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

export default function ProductLiveInspection({ session }) {
  const { sample, data, report, online, active, onFrame, refresh, setErr } = session;
  const [truth, setTruth] = useState("");
  const [baselineBusy, setBaselineBusy] = useState(false);
  const [baselineMessage, setBaselineMessage] = useState("");
  const latest = data.sensors?.at(-1) || {};
  const latestImage = data.images?.[0] || null;
  const decision = report?.decision || {};
  const critic = report?.critic || {};
  const evidence = report?.evidence || {};
  const analysts = report?.analysts || {};
  const multiview = analysts.multiview || {};
  const vision = analysts.vision || {};
  const sensor = analysts.sensor || {};
  const reading = sensor.latest || latest || {};
  const views = multiview.views || evidence?.camera?.views || [];
  const viewsCount = Math.min(3, new Set(views).size || data.images?.filter((x) => currentViews.includes(x.angle)).length || 0);
  const sensorPresent = evidence?.sensors?.physical_present === true || sensor.eligible_readings > 0;
  const ready = decision.verdict_ready === true;
  const label = decision.label || data.fusion?.label;
  const fruit = vision.identity?.fruit || (sample?.fruit_type !== "Auto" ? sample?.fruit_type : null) || "Fruit";
  const action = actionFor(label, ready);
  const captureActive = sample?.sample_id && active?.sample_id === sample.sample_id;
  const score = ready ? decision.freshness_score ?? data.fusion?.freshness_score : null;
  const visibleDamage = vision.defects?.visible_damage_estimate_pct;
  const evidenceQuality = sensor?.health?.evidence_quality?.level || "unknown";
  const gasDelta = sensor?.baseline_delta_raw;
  const trend = sensor?.trend || {};
  const warmup = sensor?.warmup || reading?.warmup || {};

  const frameFor = (view) =>
    data.images?.find((img) => img.angle === view || img.angle === `live-${view}`);

  const assistant = useMemo(
    () => assistantMessage({ ready, label, viewsCount, sensorPresent, critic, fruit, sensor }),
    [ready, label, viewsCount, sensorPresent, critic, fruit, sensor],
  );

  const captureBaseline = async () => {
    if (!sample?.sample_id || baselineBusy) return;
    setBaselineBusy(true);
    setBaselineMessage("");
    try {
      const result = await captureSensorBaseline(sample.sample_id);
      setBaselineMessage(result?.instruction || "Empty-chamber baseline reading stored.");
      await refresh();
    } catch (error) {
      setErr(error.message);
    } finally {
      setBaselineBusy(false);
    }
  };

  return (
    <div className="ffProductInspection">
      <section className={`ffHero ${action.tone}`}>
        <div className="ffHeroMain">
          <span className="ffEyebrow">LIVE FRUIT INSPECTION</span>
          <h1>{title(fruit)}</h1>
          <div className="ffDecisionRow">
            <div>
              <span>Current condition</span>
              <strong>{ready ? title(label) : "Verification in progress"}</strong>
            </div>
            <div>
              <span>Recommended action</span>
              <strong>{action.action}</strong>
            </div>
            <div>
              <span>Risk</span>
              <strong>{action.risk}</strong>
            </div>
            <div>
              <span>Usable-life estimate</span>
              <strong>Not yet calibrated</strong>
            </div>
          </div>
          <p className="ffHeroReason">
            {decision.reason || critic.warnings?.[0] || "FreshFusion is collecting and checking evidence before releasing a result."}
          </p>
          <div className="ffChipRow">
            <SmallChip icon={Thermometer} label="Temp" value={`${fmt(reading.temperature, 1)}°C`} />
            <SmallChip icon={Droplets} label="Humidity" value={`${fmt(reading.humidity, 0)}%`} />
            <SmallChip icon={Gauge} label="MQ135" value={fmt(reading.mq135_raw, 0)} />
            <SmallChip icon={Activity} label="Gas Δ" value={gasDelta == null ? "No baseline" : `${gasDelta >= 0 ? "+" : ""}${fmt(gasDelta, 0)}`} />
            <SmallChip icon={Eye} label="Damage" value={visibleDamage == null ? "--" : `${fmt(visibleDamage, 0)}%`} />
            <SmallChip icon={Camera} label="Views" value={`${viewsCount}/3`} />
            <SmallChip icon={sensorPresent ? Wifi : WifiOff} label="ESP32" value={sensorPresent ? "Ready" : "Waiting"} />
            <SmallChip icon={CheckCircle2} label="Evidence" value={title(evidenceQuality)} />
          </div>
        </div>
        <div className="ffScoreCard">
          <span>Evidence score</span>
          <strong>{score == null ? "--" : Math.round(score)}</strong>
          <small>{score == null ? "Released after evidence checks" : "/100 · calibration pending"}</small>
        </div>
      </section>

      <section className="ffLiveGrid">
        <div className="ffCameraPanel ffPanel">
          <div className="ffPanelHeader">
            <div>
              <span className="ffEyebrow">CAMERA</span>
              <h2>Current fruit view</h2>
            </div>
            <span className={`ffLiveBadge ${latestImage ? "on" : ""}`}>{latestImage ? "LIVE" : "WAITING"}</span>
          </div>
          <div className="ffMainFrame">
            {latestImage ? (
              <img src={latestImage.url} alt="Current fruit" />
            ) : (
              <div className="ffEmptyFrame"><Camera size={34} /><b>No image yet</b><span>Connect the phone camera and capture the fruit.</span></div>
            )}
          </div>
          <div className="ffThreeViews">
            {currentViews.map((view) => {
              const frame = frameFor(view);
              return (
                <div className="ffViewCard" key={view}>
                  {frame ? <img src={frame.url} alt={`${view} view`} /> : <div className="ffViewEmpty">+</div>}
                  <span>{title(view)}</span>
                </div>
              );
            })}
          </div>
          {captureActive && (
            <details className="ffCaptureFallback">
              <summary>Use this computer camera / upload fallback</summary>
              <CameraStream sampleId={sample?.sample_id} groundTruth={truth} onFrame={onFrame} />
              <label>
                Optional ground truth
                <select value={truth} onChange={(e) => setTruth(e.target.value)}>
                  <option value="">Unlabelled</option>
                  <option value="fresh">Fresh</option>
                  <option value="ripe">Ripe</option>
                  <option value="overripe">Overripe</option>
                  <option value="spoiled">Spoiled</option>
                </select>
              </label>
            </details>
          )}
        </div>

        <aside className="ffAssistant ffPanel">
          <div className="ffAssistantTitle">
            <div className="ffAssistantIcon"><Sparkles size={18} /></div>
            <div><span className="ffEyebrow">PROACTIVE ASSISTANT · {title(assistant.severity)}</span><h2>FreshFusion Assistant</h2></div>
          </div>
          <div className="ffAssistantMessage">
            <div><b>What changed?</b><p>{assistant.changed}</p></div>
            <div><b>What does it mean?</b><p>{assistant.meaning}</p></div>
            <div className="ffNextAction"><b>What should you do?</b><p>{assistant.action}</p></div>
          </div>
          <div className="ffAssistantFacts">
            <span><MessageCircle size={14} /> Updates automatically as evidence changes.</span>
            <span><ShieldAlert size={14} /> Internal quality is not measured with the current sensing setup.</span>
          </div>
          <div className="ffAskBox">
            <input placeholder="Ask about this fruit..." disabled />
            <button disabled>Ask</button>
          </div>
          <small className="ffMuted">Live guidance updates automatically from the current inspection evidence.</small>
        </aside>
      </section>

      <section className="ffEvidencePanel ffPanel">
        <details open>
          <summary><span><ChevronDown size={16} /> Sensor baseline & health</span><small>Measurement status</small></summary>
          <div className="ffTechnicalGrid">
            <div><span>Warm-up</span><b>{title(warmup.state || "unknown")}</b></div>
            <div><span>Baseline samples</span><b>{sensor?.baseline?.count ?? 0}</b></div>
            <div><span>Baseline mean</span><b>{sensor?.baseline?.mq135_raw_mean == null ? "Not recorded" : `${fmt(sensor.baseline.mq135_raw_mean, 0)} ADC`}</b></div>
            <div><span>Gas delta</span><b>{gasDelta == null ? "Not available" : `${gasDelta >= 0 ? "+" : ""}${fmt(gasDelta, 0)} ADC`}</b></div>
            <div><span>Gas trend</span><b>{title(trend.direction || "insufficient data")}</b></div>
            <div><span>Evidence quality</span><b>{title(evidenceQuality)}</b></div>
          </div>
          <div className="ffBaselineAction">
            <div>
              <b>Empty-chamber baseline</b>
              <p>Remove the fruit, let the chamber settle, then record the current physical ESP32 reading. Capture at least three readings to check baseline stability.</p>
            </div>
            <button className="secondary" onClick={captureBaseline} disabled={!sample?.sample_id || baselineBusy || !online}>
              {baselineBusy ? "Recording..." : "Record empty-chamber baseline"}
            </button>
          </div>
          {baselineMessage && <p className="ffBaselineMessage">{baselineMessage}</p>}
          <small className="ffMuted">Baseline values are local chamber references, not universal Apple/Banana/Tomato standards.</small>
        </details>
      </section>

      <section className="ffEvidencePanel ffPanel">
        <details>
          <summary><span><ChevronDown size={16} /> Technical evidence</span><small>Detailed measurement data</small></summary>
          <div className="ffTechnicalGrid">
            <div><span>Temperature</span><b>{fmt(reading.temperature, 1)}°C</b></div>
            <div><span>Humidity</span><b>{fmt(reading.humidity, 0)}%</b></div>
            <div><span>MQ135 raw</span><b>{fmt(reading.mq135_raw, 0)} ADC</b></div>
            <div><span>Recent views</span><b>{viewsCount}/3</b></div>
            <div><span>Evidence check</span><b>{title(critic.status || "waiting")}</b></div>
            <div><span>System connection</span><b>{online ? "Online" : "Offline"}</b></div>
            <div><span>Signal health</span><b>{sensor?.health?.stuck_signal?.suspected ? "Check sensor" : sensor?.health?.stuck_signal?.checked ? "No issue seen" : "Need more readings"}</b></div>
            <div><span>Baseline stability</span><b>{sensor?.baseline?.stable == null ? "Need 3+ baselines" : sensor.baseline.stable ? "Stable" : "Unstable"}</b></div>
            <div><span>Trend rate</span><b>{trend.raw_per_minute == null ? "--" : `${fmt(trend.raw_per_minute, 1)} ADC/min`}</b></div>
          </div>
          <div className="ffTechnicalNotes">
            <p><b>MQ135:</b> shown as raw / relative evidence only, not calibrated ppm.</p>
            <p><b>Internal quality:</b> not measured with the current camera + DHT11 + MQ135 sensing setup.</p>
            <p><b>Usable life:</b> shown only after calibration with labelled time-series data.</p>
          </div>
        </details>
      </section>
    </div>
  );
}
