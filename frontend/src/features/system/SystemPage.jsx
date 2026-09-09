import { Bot, Cpu, Database, Laptop, ShieldCheck, Smartphone } from "lucide-react";
import { Panel, Facts, StatusChip } from "../../shared/Panel";

function DeviceCard({ Icon, title, detail, ready, status }) {
  return (
    <article className="systemDeviceCard">
      <div className="systemDeviceHead">
        <span><Icon size={16} /> {title}</span>
        <StatusChip tone={ready ? "good" : "neutral"}>{status || (ready ? "READY" : "WAITING")}</StatusChip>
      </div>
      <small>{detail}</small>
      <div className="systemDeviceBar" aria-hidden="true"><i style={{ width: ready ? "82%" : "28%" }} /></div>
    </article>
  );
}

export default function SystemPage({ session, user }) {
  const h = session.healthInfo || {};
  const latestSensor = session.data?.sensors?.at(-1);
  const espReady = session.report?.evidence?.sensors?.physical_present === true;
  const phoneReady = session.report?.evidence?.camera?.recent === true || Boolean(h.phone_dashboard);
  const referenceReady = Boolean(session.report?.analysts?.reference?.index?.ready);

  const devices = [
    [Laptop, "Backend API", `FastAPI · ${h.backend_port ? `port ${h.backend_port}` : "local runtime"}`, session.online, session.online ? "ONLINE" : "OFFLINE"],
    [Smartphone, "Phone Camera", h.phone_mode || "Secure capture route", phoneReady, phoneReady ? "READY" : "WAITING"],
    [Cpu, "ESP32", latestSensor?.device_id || "DHT11 + MQ135", espReady, espReady ? "CONNECTED" : "WAITING"],
    [Bot, "Ollama", "127.0.0.1:11434", session.online, session.online ? "CHECK VIA AI" : "OFFLINE"],
    [Bot, "Gemma 3", "gemma3:4b · explanation only", session.online, session.online ? "LOCAL" : "WAITING"],
    [Database, "Reference Index", referenceReady ? "Public reference index loaded" : "Reference status pending", referenceReady, referenceReady ? "READY" : "WAITING"],
  ];

  return (
    <div className="featurePage systemPage">
      <div className="pageIntro">
        <span className="eyebrow">FRESHFUSION WORKSPACE</span>
        <h1>System & Devices</h1>
        <p>Operational readiness for the chamber, phone camera, local AI runtime and backend services.</p>
      </div>

      <section className="systemDeviceGrid">
        {devices.map(([Icon, title, detail, ready, status]) => (
          <DeviceCard key={title} Icon={Icon} title={title} detail={detail} ready={ready} status={status} />
        ))}
      </section>

      <section className="systemBottomGrid">
        <Panel title="Secure operator access" eyebrow="AUTHENTICATION" className="systemSecurityPanel">
          <p>JWT session · PBKDF2-SHA256 password hashing · role-aware workspace · authenticated human-review identity.</p>
          <Facts items={[
            ["Current user", user?.full_name],
            ["Email", user?.email],
            ["Role", user?.role ? user.role[0].toUpperCase() + user.role.slice(1) : null],
            ["Session", user ? "Authenticated" : "Unavailable"],
          ]} />
          <div className="chipRow"><StatusChip tone="good"><ShieldCheck size={12} /> Signed session</StatusChip></div>
        </Panel>

        <Panel title="Runtime & safety boundaries" eyebrow="LOCAL CONFIGURATION" className="systemConfigPanel">
          <Facts items={[
            ["Backend", h.backend_port ? `http://localhost:${h.backend_port}` : "Local dynamic port"],
            ["Ollama", "http://127.0.0.1:11434"],
            ["Model", "gemma3:4b"],
            ["Phone mode", h.phone_mode || "trusted HTTPS / local-only"],
            ["Verdict authority", "Deterministic investigation"],
            ["LLM role", "Explanation only"],
            ["Device authentication", h.authentication?.device_authentication || "Production hardening pending"],
          ]} />
          <div className="systemGuardrail">No calibration claim · no food-safety certification · device pairing is not claimed as authenticated</div>
        </Panel>
      </section>
    </div>
  );
}
