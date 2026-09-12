import { useMemo, useState } from "react";
import { CheckCircle2, ShieldCheck } from "lucide-react";

const fruits = ["Apple", "Banana", "Tomato"];

export default function IdentityConfirmBar({ session }) {
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const sample = session.sample;
  const report = session.report || {};
  const product = report.product || {};
  const vision = report.analysts?.vision || {};
  const raw = vision.raw_identity || {};
  const suggested = product.detected_fruit || raw.fruit || vision.identity?.raw_frame_fruit || null;
  const current = sample?.fruit_type && sample.fruit_type !== "Auto" ? sample.fruit_type : product.fruit || null;
  const source = String(sample?.source || "").toLowerCase();
  const confirmed = source === "operator-confirmed";

  const subtitle = useMemo(() => {
    if (!sample) return "Start an inspection first.";
    if (confirmed) return `Confirmed as ${current}. Raw camera predictions are kept only as diagnostics.`;
    if (suggested && suggested !== "Unknown") {
      const confidence = raw.confidence ?? vision.identity?.raw_frame_confidence;
      return `Camera suggestion: ${suggested}${confidence != null ? ` (${Math.round(confidence)}%)` : ""}. Confirm once before the pitch result is trusted.`;
    }
    return "Waiting for a clear fruit frame. You can still confirm the physical fruit manually.";
  }, [sample, confirmed, current, suggested, raw.confidence, vision.identity?.raw_frame_confidence]);

  const confirm = async (fruit) => {
    if (!sample?.sample_id || busy) return;
    setBusy(fruit);
    setMessage("");
    try {
      const response = await fetch(`/api/v1/samples/${encodeURIComponent(sample.sample_id)}/identity`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fruit_type: fruit }),
      });
      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const body = await response.json();
          detail = body?.detail || detail;
        } catch {}
        throw new Error(detail);
      }
      setMessage(`${fruit} confirmed for this inspection.`);
      await session.refresh();
    } catch (error) {
      session.setErr?.(error.message || "Identity confirmation failed.");
    } finally {
      setBusy("");
    }
  };

  if (!sample) return null;

  return (
    <section className="ffPanel" style={{ marginBottom: 14, padding: 16, display: "grid", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "space-between", flexWrap: "wrap" }}>
        <div>
          <div className="ffEyebrow">FRUIT IDENTITY CONTROL</div>
          <h3 style={{ margin: "4px 0 5px" }}>{confirmed ? `Confirmed: ${current}` : "Confirm the physical fruit"}</h3>
          <p style={{ margin: 0, opacity: 0.76 }}>{subtitle}</p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {fruits.map((fruit) => {
            const active = String(current || "").toLowerCase() === fruit.toLowerCase();
            return (
              <button
                key={fruit}
                type="button"
                className={active && confirmed ? "primary" : "secondary"}
                onClick={() => confirm(fruit)}
                disabled={Boolean(busy)}
              >
                {active && confirmed ? <CheckCircle2 size={14} /> : <ShieldCheck size={14} />}
                {busy === fruit ? "Confirming..." : fruit}
              </button>
            );
          })}
        </div>
      </div>
      {message && <small style={{ color: "#1f6d4a" }}>{message}</small>}
      <small style={{ opacity: 0.68 }}>
        One camera is enough for fruit identity. Extra views improve surface coverage and physical-evidence confidence; they are not three separate cameras.
      </small>
    </section>
  );
}
