import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CheckCircle2, Leaf, RefreshCw, WifiOff } from 'lucide-react';
import CameraStream from './components/CameraStream';
import { createSample, health, listSamples } from './api';
import './styles.css';

function PhoneVisionApp() {
  const [online, setOnline] = useState(false);
  const [sample, setSample] = useState(null);
  const [truth, setTruth] = useState('');
  const [error, setError] = useState('');
  const [frames, setFrames] = useState(0);
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

  return <div className="phoneNodePage">
    <div className="phoneTopbar">
      <div className="brandLine">
        <div className="logoMark"><Leaf size={18}/></div>
        <div><b>FreshFusion</b><span>Phone Vision Node</span></div>
      </div>
      <span className={online ? 'phoneOnline on' : 'phoneOnline'}>
        {online ? 'connected' : 'offline'}
      </span>
    </div>

    <div className="phoneSample">
      <span>Active sample</span>
      <b>{sample ? `${sample.fruit_type} · ${sample.sample_id}` : 'Connecting...'}</b>
      <small>Keep the fruit centered. FreshFusion automatically selects Apple or Banana after reliable camera evidence and follows a new sample if the fruit changes.</small>
    </div>

    {error && <div className="errorBox"><WifiOff size={15}/> {error}</div>}

    <CameraStream
      sampleId={sample?.sample_id}
      groundTruth={truth}
      compact
      autoStart
      onFrame={() => setFrames(v => v + 1)}
    />

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
      <p>Select Front, Back, Left, Right or Top as you move around the detected fruit. Frames continue uploading automatically.</p>
    </div>

    <div className="phoneHelp">
      <RefreshCw size={17}/>
      <p>{frames} frames uploaded in this session. Keep this page open while scanning.</p>
    </div>
  </div>;
}

createRoot(document.getElementById('phone-root')).render(<PhoneVisionApp />);
