import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CheckCircle2,
  Leaf,
  RefreshCw,
  ShieldCheck,
  TriangleAlert,
  WifiOff,
} from "lucide-react";
import CameraStream from "./components/CameraStream";
import { createSample, health, activeSample, bundle } from "./api";
import "./styles.css";
import "./validation.css";

function PhoneVisionApp() {
  const [online, setOnline] = useState(false);
  const [sample, setSample] = useState(null);
  const [truth, setTruth] = useState("");
  const [error, setError] = useState("");
  const [frames, setFrames] = useState(0);
  const [validation, setValidation] = useState(null);
  const syncing = useRef(false);
  const selectedId = useRef(
    new URLSearchParams(location.search).get("sample_id"),
  );
  const [target, setTarget] = useState(null);

  const syncActiveSample = async () => {
    if (syncing.current) return;
    syncing.current = true;
    try {
      await health();
      setOnline(true);
      let active = await activeSample();
      if (!active) active = await createSample("Auto");
      setTarget(active);
      if (!selectedId.current) selectedId.current = active.sample_id;
      const id = selectedId.current;
      const payload = await bundle(id);
      if (id !== selectedId.current) return;
      setSample(payload.sample);
      setValidation(payload.fusion?.components?.validation || null);
      setError("");
    } catch (e) {
      setOnline(false);
      setError(e.message || String(e));
    } finally {
      syncing.current = false;
    }
  };

  useEffect(() => {
    syncActiveSample();
    const timer = setInterval(syncActiveSample, 2500);
    return () => clearInterval(timer);
  }, []);

  const onFrame = (result) => {
    setFrames((v) => v + 1);
    if (result?.physical_validation) setValidation(result.physical_validation);
    if (
      result?.auto_detection?.sample_changed &&
      result.auto_detection.previous_sample_id === selectedId.current
    ) {
      selectedId.current = result.sample_id;
      setTruth("");
      setSample({ sample_id: result.sample_id, fruit_type: result.fruit_type });
      setTarget({ sample_id: result.sample_id });
      const url = new URL(location.href);
      url.searchParams.set("sample_id", result.sample_id);
      history.replaceState(null, "", url);
    }
  };

  const verified = validation?.physical_likely === true;
  const failed = ["suspected_2d_display", "suspected_flat_reference"].includes(
    validation?.status,
  );

  return (
    <div className="phoneNodePage">
      <div className="phoneTopbar">
        <div className="brandLine">
          <div className="logoMark">
            <Leaf size={18} />
          </div>
          <div>
            <b>FreshFusion</b>
            <span>Phone Vision Node</span>
          </div>
        </div>
        <span className={online ? "phoneOnline on" : "phoneOnline"}>
          {online ? "connected" : "offline"}
        </span>
      </div>

      <div className="phoneSample">
        <span>Active sample</span>
        <b>
          {sample
            ? `${sample.fruit_type} · ${sample.sample_id}`
            : "Connecting..."}
        </b>
        <small>
          Scan the real physical fruit. Do not point the camera at a fruit
          photo, laptop display or another phone screen.
        </small>
      </div>

      {error && (
        <div className="errorBox">
          <WifiOff size={15} /> {error}
        </div>
      )}

      {sample && target && sample.sample_id !== target.sample_id && (
        <div className="errorBox">
          Capture target changed to {target.sample_id}. This phone remains
          paired to {sample.sample_id}.{" "}
          <button
            className="secondary"
            onClick={() => {
              selectedId.current = target.sample_id;
              setSample(null);
              setValidation(null);
              setFrames(0);
              const url = new URL(location.href);
              url.searchParams.set("sample_id", target.sample_id);
              history.replaceState(null, "", url);
              syncActiveSample();
            }}
          >
            Pair with active inspection
          </button>
        </div>
      )}
      <CameraStream
        sampleId={
          online && sample?.sample_id === target?.sample_id
            ? sample?.sample_id
            : undefined
        }
        groundTruth={truth}
        compact
        autoStart
        onFrame={onFrame}
      />

      <div className={`phoneHelp ${failed ? "physicalWarn" : ""}`}>
        {verified ? <ShieldCheck size={17} /> : <TriangleAlert size={17} />}
        <p>
          {validation?.message ||
            "Physical verification needs at least three genuinely different views. Start with Front, then move around the real fruit and select Left/Right and Back/Top."}
        </p>
      </div>

      {validation && (
        <div className="phoneSample">
          <span>Physical evidence</span>
          <b>
            {verified
              ? "Likely physical fruit"
              : failed
                ? "Flat/screen reference suspected"
                : "Collecting views"}
          </b>
          <small>
            {validation.views_count || 0}/3 views · screen/photo suspicion{" "}
            {Math.round(validation.screen_suspicion_pct || 0)}% · appearance
            change {Math.round(validation.appearance_diversity_pct || 0)}%
          </small>
        </div>
      )}

      <label className="truthSelect">
        <span>Dataset label (optional)</span>
        <select value={truth} onChange={(e) => setTruth(e.target.value)}>
          <option value="">Unlabelled</option>
          <option value="fresh">Fresh</option>
          <option value="ripe">Ripe</option>
          <option value="overripe">Overripe</option>
          <option value="spoiled">Spoiled</option>
        </select>
      </label>

      <div className="phoneHelp">
        <CheckCircle2 size={17} />
        <p>
          Select Front, Left/Right and Back/Top while physically moving around
          the fruit. Frames continue uploading automatically.
        </p>
      </div>
      <a className="secondary" href="/#overview">
        Open investigation workspace
      </a>

      <div className="phoneHelp">
        <RefreshCw size={17} />
        <p>
          {frames} frames uploaded in this session. Keep this page open while
          scanning.
        </p>
      </div>
    </div>
  );
}

createRoot(document.getElementById("phone-root")).render(<PhoneVisionApp />);
