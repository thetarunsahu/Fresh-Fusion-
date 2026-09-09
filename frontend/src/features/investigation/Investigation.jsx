import { Activity, Database, Eye, Layers3, ShieldCheck } from "lucide-react";
import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { fmt, titleCase } from "../../shared/format";
import HumanVerification from "./HumanVerification";
import GemmaExplanation from "./GemmaExplanation";

function AnalystLead({ Icon, title, note }) {
  return (
    <div className="analystLead">
      <span className="analystLeadIcon"><Icon size={17} /></span>
      <div><b>{title}</b><small>{note}</small></div>
    </div>
  );
}

function Bucket({ title, items, tone }) {
  return (
    <div className={`ffCriticRow ${tone || ""}`}>
      <span>{title}</span>
      <b>{items?.length ? items.join(" · ") : "None recorded"}</b>
    </div>
  );
}

export default function Investigation({ session }) {
  const report = session.report;
  const { vision = {}, sensor = {}, reference = {}, multiview = {} } = report?.analysts || {};
  const reading = sensor.latest || {};
  const match = reference.match || {};
  const agreement = report?.agreement;
  const critic = report?.critic;
  const decision = report?.decision;
  const agreementTone = agreement?.status === "ALIGNED" ? "good" : agreement?.status === "CONFLICTING" ? "warning" : "neutral";

  const analystPanels = [
    {
      key: "vision",
      title: "Vision Analyst",
      eyebrow: "OPENCV / HEURISTICS",
      Icon: Eye,
      lead: "Visual condition",
      note: "Identity, visible surface condition and image quality",
      items: [
        ["Detected fruit", vision.identity?.fruit],
        ["Identity confidence", vision.identity?.confidence == null ? "Not available" : `${fmt(vision.identity.confidence)}%`],
        ["Usable recent images", vision.usable_images],
        ["Healthy surface", vision.healthy_surface_estimate_pct == null ? "Not available" : `${fmt(vision.healthy_surface_estimate_pct)}%`],
        ["Visible damage", vision.defects?.visible_damage_estimate_pct == null ? "Not available" : `${fmt(vision.defects.visible_damage_estimate_pct)}%`],
        ["Freshness model", titleCase(vision.ai?.status)],
      ],
      foot: "Surface estimates can be affected by lighting, shadows and background.",
    },
    {
      key: "sensor",
      title: "Sensor Analyst",
      eyebrow: "DETERMINISTIC",
      Icon: Activity,
      lead: "Chamber telemetry",
      note: "Physical hardware evidence and recency checks",
      items: [
        ["Temperature", reading.temperature == null ? "Not available" : `${fmt(reading.temperature)} °C`],
        ["Humidity", reading.humidity == null ? "Not available" : `${fmt(reading.humidity)}% RH`],
        ["MQ135 raw", reading.mq135_raw == null ? "Not available" : `${fmt(reading.mq135_raw, 0)} ADC`],
        ["Relative response", fmt(reading.relative_gas_response, 4)],
        ["Declared source", reading.source],
        ["Eligible readings", sensor.eligible_readings],
      ],
      foot: sensor.note || "Uncalibrated 12-bit electrical response, not ppm. Simulator data cannot unlock the verdict.",
    },
    {
      key: "reference",
      title: "Reference Analyst",
      eyebrow: "LOCAL PUBLIC INDEX",
      Icon: Database,
      lead: "Published context",
      note: "Nearest reference examples without claiming probability",
      items: [
        ["Dataset", match.source?.name || reference.index?.source?.name],
        ["Nearest class", match.match],
        ["Similarity", match.similarity == null ? "Not available" : `${fmt(match.similarity)}%`],
        ["Reference samples", match.reference_samples],
        ["Indexed examples", reference.index?.samples],
        ["Index state", reference.index?.ready ? "Available" : report ? "Not built" : "Unknown"],
      ],
      foot: "Similarity is context, not model accuracy or probability.",
    },
    {
      key: "multiview",
      title: "Multi-view Analyst",
      eyebrow: "PHYSICAL EVIDENCE",
      Icon: Layers3,
      lead: "Physical consistency",
      note: "Changed viewpoints, identity consistency and presentation checks",
      items: [
        ["Captured views", multiview.views?.join(", ") || "None"],
        ["Required", `${multiview.required_views ?? 3} minimum`],
        ["Physical status", titleCase(multiview.status)],
        ["Screen suspicion", multiview.screen_suspicion_pct == null ? "Not available" : `${fmt(multiview.screen_suspicion_pct)}%`],
        ["Appearance diversity", multiview.appearance_diversity_pct == null ? "Not available" : `${fmt(multiview.appearance_diversity_pct)}%`],
        ["Identity consistency", multiview.identity_consistency_pct == null ? "Not available" : `${fmt(multiview.identity_consistency_pct)}%`],
      ],
      foot: multiview.message || "A monocular camera cannot guarantee liveness.",
    },
  ];

  return (
    <div className="featurePage investigationPage ffInvestigationPage">
      <div className="ffInvestigationTopline">
        <div><span>Investigation</span><b>{session.sample ? `Sample ${session.sample.sample_id}` : "No sample selected"}</b></div>
        <div className="chipRow"><StatusChip tone={session.online ? "good" : "neutral"}>{session.online ? "Backend online" : "Backend offline"}</StatusChip><StatusChip>Gemma optional</StatusChip></div>
      </div>

      <section className="workspacePanel ffInvestigationIntro">
        <div>
          <span className="eyebrow">CROSS-MODAL INVESTIGATION ENGINE</span>
          <h1>Independent evidence, challenged before release.</h1>
          <p>Vision and sensors carry freshness signals. Reference context and multi-view consistency support the critic before deterministic fusion.</p>
        </div>
        <StatusChip tone={decision?.verdict_ready ? "good" : "warning"}>{decision?.verdict_ready ? "ASSESSMENT AVAILABLE" : "ASSESSMENT LOCKED"}</StatusChip>
      </section>

      {!report && <div className="notice">{session.sample ? "Waiting for the investigation response." : "Create or select an inspection to collect evidence."}</div>}

      <section className="ffAnalystGrid">
        {analystPanels.map(({ key, title, eyebrow, Icon, lead, note, items, foot }) => (
          <Panel key={key} title={title} eyebrow={eyebrow} className={`ffAnalystCard ${key}`}>
            <AnalystLead Icon={Icon} title={lead} note={note} />
            <Facts items={items} />
            <p className="footnote">{foot}</p>
          </Panel>
        ))}
      </section>

      <Panel title="Signals are compared without pretending every source is equivalent." eyebrow="EVIDENCE AGREEMENT" className="ffAgreementPanel">
        <div className="ffAgreementHead">
          <p>{agreement?.summary || "Collect vision and hardware sensor evidence to compare freshness-bearing signals."}</p>
          <StatusChip tone={agreementTone}>{agreement?.status || "INSUFFICIENT"}</StatusChip>
        </div>
        <div className="ffAgreementGrid">
          {(agreement?.matrix || []).map((item) => (
            <div key={item.source}>
              <b>{item.source}</b>
              <strong>{item.signal ? titleCase(item.signal) : "Not available"}</strong>
              <small>{item.role}</small>
            </div>
          ))}
          {!agreement?.matrix?.length && ["Vision", "Sensor", "Reference", "Multi-view"].map((name) => <div key={name}><b>{name}</b><strong>Waiting</strong><small>evidence pending</small></div>)}
        </div>
      </Panel>

      <section className="ffInvestigationBottomGrid">
        <Panel title="Blocking checks" eyebrow="EVIDENCE CRITIC" className="ffCriticPanel">
          <div className="ffPanelStatus"><ShieldCheck size={17} /><StatusChip tone={critic?.blocking ? "warning" : "good"}>{critic?.status || "NEEDS MORE DATA"}</StatusChip></div>
          <Bucket title="Supporting" items={critic?.supporting_evidence} tone="good" />
          <Bucket title="Missing" items={critic?.missing_evidence} tone="warning" />
          <Bucket title="Contradictions" items={critic?.contradictions} />
          <Bucket title="Warnings" items={critic?.warnings} tone="warning" />
        </Panel>

        <Panel title={decision?.verdict_ready ? titleCase(decision.label) : "More evidence required"} eyebrow="FINAL ASSESSMENT" className="ffFinalAssessmentPanel">
          <div className="ffFinalAssessmentHead">
            <StatusChip tone={decision?.verdict_ready ? "good" : "warning"}>{decision?.verdict_ready ? "EXPERIMENTAL ASSESSMENT" : "VERDICT LOCKED"}</StatusChip>
            <div className="ffLockedScore"><strong>{decision?.verdict_ready ? fmt(decision.freshness_score, 0) : "—"}</strong><span>/100</span></div>
          </div>
          <p>{decision?.reason || "Freshness score is intentionally withheld until the critic allows release."}</p>
          {decision?.verdict_ready && <small>Deterministic confidence: {fmt(decision.confidence)}% · {decision.confidence_method}</small>}
        </Panel>
      </section>

      <section className="ffInvestigationSupportGrid">
        <GemmaExplanation sampleId={session.sample?.sample_id} />
        <HumanVerification key={session.sample?.sample_id || "none"} sampleId={session.sample?.sample_id} report={report} onSaved={session.refresh} />
      </section>
    </div>
  );
}
