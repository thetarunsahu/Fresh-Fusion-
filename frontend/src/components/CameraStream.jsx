import { useEffect, useRef, useState } from 'react';
import { Camera, CircleStop, RefreshCw, ShieldCheck, Upload } from 'lucide-react';
import { uploadImage, uploadStreamFrame } from '../api';

const isPhone = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
const views = ['front','back','left','right','top'];

export default function CameraStream({ sampleId, groundTruth = '', onFrame, compact = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const busyRef = useRef(false);
  const intervalRef = useRef(2500);
  const fileRef = useRef(null);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(0);
  const [intervalMs, setIntervalMs] = useState(2500);
  const [view, setView] = useState('front');

  const stop = () => {
    clearTimeout(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setRunning(false);
    setStatus('stopped');
  };

  const captureAndSend = async () => {
    if (!streamRef.current || !videoRef.current || busyRef.current || !sampleId) return;
    const video = videoRef.current;
    if (!video.videoWidth || !video.videoHeight) return;
    busyRef.current = true;
    setStatus('sending');
    try {
      const maxWidth = 960;
      const scale = Math.min(1, maxWidth / video.videoWidth);
      const width = Math.max(320, Math.round(video.videoWidth * scale));
      const height = Math.max(240, Math.round(video.videoHeight * scale));
      const canvas = canvasRef.current;
      canvas.width = width;
      canvas.height = height;
      canvas.getContext('2d', {alpha:false}).drawImage(video, 0, 0, width, height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.82));
      if (!blob) throw new Error('Could not create camera frame');
      const file = new File([blob], `live-${view}-${Date.now()}.jpg`, {type:'image/jpeg'});
      const result = await uploadStreamFrame(sampleId, view, groundTruth, file);
      setSent(v => v + 1);
      setStatus('live');
      onFrame?.(result);
    } catch (e) {
      setError(e.message || String(e));
      setStatus('error');
    } finally {
      busyRef.current = false;
    }
  };

  const schedule = () => {
    clearTimeout(timerRef.current);
    if (!streamRef.current) return;
    timerRef.current = setTimeout(async () => {
      await captureAndSend();
      schedule();
    }, intervalRef.current);
  };

  const start = async () => {
    setError('');
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Live camera needs HTTPS and camera permission.');
      setStatus('blocked');
      return;
    }
    try {
      setStatus('requesting');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio:false,
        video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}
      });
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      setRunning(true);
      setStatus('live');
      schedule();
    } catch (e) {
      setError(e?.name === 'NotAllowedError' ? 'Camera permission was not granted. Allow camera access and tap Start camera.' : (e.message || String(e)));
      setStatus('blocked');
    }
  };

  const changeInterval = e => {
    const next = Number(e.target.value);
    setIntervalMs(next);
    intervalRef.current = next;
    if (streamRef.current) schedule();
  };

  const manualFile = async e => {
    const file = e.target.files?.[0];
    if (!file || !sampleId) return;
    try {
      setStatus('sending');
      const result = await uploadImage(sampleId, view, groundTruth, file);
      setSent(v => v + 1);
      setStatus(running ? 'live' : 'idle');
      onFrame?.(result);
    } catch (x) {
      setError(x.message || String(x));
      setStatus('error');
    } finally {
      e.target.value = '';
    }
  };

  useEffect(() => {
    if (sampleId && isPhone()) {
      const id = setTimeout(start, 450);
      return () => { clearTimeout(id); stop(); };
    }
    return () => stop();
  }, [sampleId]);

  return <div className={`cameraModule ${compact ? 'compact' : ''}`}>
    <div className="cameraHead">
      <div>
        <span>PHONE VISION</span>
        <h2>{compact ? 'Keep the fruit inside the guide' : 'Continuous camera stream'}</h2>
      </div>
      <div className={`streamState ${status}`}><i></i>{status === 'live' ? 'LIVE' : status.toUpperCase()}</div>
    </div>

    <div className="viewSteps" aria-label="Fruit view selector">
      {views.map(v => <button key={v} className={view === v ? 'selected' : ''} onClick={() => setView(v)}>{v}</button>)}
    </div>

    <div className="videoStage">
      <video ref={videoRef} autoPlay muted playsInline />
      {!running && <div className="cameraEmpty"><Camera size={34}/><b>Camera not active</b><span>Open this page on the phone and allow rear-camera access.</span></div>}
      {running && <><div className="focusFrame"></div><div className="liveCorner">{view.toUpperCase()} · AUTO {intervalMs/1000}s</div></>}
    </div>
    <canvas ref={canvasRef} hidden />

    <div className="cameraControls">
      {!running ? <button className="primary" onClick={start}><Camera size={17}/> Start camera</button> : <button className="danger" onClick={stop}><CircleStop size={17}/> Stop</button>}
      <label className="field"><span>Send every</span><select value={intervalMs} onChange={changeInterval}><option value="1500">1.5 sec</option><option value="2500">2.5 sec</option><option value="5000">5 sec</option><option value="10000">10 sec</option></select></label>
      {!compact && <><button className="ghost" onClick={() => fileRef.current?.click()}><Upload size={16}/> Upload fallback</button><input ref={fileRef} type="file" accept="image/*" capture="environment" hidden onChange={manualFile}/></>}
    </div>

    <div className="cameraMeta">
      <span><ShieldCheck size={14}/> rear camera</span>
      <span><RefreshCw size={14}/> {sent} frames sent</span>
      <span>Current view: {view}</span>
    </div>
    {error && <div className="cameraError">{error}</div>}
  </div>;
}
