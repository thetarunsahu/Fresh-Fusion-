import { Bot, Cpu, Database, Laptop, ShieldCheck, Smartphone } from "lucide-react";
import { Panel, Facts, StatusChip } from "../../shared/Panel";

export default function SystemPage({ session, user }) {
  const h = session.healthInfo || {};
  const devices = [
    ["Backend API", session.online, Laptop],
    ["Phone camera path", Boolean(h.phone_dashboard), Smartphone],
    ["ESP32 endpoint", Boolean(h.esp32_endpoint), Cpu],
    ["Reference / database services", session.online, Database],
    ["Local AI runtime", session.online, Bot],
  ];
  return (
    <div className="featurePage systemPage">
      <div className="pageIntro">
        <span className="eyebrow">SYSTEM</span>
        <h1>Know what is connected before the demo starts.</h1>
        <p>Operational readiness for the FreshFusion laptop, phone, ESP32, local AI and authenticated workspace.</p>
      </div>
      <div className="twoPanels">
        <Panel title="Device readiness" eyebrow="LOCAL PROTOTYPE">
          <div className="connectionList">
            {devices.map(([label, ready, Icon]) => (
              <div key={label}><span><Icon size={15} /> {label}</span><StatusChip tone={ready ? "good" : "neutral"}>{ready ? "Ready" : "Waiting"}</StatusChip></div>
            ))}
          </div>
        </Panel>
        <Panel title="Authenticated operator" eyebrow="JWT USER SESSION">
          <Facts items={[
            ["Name", user?.full_name],
            ["Email", user?.email],
            ["Role", user?.role],
            ["Account active", user?.is_active ? "Yes" : "No"],
          ]} />
          <div className="chipRow"><StatusChip tone="good"><ShieldCheck size={12} /> Signed session</StatusChip></div>
        </Panel>
      </div>
      <Panel title="Runtime endpoints" eyebrow="DEMO RECOVERY REFERENCE">
        <Facts items={[
          ["Backend status", session.online ? "Online" : "Disconnected"],
          ["Backend port", h.backend_port],
          ["Frontend port", h.frontend_port],
          ["Phone mode", h.phone_mode],
          ["Phone dashboard", h.phone_dashboard],
          ["ESP32 API", h.esp32_endpoint],
          ["Authentication", h.authentication?.mode || "JWT"],
          ["Device authentication", h.authentication?.device_authentication || "Planned"],
        ]} />
      </Panel>
      <div className="notice">
        <b>Prototype boundary:</b> user authentication is implemented. Secure ESP32/device pairing remains a production-hardening item and should not be claimed as complete.
      </div>
    </div>
  );
}
