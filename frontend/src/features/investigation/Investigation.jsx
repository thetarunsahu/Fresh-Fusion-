import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { fmt, titleCase } from "../../shared/format";
import HumanVerification from "./HumanVerification";
import GemmaExplanation from "./GemmaExplanation";

export default function Investigation({ session }) {
  const report = session.report;
  const {
    vision = {},
    sensor = {},
    reference = {},
    multiview = {},
  } = report?.analysts || {};
  const reading = sensor.latest || {};
  const match = reference.match || {};
  const agreement = report?.agreement;
  const critic = report?.critic;
  const decision = report?.decision;
  const agreementTone =
    agreement?.status === "ALIGNED"
      ? "good"
      : agreement?.status === "CONFLICTING"
        ? "warning"
        : "neutral";

  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">INVESTIGATION</span>
        <h1>Independent evidence, challenged before release.</h1>
        <p>
          Vision and sensors carry freshness signals. Reference data provides
          context, multi-view analysis gates physical evidence, and the critic
          blocks unsupported conclusions before deterministic fusion.
        </p>
      </div>
      {!report && (
        <div className="notice">
          {session.sample
            ? "Waiting for the investigation response."
            : "Create or select an inspection to collect evidence. Analyst fields stay empty until measurements exist."}
        </div>
      )}
      <div className="analystGrid">
        <Panel title="Vision Analyst" eyebrow="OPENCV / HEURISTICS">
          <Facts
            items={[
              ["Detected fruit", vision.identity?.fruit],
              [
                "Identity confidence (heuristic)",
                vision.identity?.confidence == null
                  ? "Not available"
                  : `${fmt(vision.identity.confidence)}%`,
              ],
              ["Usable recent images", vision.usable_images],
              [
                "Healthy surface estimate",
                vision.healthy_surface_estimate_pct == null
                  ? "Not available"
                  : `${fmt(vision.healthy_surface_estimate_pct)}%`,
              ],
              [
                "Visible damage estimate",
                vision.defects?.visible_damage_estimate_pct == null
                  ? "Not available"
                  : `${fmt(vision.defects.visible_damage_estimate_pct)}%`,
              ],
              ["Trained freshness inference", titleCase(vision.ai?.status)],
            ]}
          />
          <ul className="findingList">
            {vision.warnings?.map((x, i) => (
              <li key={i}>
                <b>{x.label}:</b> {x.note}
              </li>
            ))}
          </ul>
          <p className="footnote">
            Surface estimates can be affected by lighting, shadows and
            background.
          </p>
        </Panel>
        <Panel title="Sensor Analyst" eyebrow="DETERMINISTIC">
          <Facts
            items={[
              ["Temperature", `${fmt(reading.temperature)} °C`],
              ["Humidity", `${fmt(reading.humidity)}% RH`],
              ["MQ135 raw", `${fmt(reading.mq135_raw, 0)} ADC`],
              [
                "Relative response (raw / 4095)",
                fmt(reading.relative_gas_response, 4),
              ],
              ["Latest declared source", reading.source],
              [
                "Reading age",
                sensor.age_seconds == null
                  ? "Not available"
                  : `${fmt(sensor.age_seconds, 0)} seconds`,
              ],
              ["Eligible hardware readings", sensor.eligible_readings],
            ]}
          />
          <p className="footnote">
            {sensor.note ||
              "Uncalibrated 12-bit electrical response, not ppm. Simulator data cannot unlock the verdict. Source labels are not device authentication."}
          </p>
        </Panel>
        <Panel title="Reference Analyst" eyebrow="LOCAL PUBLIC REFERENCE INDEX">
          <Facts
            items={[
              ["Dataset", match.source?.name || reference.index?.source?.name],
              ["Nearest published class", match.match],
              [
                "Reference similarity",
                match.similarity == null
                  ? "Not available"
                  : `${fmt(match.similarity)}%`,
              ],
              ["Examples in matched class", match.reference_samples],
              ["Indexed examples", reference.index?.samples],
              [
                "Index state",
                reference.index?.ready
                  ? "Available"
                  : report
                    ? "Not built"
                    : "Unknown",
              ],
            ]}
          />
          <p className="footnote">
            Similarity ≠ model accuracy or probability. Published normal/rotten
            labels are not silently converted to FreshFusion's four stages.
          </p>
        </Panel>
        <Panel title="Multi-view Analyst" eyebrow="PHYSICAL EVIDENCE">
          <Facts
            items={[
              ["Captured recent views", multiview.views?.join(", ") || "None"],
              ["Required views", multiview.required_views ?? 3],
              ["Physical fruit status", titleCase(multiview.status)],
              [
                "Screen/photo suspicion",
                fmt(multiview.screen_suspicion_pct) + "%",
              ],
              [
                "Appearance diversity",
                fmt(multiview.appearance_diversity_pct) + "%",
              ],
              [
                "Identity consistency",
                fmt(multiview.identity_consistency_pct) + "%",
              ],
            ]}
          />
          <p className="footnote">
            {multiview.message ||
              "Move around the real fruit, changing the selected view. A monocular camera cannot guarantee liveness."}
          </p>
        </Panel>
      </div>

      <Panel title="Evidence agreement" eyebrow="CROSS-MODAL CONSISTENCY">
        <div className="agreementHeader">
          <div>
            <StatusChip tone={agreementTone}>
              {agreement?.status || "INSUFFICIENT"}
            </StatusChip>
            <p>
              {agreement?.summary ||
                "Collect vision and hardware sensor evidence to compare freshness-bearing signals."}
            </p>
          </div>
          <div className="agreementCount">
            <strong>{agreement?.counted_sources ?? 0}</strong>
            <span>freshness signals compared</span>
          </div>
        </div>
        <div className="agreementGrid">
          {(agreement?.matrix || []).map((item) => (
            <div className="agreementCard" key={item.source}>
              <span className="eyebrow">{item.role}</span>
              <h3>{item.source}</h3>
              <strong>{item.signal ? titleCase(item.signal) : "Not available"}</strong>
              <p>{item.detail}</p>
            </div>
          ))}
        </div>
        <p className="footnote">
          {agreement?.note ||
            "Reference and multi-view evidence are not treated as equivalent freshness votes."}
        </p>
      </Panel>

      <Panel title="Evidence critic" eyebrow="DETERMINISTIC CHECKS">
        <StatusChip tone={critic?.blocking ? "warning" : "neutral"}>
          {critic?.status || "NEEDS MORE DATA"}
        </StatusChip>
        <div className="criticGrid">
          {[
            ["Supporting evidence", "supporting_evidence"],
            ["Missing evidence", "missing_evidence"],
            ["Contradictions", "contradictions"],
            ["Warnings", "warnings"],
          ].map(([name, key]) => (
            <div key={key}>
              <h3>{name}</h3>
              {critic?.[key]?.length ? (
                <ul className="findingList">
                  {critic[key].map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">
                  {critic ? "None recorded." : "Awaiting evidence."}
                </p>
              )}
            </div>
          ))}
        </div>
      </Panel>
      <Panel
        title="Final assessment"
        eyebrow="FRESHNESS HYPOTHESIS → CRITIC → FUSION"
      >
        <div className="assessment">
          <div>
            <StatusChip tone={decision?.verdict_ready ? "good" : "warning"}>
              {decision?.verdict_ready
                ? "EXPERIMENTAL ASSESSMENT"
                : "VERDICT LOCKED"}
            </StatusChip>
            <h2>
              {decision?.verdict_ready
                ? titleCase(decision.label)
                : decision?.status || "More evidence required"}
            </h2>
            <p>
              {decision?.reason ||
                "Connect the backend and collect camera plus hardware evidence."}
            </p>
          </div>
          <div className="assessmentScore">
            <strong>
              {decision?.verdict_ready ? fmt(decision.freshness_score, 0) : "—"}
            </strong>
            <span>/100 freshness</span>
          </div>
        </div>
        {decision?.verdict_ready && (
          <p>
            Deterministic confidence: {fmt(decision.confidence)}%.{" "}
            {decision.confidence_method}
          </p>
        )}
      </Panel>

      <GemmaExplanation sampleId={session.sample?.sample_id} />

      <HumanVerification
        key={session.sample?.sample_id || "none"}
        sampleId={session.sample?.sample_id}
        report={report}
        onSaved={session.refresh}
      />
    </div>
  );
}
