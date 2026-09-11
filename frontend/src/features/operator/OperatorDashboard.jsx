import { AlertTriangle, Bot, ChevronRight, Eye, PackageCheck } from "lucide-react";
import { Panel, StatusChip } from "../../shared/Panel";
import { evidenceMetrics, operatorGuidance, proactiveMessages } from "./operatorGuidance";
import "./operator.css";

export default function OperatorDashboard({ session, navigate }) {
  const report = session.report;
  const fruit = session.sample?.fruit_type || "Fruit";
  const decision = report?.decision || {};
  const guidance = operatorGuidance(report);
  const metrics = evidenceMetrics(report);
  const assistant = proactiveMessages(report, fruit);
  const score = decision?.verdict_ready && decision.freshness_score != null
    ? Math.round(Number(decision.freshness_score))
    : null;

  return (
    <div className="featurePage operatorPage">
      <div className="pageIntro operatorIntro">
        <span className="eyebrow">OPERATOR VIEW</span>
        <h1>What should I do with this fruit?</h1>
        <p>
          FreshFusion shows the decision first, then keeps the technical evidence visible in a smaller supporting layer.
        </p>
      </div>

      {!session.sample && (
        <div className="notice">
          Start or select an inspection. Operator guidance appears only when real evidence is available.
        </div>
      )}

      <div className="operatorHero">
        <section className={`decisionCard ${guidance.tone}`}>
          <div className="decisionTopline">
            <span>{fruit}</span>
            <StatusChip tone={decision.verdict_ready ? "good" : "warning"}>
              {decision.verdict_ready ? "ASSESSMENT READY" : "NOT CONFIRMED"}
            </StatusChip>
          </div>

          <div className="decisionMain">
            <div>
              <span className="decisionLabel">QUALITY STATUS</span>
              <h2>{guidance.status}</h2>
            </div>
            {score != null && (
              <div className="compactScore" title="Experimental evidence score; not a validated freshness percentage">
                <strong>{score}</strong>
                <span>/100</span>
              </div>
            )}
          </div>

          <div className="operatorActionGrid">
            <div>
              <span>ACTION</span>
              <b>{guidance.action}</b>
            </div>
            <div>
              <span>RISK</span>
              <b>{guidance.risk}</b>
            </div>
            <div>
              <span>ESTIMATED USABLE LIFE</span>
              <b>{guidance.sellWindow}</b>
            </div>
          </div>

          <div className="decisionReason">
            <b>Why?</b>
            <p>{guidance.reason}</p>
          </div>

          <div className="microMetrics" aria-label="Technical evidence summary">
            {metrics.map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <b>{value}</b>
              </div>
            ))}
          </div>

          <div className="buttonRow operatorButtons">
            <button className="secondary" onClick={() => navigate("investigation")}> 
              <Eye size={15} /> Why this result?
            </button>
            <button className="secondary" onClick={() => navigate("evidence")}> 
              Full evidence <ChevronRight size={15} />
            </button>
          </div>
        </section>

        <aside className="assistantRail">
          <div className="assistantHeading">
            <Bot size={20} />
            <div>
              <b>FreshFusion Assistant</b>
              <span>Proactive guidance</span>
            </div>
          </div>

          <div className="assistantMessages">
            {assistant.map((item, index) => (
              <div className={`assistantMessage ${item.level}`} key={`${item.title}-${index}`}>
                <div className="assistantMessageTitle">
                  {item.level === "critical" ? <AlertTriangle size={15} /> : <PackageCheck size={15} />}
                  <b>{item.title}</b>
                </div>
                <p>{item.text}</p>
              </div>
            ))}
          </div>

          <p className="assistantBoundary">
            The assistant explains and recommends actions from backend evidence. It does not independently decide freshness.
          </p>
        </aside>
      </div>

      <Panel title="Current prototype boundaries" eyebrow="TRUTHFUL PRODUCT STATUS">
        <div className="operatorBoundaryGrid">
          <div>
            <b>3-view visual workflow</b>
            <p>Current prototype expects three changed views, not five cameras.</p>
          </div>
          <div>
            <b>Internal texture</b>
            <p>Not measured by the present camera + DHT11 + MQ135 prototype.</p>
          </div>
          <div>
            <b>MQ135</b>
            <p>Shown as raw/relative response. Fruit-specific calibrated ranges still require controlled data collection.</p>
          </div>
          <div>
            <b>Usable-life estimate</b>
            <p>Kept uncalibrated until a real longitudinal dataset supports fruit-specific time estimates.</p>
          </div>
        </div>
      </Panel>
    </div>
  );
}
