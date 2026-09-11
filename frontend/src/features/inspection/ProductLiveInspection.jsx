import { useMemo, useState } from "react";
import { Camera, ChevronDown, MessageCircle, ShieldAlert, Sparkles, Thermometer, Droplets, Gauge, Eye, Wifi, WifiOff } from "lucide-react";
import CameraStream from "../../components/CameraStream";
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

function assistantMessage({ ready, label, viewsCount, sensorPresent, critic, fruit }) {
  if (viewsCount < 3) {
    return {
      changed: `Only ${viewsCount}/3 views are available.`,
      meaning: "There is not enough visual evidence to confirm the fruit condition yet.",
      action: "Capture the remaining view before relying on the result.",
    };
  }
  if (!sensorPresent) {
    return {
      changed: "The camera evidence is available, but fresh sensor evidence is missing.",
      meaning: "The system cannot complete a reliable multimodal assessment yet.",
      action: "Wait for a fresh ESP32 reading and keep the fruit in the chamber.",
    };
  }
  if (critic?.blocking || critic?.status === "BLOCKED") {
    return {
      changed: "The evidence check found a conflict or missing requirement.",
      meaning: "FreshFusion is deliberately holding the final result instead of guessing.",
      action: "Follow the highlighted evidence request, then inspect again.",
    };
  }
  if (!ready) {
    return {
      changed: "Evidence is still being verified.",
      meaning: "The system does not have enough verified information for a final assessment.",
      action: "Keep the fruit steady and allow the camera and sensors to finish collecting evidence.",
    };
  }
  const state = title(label || "current condition");
  const recommendation = actionFor(label, true).action;
  return {
    changed: `${fruit || "This fruit"} is currently assessed as ${state}.`,
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
  const { sample, data, report, online, active, onFrame } = session;
  const [truth, setTruth] = useState("");
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

  const frameFor = (view) =>
    data.images?.find((img) => img.angle === view || img.angle === `live-${view}`);

  const assistant = useMemo(
    () => assistantMessage({ ready, label, viewsCount, sensorPresent, critic, fruit }),
    [ready, label, viewsCount, sensorPresent, critic, fruit],
  );

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
            <SmallChip icon={Eye} label="Damage" value={visibleDamage == null ? "--" : `${fmt(visibleDamage, 0)}%`} />
            <SmallChip icon={Camera} label="Views" value={`${viewsCount}/3`} />
            <SmallChip icon={sensorPresent ? Wifi : WifiOff} label="ESP32" value={sensorPresent ? "Ready" : "Waiting"} />
          </div>
        </div>
        <div className="ffScoreCard">
          <span>Evidence score</span>
          <strong>{score == null ? "--" : Math.round(score)}</strong>
          <small>{score == null ? "Released only after evidence checks" : "/100 experimental"}</small>
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
            <div><span className="ffEyebrow">PROACTIVE ASSISTANT</span><h2>FreshFusion Assistant</h2></div>
          </div>
          <div className="ffAssistantMessage">
            <div><b>What changed?</b><p>{assistant.changed}</p></div>
            <div><b>What does it mean?</b><p>{assistant.meaning}</p></div>
            <div className="ffNextAction"><b>What should you do?</b><p>{assistant.action}</p></div>
          </div>
          <div className="ffAssistantFacts">
            <span><MessageCircle size={14} /> Updates automatically as evidence changes.</span>
            <span><ShieldAlert size={14} /> Internal quality is not measured in the current prototype.</span>
          </div>
          <div className="ffAskBox">
            <input placeholder="Ask about this fruit..." disabled />
            <button disabled>Ask</button>
          </div>
          <small className="ffMuted">Interactive Q&A is the next assistant layer; current messages are evidence-driven and proactive.</small>
        </aside>
      </section>

      <section className="ffEvidencePanel ffPanel">
        <details>
          <summary><span><ChevronDown size={16} /> Technical evidence</span><small>For jury / QA / engineering review</small></summary>
          <div className="ffTechnicalGrid">
            <div><span>Temperature</span><b>{fmt(reading.temperature, 1)}°C</b></div>
            <div><span>Humidity</span><b>{fmt(reading.humidity, 0)}%</b></div>
            <div><span>MQ135 raw</span><b>{fmt(reading.mq135_raw, 0)} ADC</b></div>
            <div><span>Recent views</span><b>{viewsCount}/3</b></div>
            <div><span>Evidence critic</span><b>{title(critic.status || "waiting")}</b></div>
            <div><span>Backend</span><b>{online ? "Online" : "Offline"}</b></div>
          </div>
          <div className="ffTechnicalNotes">
            <p><b>MQ135:</b> shown as raw / relative evidence only, not calibrated ppm.</p>
            <p><b>Internal quality:</b> not measured by the current camera + DHT11 + MQ135 prototype.</p>
            <p><b>Usable life:</b> intentionally not estimated until a labelled time-series dataset supports it.</p>
          </div>
        </details>
      </section>
    </div>
  );
}
