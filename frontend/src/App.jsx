import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Apple, Cpu, Database, Droplets, FlaskConical, Gauge, Plus, Radio, Thermometer, Wifi } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "./api";

const emptyOverview = { total_samples: 0, total_readings: 0, latest_sample: null, latest_reading: null };

function MetricCard({ icon: Icon, label, value, unit, hint }) {
  return (
    <article className="metric-card glass">
      <div className="metric-icon"><Icon size={20} /></div>
      <div>
        <span className="eyebrow">{label}</span>
        <div className="metric-value">{value ?? "--"}<small>{unit}</small></div>
        <p>{hint}</p>
      </div>
    </article>
  );
}

function App() {
  const [online, setOnline] = useState(false);
  const [overview, setOverview] = useState(emptyOverview);
  const [readings, setReadings] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Connect the backend, then create a sample.");

  const refresh = useCallback(async () => {
    try {
      await api.health();
      setOnline(true);
      const nextOverview = await api.overview();
      setOverview(nextOverview);
      const code = nextOverview.latest_sample?.sample_code;
      setReadings(code ? await api.readings(code) : []);
      setMessage(code ? `Tracking ${code}` : "Backend online. Create the first fruit sample.");
    } catch (error) {
      setOnline(false);
      setMessage(error.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  const chartData = useMemo(
    () => [...readings].reverse().map((item, index) => ({
      index: index + 1,
      temp: item.temperature,
      humidity: item.humidity,
      gas: item.gas_ppm ?? item.gas_raw,
    })),
    [readings],
  );

  const createSample = async () => {
    setBusy(true);
    try {
      const sample = await api.createSample("Banana");
      setMessage(`Created ${sample.sample_code}. Add a test reading next.`);
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  const pushTestReading = async () => {
    const code = overview.latest_sample?.sample_code;
    if (!code) return createSample();
    setBusy(true);
    try {
      const t = Date.now() / 10000;
      await api.pushReading(code, {
        device_id: "SIMULATOR_01",
        temperature: +(26.5 + Math.sin(t) * 1.2).toFixed(2),
        humidity: +(61 + Math.cos(t * 0.8) * 4).toFixed(2),
        gas_raw: Math.round(1450 + Math.sin(t * 1.4) * 220),
        gas_ppm: +(410 + Math.sin(t * 1.1) * 75).toFixed(2),
        voc_index: +(52 + Math.cos(t) * 11).toFixed(2),
      });
      setMessage("Test sensor packet stored successfully.");
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  const latest = overview.latest_reading;
  const sample = overview.latest_sample;

  return (
    <main className="app-shell">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />

      <header className="topbar glass">
        <div className="brand">
          <div className="brand-orbit"><Apple size={24} /></div>
          <div><strong>FreshFusion</strong><span>Fruit Intelligence OS</span></div>
        </div>
        <div className={`connection ${online ? "online" : "offline"}`}>
          <Wifi size={16} /> {online ? "Backend Online" : "Backend Offline"}
        </div>
      </header>

      <section className="hero">
        <div>
          <span className="kicker"><Radio size={14} /> LIVE MULTIMODAL ANALYSIS</span>
          <h1>See the fruit.<br /><span>Sense the change.</span></h1>
          <p>One dashboard for sensor telemetry, computer vision, texture intelligence and the final freshness score.</p>
          <div className="actions">
            <button onClick={createSample} disabled={!online || busy}><Plus size={17} /> New sample</button>
            <button className="secondary" onClick={pushTestReading} disabled={!online || busy}><FlaskConical size={17} /> Push test reading</button>
          </div>
          <div className="status-line"><Activity size={15} /> {message}</div>
        </div>

        <div className="fruit-core glass">
          <div className="rings"><div className="fruit-sphere">{sample?.fruit_type?.[0] || "F"}</div></div>
          <span className="eyebrow">CURRENT SAMPLE</span>
          <strong>{sample?.sample_code || "NO SAMPLE"}</strong>
          <p>{sample?.fruit_type || "Waiting for fruit"} · {sample?.status || "idle"}</p>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard icon={Thermometer} label="Temperature" value={latest?.temperature} unit="°C" hint="Chamber environment" />
        <MetricCard icon={Droplets} label="Humidity" value={latest?.humidity} unit="%" hint="Relative humidity" />
        <MetricCard icon={Gauge} label="Gas level" value={latest?.gas_ppm ?? latest?.gas_raw} unit={latest?.gas_ppm ? " ppm" : " raw"} hint="Volatile gas signal" />
        <MetricCard icon={Cpu} label="VOC index" value={latest?.voc_index} unit="" hint={latest?.device_id || "No device"} />
      </section>

      <section className="dashboard-grid">
        <article className="chart-panel glass">
          <div className="panel-head">
            <div><span className="eyebrow">SENSOR TELEMETRY</span><h2>Freshness environment</h2></div>
            <span className="live-pill">● Live</span>
          </div>
          {chartData.length ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="tempFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#71f7af" stopOpacity={0.38}/><stop offset="95%" stopColor="#71f7af" stopOpacity={0}/></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.07)" />
                <XAxis dataKey="index" stroke="#6f847a" tickLine={false} />
                <YAxis stroke="#6f847a" tickLine={false} />
                <Tooltip contentStyle={{ background: "#0b1511", border: "1px solid #244033", borderRadius: 14 }} />
                <Area type="monotone" dataKey="temp" stroke="#71f7af" fill="url(#tempFill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div className="empty-chart">Push readings to generate live telemetry.</div>}
        </article>

        <aside className="insight-panel glass">
          <div className="panel-head"><div><span className="eyebrow">PIPELINE</span><h2>Intelligence layers</h2></div></div>
          <div className="pipeline-item active"><Radio /><div><b>Sensor layer</b><span>Temperature · humidity · gas</span></div></div>
          <div className="pipeline-item"><Apple /><div><b>Vision layer</b><span>Color · texture · defects</span></div></div>
          <div className="pipeline-item"><Cpu /><div><b>AI model</b><span>Fresh · ripe · overripe · spoiled</span></div></div>
          <div className="pipeline-item"><Activity /><div><b>Fusion engine</b><span>Final freshness score</span></div></div>
        </aside>
      </section>

      <section className="bottom-grid">
        <article className="glass compact-stat"><Database /><div><span className="eyebrow">DATABASE</span><strong>{overview.total_samples}</strong><p>fruit samples stored</p></div></article>
        <article className="glass compact-stat"><Activity /><div><span className="eyebrow">TELEMETRY</span><strong>{overview.total_readings}</strong><p>sensor readings stored</p></div></article>
        <article className="glass roadmap"><span className="eyebrow">NEXT MODULE</span><strong>Computer Vision Lab</strong><p>Image upload, segmentation, RGB/HSV, GLCM texture and defect mapping.</p></article>
      </section>
    </main>
  );
}

export default App;
