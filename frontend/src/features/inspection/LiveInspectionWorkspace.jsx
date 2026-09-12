import ProductLiveInspection from "./ProductLiveInspection";
import InspectionAssistant from "./InspectionAssistant";
import P0InspectionPanel from "./P0InspectionPanel";
import LiveInspection from "./LiveInspection";
import "./live-inspection-workspace.css";

function proactiveFromReport(session) {
  const report = session.report || {};
  const product = report.product || {};
  const decision = report.decision || {};
  const critic = report.critic || {};
  const latestEvent = (product.events || []).find((event) => ["critical", "warning"].includes(event.severity));
  if (latestEvent) {
    return {
      severity: latestEvent.severity,
      changed: latestEvent.message,
      meaning: "FreshFusion recorded this change as part of the inspection history.",
      action: product.recommendation?.action || "Review the latest evidence before taking action.",
    };
  }
  if (!decision.verdict_ready) {
    return {
      severity: critic.blocking ? "warning" : "info",
      changed: decision.reason || "The assessment is still being verified.",
      meaning: "FreshFusion will not force a final result while required evidence is missing or conflicting.",
      action: "Complete the evidence request shown above, then inspect again.",
    };
  }
  return {
    severity: "info",
    changed: `Current verified condition: ${String(decision.label || "unknown").replaceAll("-", " ")}.`,
    meaning: "The result uses the currently verified visual, sensor and supporting evidence.",
    action: product.recommendation?.action || "Continue monitoring if the fruit remains in storage.",
  };
}

export default function LiveInspectionWorkspace({ session }) {
  return (
    <>
      <ProductLiveInspection session={session} />

      <section className="ffAssistantUpgrade">
        <div className="ffAssistantUpgradeHead">
          <span>INTERACTIVE ASSISTANT</span>
          <h2>Ask about this inspection</h2>
          <p>Ask why FreshFusion produced the current result, what changed, which evidence is missing, or what action to take next.</p>
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
