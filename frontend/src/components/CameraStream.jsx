import { useEffect, useRef, useState } from 'react';
import { Camera, CircleStop, RefreshCw, ShieldCheck, Smartphone, Upload } from 'lucide-react';
import { uploadImage, uploadStreamFrame } from '../api';

const isPhone = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

export default function CameraStream({ sampleId, groundTruth = '', onFrame }) {
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
      const file = new File([blob], `live-${Date.now()}.jpg`, {type:'image/jpeg'});
      const result = await uploadStreamFrame(sampleId, groundTruth, file);
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
      setError('Live camera needs a secure HTTPS page on the phone.');
      setStatus('blocked');
      return;
    }
    try {
      setStatus('requesting');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: {ideal:'environment'},
          width: {ideal:1280},
          height: {ideal:720},
        },
      });
      streamRef.current = stream;
      const video = videoRef.current;
      video.srcObject = stream;
      await video.play();
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
      const result = await uploadImage(sampleId, 'manual', groundTruth, file);
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
      const id = setTimeout(start, 350);
      return () => { clearTimeout(id); stop(); };
    }
    return () => stop();
  }, [sampleId]);

  return <div className="cameraModule">
    <div className="cameraHead">
      <div><span className="eyebrow">PHONE VISION NODE</span><h2>Continuous camera intelligence</h2></div>
      <div className={`streamState ${status}`}><i></i>{status === 'live' ? 'LIVE' : status.toUpperCase()}</div>
    </div>

    <div className="videoStage">
      <video ref={videoRef} autoPlay muted playsInline />
      {!running && <div className="cameraEmpty"><Smartphone size={36}/><b>Phone camera waiting</b><span>On the first visit your browser will ask for camera permission.</span></div>}
      {running && <><div className="focusFrame"></div><div className="liveCorner">AUTO FRAME · {intervalMs/1000}s</div></>}
    </div>
    <canvas ref={canvasRef} hidden />

    <div className="cameraControls">
      {!running ? <button className="primary" onClick={start}><Camera size={17}/> Start camera</button> : <button className="danger" onClick={stop}><CircleStop size={17}/> Stop stream</button>}
      <label className="field"><span>Frame interval</span><select value={intervalMs} onChange={changeInterval}><option value="1500">1.5 sec</option><option value="2500">2.5 sec</option><option value="5000">5 sec</option><option value="10000">10 sec</option></select></label>
      <button className="ghost" onClick={() => fileRef.current?.click()}><Upload size={16}/> Upload fallback</button>
      <input ref={fileRef} type="file" accept="image/*" capture="environment" hidden onChange={manualFile}/>
    </div>

    <div className="cameraMeta">
      <span><ShieldCheck size={14}/> rear camera preferred</span>
      <span><RefreshCw size={14}/> {sent} frames sent</span>
      <span>JPEG · max 960px · automatic analysis</span>
    </div>
    {error && <div className="cameraError">{error}</div>}
  </div>;
}
