import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Image, LineChart, PackageCheck, Scale, ShieldCheck } from "lucide-react";
import { updateInspectionProfile } from "../../api";
import "./p0-inspection-panel.css";

const nice = (value) => String(value ?? "--").replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const num = (value, digits = 1) => value == null || Number.isNaN(Number(value)) ? "--" : Number(value).toFixed(digits);

function Status({ ok, children }) {
  return <span className={`p0Status ${ok ? "ok" : "warn"}`}>{ok ? <CheckCircle2 size={13}/> : <AlertTriangle size={13}/>} {children}</span>;
}

export default function P0InspectionPanel({ session }) {
  const product = session.report?.product || {};
  const quality = product.image_quality || {};
  const comparison = product.condition_comparison || {};
  const breakdown = product.score_breakdown || {};
  const recommendation = product.recommendation || {};
  const protocol = product.protocol || {};
  const drift = product.sensor_drift || {};
  const provenance = product.provenance || {};
  const events = product.events || [];
  const sourceProfile = product.profile || {};
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({ fruit_count: 1, approximate_weight_g: "", fruit_instance_id: "", inspection_duration_seconds: "", chamber_purged: "", batch_id: "", supplier: "", storage_location: "" });

  useEffect(() => {
    setProfile({
      fruit_count: sourceProfile.fruit_count ?? 1,
      approximate_weight_g: sourceProfile.approximate_weight_g ?? "",
      fruit_instance_id: sourceProfile.fruit_instance_id ?? sourceProfile.protocol?.fruit_instance_id ?? "",
      inspection_duration_seconds: sourceProfile.protocol?.inspection_duration_seconds ?? "",
      chamber_purged: sourceProfile.protocol?.chamber_purged == null ? "" : String(sourceProfile.protocol.chamber_purged),
      batch_id: sourceProfile.batch_id ?? "",
      supplier: sourceProfile.supplier ?? "",
      storage_location: sourceProfile.storage_location ?? "",
    });
  }, [session.sample?.sample_id, sourceProfile.approximate_weight_g, sourceProfile.fruit_count, sourceProfile.fruit_instance_id, sourceProfile.batch_id, sourceProfile.supplier, sourceProfile.storage_location, sourceProfile.protocol?.fruit_instance_id, sourceProfile.protocol?.inspection_duration_seconds, sourceProfile.protocol?.chamber_purged]);

  const qualityIssues = quality.issues || [];
  const recentAlerts = useMemo(() => events.slice(0, 5), [events]);

  const save = async () => {
    if (!session.sample?.sample_id) return;
    setSaving(true);
    try {
      await updateInspectionProfile(session.sample.sample_id, {
        fruit_count: Number(profile.fruit_count || 1),
        approximate_weight_g: profile.approximate_weight_g === "" ? null : Number(profile.approximate_weight_g),
        fruit_instance_id: profile.fruit_instance_id || null,
        inspection_duration_seconds: profile.inspection_duration_seconds === "" ? null : Number(profile.inspection_duration_seconds),
        chamber_purged: profile.chamber_purged === "" ? null : profile.chamber_purged === "true",
        batch_id: profile.batch_id || null,
        supplier: profile.supplier || null,
        storage_location: profile.storage_location || null,
      });
      await session.refresh();
    } catch (error) {
      session.setErr(error.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="p0Panel">
      <div className="p0Header">
        <div><span>INSPECTION QUALITY & DECISION LOGIC</span><h2>Why FreshFusion trusts — or holds — this result</h2></div>
        <Status ok={!quality.blocking}>{quality.status === "ready" ? "Image evidence ready" : "Image evidence needs attention"}</Status>
      </div>

      <div className="p0Grid">
        <article className="p0Card">
          <div className="p0Title"><Image size={17}/><b>Image quality gate</b></div>
          <div className="p0MiniGrid">
            <div><span>Usable views</span><b>{quality.usable_views?.length ?? 0}/3</b></div>
            <div><span>Duplicate views</span><b>{quality.duplicate_pairs?.length ?? 0}</b></div>
            <div><span>Captured</span><b>{quality.captured_views?.length ?? 0}/3</b></div>
          </div>
          {qualityIssues.length ? <ul>{qualityIssues.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="p0Good">Blur, lighting, framing and duplicate-view checks are clear.</p>}
        </article>

        <article className="p0Card">
          <div className="p0Title"><LineChart size={17}/><b>Condition change</b></div>
          {comparison.available ? (
            <><div className="p0Compare"><strong>{nice(comparison.previous_label)}</strong><span>→</span><strong>{nice(comparison.current_label)}</strong></div><p>Score change: <b>{comparison.score_change > 0 ? "+" : ""}{num(comparison.score_change)} points</b></p></>
          ) : <p>No verified previous assessment is available yet.</p>}
          {recentAlerts.length > 0 && <div className="p0Events">{recentAlerts.map((event) => <div key={event.id} className={`p0Event ${event.severity}`}><b>{nice(event.event_type)}</b><span>{event.message}</span></div>)}</div>}
        </article>

        <article className="p0Card">
          <div className="p0Title"><ShieldCheck size={17}/><b>Why this score?</b></div>
          <div className="p0MiniGrid">
            <div><span>Sensor</span><b>{num(breakdown.sensor?.score)} × 48%</b><small>{breakdown.sensor?.contribution == null ? "--" : `${num(breakdown.sensor.contribution)} pts`}</small></div>
            <div><span>Vision</span><b>{num(breakdown.vision?.score)} × 52%</b><small>{breakdown.vision?.contribution == null ? "--" : `${num(breakdown.vision.contribution)} pts`}</small></div>
            <div><span>Final</span><b>{breakdown.final_score == null ? "Locked" : num(breakdown.final_score)}</b><small>deterministic score</small></div>
          </div>
          <p>{recommendation.reason || "The final score stays locked until required evidence passes."}</p>
          {recommendation.damage_note && <p className="p0Info">{recommendation.damage_note}</p>}
        </article>
      </div>

      <div className="p0Protocol">
        <div className="p0ProtocolHead"><div><span>MEASUREMENT PROTOCOL</span><h3>Keep every inspection comparable</h3></div><Status ok={protocol.ready !== false}>{protocol.ready === false ? "Protocol incomplete" : "Protocol ready / optional"}</Status></div>
        <div className="p0Form">
          <label><PackageCheck size={14}/> Fruit specimen ID<input value={profile.fruit_instance_id} onChange={(e)=>setProfile({...profile, fruit_instance_id:e.target.value})} placeholder="e.g. APP-01"/></label>
          <label><PackageCheck size={14}/> Fruit count<input type="number" min="1" value={profile.fruit_count} onChange={(e)=>setProfile({...profile, fruit_count:e.target.value})}/></label>
          <label><Scale size={14}/> Approx. weight (g)<input type="number" min="1" value={profile.approximate_weight_g} onChange={(e)=>setProfile({...profile, approximate_weight_g:e.target.value})}/></label>
          <label><Clock3 size={14}/> Stabilization time (s)<input type="number" min="10" value={profile.inspection_duration_seconds} onChange={(e)=>setProfile({...profile, inspection_duration_seconds:e.target.value})}/></label>
          <label>Chamber reset<select value={profile.chamber_purged} onChange={(e)=>setProfile({...profile, chamber_purged:e.target.value})}><option value="">Not confirmed</option><option value="true">Purged / reset</option><option value="false">Not purged</option></select></label>
          <label>Batch ID<input value={profile.batch_id} onChange={(e)=>setProfile({...profile, batch_id:e.target.value})}/></label>
          <label>Supplier<input value={profile.supplier} onChange={(e)=>setProfile({...profile, supplier:e.target.value})}/></label>
          <label>Storage location<input value={profile.storage_location} onChange={(e)=>setProfile({...profile, storage_location:e.target.value})}/></label>
          <button className="primary" onClick={save} disabled={saving || !session.online}>{saving ? "Saving..." : "Save inspection setup"}</button>
        </div>
        <p className="p0Info">Use the same specimen ID when you re-inspect the same physical fruit. This keeps all of its views and repeated observations in one validation split.</p>
        {(protocol.issues?.length > 0 || protocol.warnings?.length > 0) && <div className="p0ProtocolNotes">{[...(protocol.issues||[]), ...(protocol.warnings||[])].map((x)=><span key={x}>{x}</span>)}</div>}
        {drift.checked && <p className={drift.suspected ? "p0Drift warn" : "p0Drift"}>Sensor drift: <b>{drift.suspected ? "Review required" : "Within historical band"}</b> · current baseline {num(drift.current_baseline_mean,0)} ADC vs historical {num(drift.historical_baseline_median,0)} ADC.</p>}
      </div>

      <div className="p0Protocol">
        <div className="p0ProtocolHead"><div><span>DECISION PROVENANCE</span><h3>Exactly which logic produced this assessment</h3></div><Status ok={provenance.calibration_version && provenance.calibration_version !== "UNCALIBRATED"}>{provenance.scientific_status ? nice(provenance.scientific_status) : "Version data pending"}</Status></div>
        <div className="p0MiniGrid">
          <div><span>Rule version</span><b>{provenance.rule_version || "--"}</b></div>
          <div><span>Recommendation</span><b>{provenance.recommendation_version || "--"}</b></div>
          <div><span>Dataset version</span><b>{provenance.dataset_version || "--"}</b></div>
          <div><span>Calibration</span><b>{provenance.calibration_version || "--"}</b></div>
          <div><span>Split policy</span><b>{provenance.split_version || "--"}</b></div>
          <div><span>Model artifact</span><b>{nice(provenance.model?.status || "not deployed")}</b><small>{provenance.model?.sha256 ? `${provenance.model.sha256.slice(0, 12)}…` : "No validated model hash"}</small></div>
        </div>
      </div>
    </section>
  );
}
