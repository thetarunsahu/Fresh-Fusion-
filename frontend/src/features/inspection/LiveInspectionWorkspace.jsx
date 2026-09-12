import ProductLiveInspection from "./ProductLiveInspection";
import InspectionAssistant from "./InspectionAssistant";
import IdentityConfirmBar from "./IdentityConfirmBar";
import P0InspectionPanel from "./P0InspectionPanel";
import LiveInspection from "./LiveInspection";
import "./live-inspection-workspace.css";

const fmt = (value, digits = 0) =>
  value == null || Number.isNaN(Number(value)) ? "--" : Number(value).toFixed(digits);

function proactiveFromReport(session) {
  const report = session.report || {};
  const product = report.product || {};
  const decision = report.decision || {};
  const critic = report.critic || {};
  const vision = report.analysts?.vision || {};
  const sensor = report.analysts?.sensor || {};
  const multiview = report.analysts?.multiview || {};
  const fruit = product.fruit || session.sample?.fruit_type || "fruit";
  const score = decision.verdict_ready
    ? decision.freshness_score
    : product.provisional_quality_score ?? product.score_breakdown?.provisional_score;
  const damage = vision.defects?.visible_damage_estimate_pct;
  const reading = sensor.latest || {};
  const gasDelta = sensor.baseline_delta_raw;
  const viewsCount = multiview.views_count ?? (multiview.views || []).length ?? 0;
  const latestEvent = (product.events || []).find((event) => ["critical", "warning"].includes(event.severity));

  if (latestEvent) {
    return {
      severity: latestEvent.severity,
      changed: latestEvent.message,
      meaning: `${fruit} currently has ${score == null ? "no released score yet" : `${Math.round(score)}/100 ${decision.verdict_ready ? "final" : "provisional"} quality`}. Visible surface damage: ${damage == null ? "not available" : `${fmt(damage)}%`}.`,
      action: product.recommendation?.action || "Review the highlighted evidence before taking action.",
    };
  }

  if (!decision.verdict_ready) {
    const sensorBits = [];
    if (reading.temperature != null) sensorBits.push(`${fmt(reading.temperature, 1)}°C`);
    if (reading.humidity != null) sensorBits.push(`${fmt(reading.humidity)}% RH`);
    if (reading.mq135_raw != null) sensorBits.push(`MQ135 ${fmt(reading.mq135_raw)} ADC`);
    if (gasDelta != null) sensorBits.push(`Δ ${gasDelta >= 0 ? "+" : ""}${fmt(gasDelta)} ADC`);
    return {
      severity: critic.blocking ? "warning" : "info",
      changed: `${fruit}: ${score == null ? "quality score is still forming" : `provisional quality ${Math.round(score)}/100`}; ${viewsCount}/3 views verified${damage == null ? "" : `; visible damage ${fmt(damage)}%`}.`,
      meaning: `${sensorBits.length ? `Current chamber evidence: ${sensorBits.join(", ")}. ` : ""}${decision.reason || "The final assessment is still being verified."}`,
      action: viewsCount < 3
        ? `Fruit identity can work from one camera view; capture ${3 - viewsCount} more changed view${3 - viewsCount === 1 ? "" : "s"} only to strengthen surface coverage and physical verification.`
        : product.recommendation?.action || "Complete the remaining evidence check shown above.",
    };
  }

  return {
    severity: "info",
    changed: `${fruit} is verified as ${String(decision.label || "unknown").replaceAll("-", " ")} with score ${Math.round(decision.freshness_score ?? score ?? 0)}/100.`,
    meaning: `Visible damage ${damage == null ? "not available" : `${fmt(damage)}%`}; ${viewsCount}/3 views; ${reading.mq135_raw == null ? "no MQ135 reading" : `MQ135 ${fmt(reading.mq135_raw)} ADC${gasDelta == null ? "" : ` (${gasDelta >= 0 ? "+" : ""}${fmt(gasDelta)} vs baseline)`}`}.`,
    action: product.recommendation?.action || "Continue monitoring if the fruit remains in storage.",
  };
}

export default function LiveInspectionWorkspace({ session }) {
  return (
    <>
      <IdentityConfirmBar session={session} />
      <ProductLiveInspection session={session} />

      <section className="ffAssistantUpgrade">
        <div className="ffAssistantUpgradeHead">
          <span>INTERACTIVE ASSISTANT</span>
          <h2>Ask about this inspection</h2>
          <p>Ask why the score changed, what the camera sees, what MQ135 means, what evidence is missing, or what action to take next.</p>
        </div>
        <InspectionAssistant session={session} proactive={proactiveFromReport(session)} />
      </section>

      <P0InspectionPanel session={session} />

      <section className="ffRestoredEvidence">
        <div className="ffRestoredEvidenceHeader">
          <div>
            <span>DETAILED ANALYSIS</span>
            <h2>Inspection evidence and measurements</h2>
            <p>
              Open the detailed analysis when you want to review sensor trends, phone pairing,
              reference data, image analysis, colour, texture and observation details.
            </p>
          </div>
        </div>

        <details className="ffRestoredDetails">
          <summary>Open detailed analysis</summary>
          <div className="ffLegacyEvidenceOnly">
            <LiveInspection session={session} />
          </div>
        </details>
      </section>
    </>
  );
}
