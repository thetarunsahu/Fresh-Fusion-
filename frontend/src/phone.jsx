import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CheckCircle2, Leaf, RefreshCw, ShieldCheck, TriangleAlert, WifiOff } from 'lucide-react';
import CameraStream from './components/CameraStream';
import { createSample, health, listSamples } from './api';
import './styles.css';
import './validation.css';

function PhoneVisionApp() {
  const [online, setOnline] = useState(false);
  const [sample, setSample] = useState(null);
  const [truth, setTruth] = useState('');
  const [error, setError] = useState('');
  const [frames, setFrames] = useState(0);
  const [validation, setValidation] = useState(null);
  const syncing = useRef(false);

  const syncActiveSample = async () => {
    if (syncing.current) return;
    syncing.current = true;
    try {
      await health();
      setOnline(true);
      let rows = await listSamples();
      if (!rows.length) {
        const created = await createSample('Auto');
        rows = [created];
      }
      const active = rows[0];
      setSample(current => current?.sample_id === active.sample_id ? {...current, ...active} : active);
      setError('');
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

  const onFrame = result => {
    setFrames(v => v + 1);
    if (result?.physical_validation) setValidation(result.physical_validation);
  };

  const verified = validation?.physical_likely === true;
  const failed = ['suspected_2d_display','suspected_flat_reference'].includes(validation?.status);

  return <div className="phoneNodePage">
    <div className="phoneTopbar">
      <div className="brandLine">
        <div className="logoMark"><Leaf size={18}/></div>
        <div><b>FreshFusion</b><span>Phone Vision Node</span></div>
      </div>
      <span className={online ? 'phoneOnline on' : 'phoneOnline'}>{online ? 'connected' : 'offline'}</span>
    </div>

    <div className="phoneSample">
      <span>Active sample</span>
      <b>{sample ? `${sample.fruit_type} · ${sample.sample_id}` : 'Connecting...'}</b>
      <small>Scan the real physical fruit. Do not point the camera at a fruit photo, laptop display or another phone screen.</small>
    </div>

    {error && <div className="errorBox"><WifiOff size={15}/> {error}</div>}

    <CameraStream
      sampleId={sample?.sample_id}
      groundTruth={truth}
      compact
      autoStart
      onFrame={onFrame}
    />

    <div className={`phoneHelp ${failed ? 'physicalWarn' : ''}`}>
      {verified ? <ShieldCheck size={17}/> : <TriangleAlert size={17}/>} 
      <p>{validation?.message || 'Physical verification needs at least three genuinely different views. Start with Front, then move around the real fruit and select Left/Right and Back/Top.'}</p>
    </div>

    {validation && <div className="phoneSample">
      <span>Physical evidence</span>
      <b>{verified ? 'Likely physical fruit' : failed ? 'Flat/screen reference suspected' : 'Collecting views'}</b>
      <small>{validation.views_count || 0}/3 views · screen/photo suspicion {Math.round(validation.screen_suspicion_pct || 0)}% · appearance change {Math.round(validation.appearance_diversity_pct || 0)}%</small>
    </div>}

    <label className="truthSelect">
      <span>Dataset label (optional)</span>
      <select value={truth} onChange={e => setTruth(e.target.value)}>
        <option value="">Unlabelled</option>
        <option value="fresh">Fresh</option>
        <option value="ripe">Ripe</option>
        <option value="overripe">Overripe</option>
        <option value="spoiled">Spoiled</option>
      </select>
    </label>

    <div className="phoneHelp">
      <CheckCircle2 size={17}/>
      <p>Select Front, Left/Right and Back/Top while physically moving around the fruit. Frames continue uploading automatically.</p>
    </div>

    <div className="phoneHelp">
      <RefreshCw size={17}/>
      <p>{frames} frames uploaded in this session. Keep this page open while scanning.</p>
    </div>
  </div>;
}

createRoot(document.getElementById('phone-root')).render(<PhoneVisionApp />);
