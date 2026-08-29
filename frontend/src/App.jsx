import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Camera, Cloud, Database, FlaskConical, Gauge, Leaf, Radio, RefreshCw, Smartphone, Thermometer, Wifi, WifiOff } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { QRCodeSVG } from 'qrcode.react';
import FruitTwin from './components/FruitTwin';
import CameraStream from './components/CameraStream';
import { API_ROOT, bundle, context, createSample, fuse, health, listSamples, pushReading, wsUrl } from './api';

const fmt = (v, d=1) => v == null ? '--' : Number(v).toFixed(d);
function Metric({icon:Icon,label,value,unit,sub,live}){return <div className="metric glass"><div className="metricTop"><div className="metricIcon"><Icon size={18}/></div>{live&&<span className="pulseTag">LIVE</span>}</div><span>{label}</span><strong>{value}<small>{unit}</small></strong><p>{sub}</p></div>}
function Ring({value=0}){const p=Math.max(0,Math.min(100,Number(value)||0));return <div className="ring" style={{'--p':`${p}%`}}><div><strong>{Math.round(p)}</strong><span>/100</span><small>freshness</small></div></div>}

export default function App(){
  const [online,setOnline]=useState(false);
  const [sample,setSample]=useState(null);
  const [data,setData]=useState({sensors:[],images:[],fusion:null});
  const [external,setExternal]=useState(null);
  const [fruitType,setFruitType]=useState('Banana');
  const [truth,setTruth]=useState('');
  const [recent,setRecent]=useState([]);
  const [busy,setBusy]=useState('');
  const [err,setErr]=useState('');
  const booted=useRef(false);

  const latest=data.sensors.at(-1)||{};
  const fusion=data.fusion||{};
  const analysis=data.images?.[0]?.analysis||{};
  const color=analysis.color||{}, texture=analysis.texture||{}, defects=analysis.defects||{};
  const score=fusion.freshness_score ?? 68;
  const sensorConnected=Boolean(latest.device_id);
  const chart=useMemo(()=>data.sensors.slice(-80).map((r,i)=>({i,temperature:r.temperature,humidity:r.humidity,gas:r.gas_ppm ?? r.mq135_raw})),[data.sensors]);

  const refresh=async(id=sample?.sample_id)=>{if(!id)return;try{setData(await bundle(id));}catch(x){setErr(x.message)}};
  const loadRecent=async()=>{try{setRecent(await listSamples())}catch{}};
  const newSample=async()=>{setBusy('sample');setErr('');try{const s=await createSample(fruitType);setSample(s);setData({sensors:[],images:[],fusion:null});await refresh(s.sample_id);await loadRecent();}catch(x){setErr(x.message)}finally{setBusy('')}};
  const recompute=async()=>{if(!sample)return;setBusy('fusion');try{await fuse(sample.sample_id);await refresh();}finally{setBusy('')}};
  const simulate=async()=>{if(!sample)return;const raw=680+Math.random()*450;await pushReading({sample_id:sample.sample_id,device_id:'SIMULATOR',temperature:25+Math.random()*4,humidity:56+Math.random()*16,mq135_raw:raw,gas_ppm:raw*.5,voc_index:Math.max(0,(raw-500)/10),rssi:-48});};
  const getWeather=()=>navigator.geolocation?.getCurrentPosition(async p=>setExternal(await context(sample?.fruit_type||fruitType,p.coords.latitude,p.coords.longitude)),async()=>setExternal(await context(sample?.fruit_type||fruitType)),{timeout:5000});

  useEffect(()=>{
    if(booted.current)return;booted.current=true;
    (async()=>{
      health().then(()=>setOnline(true)).catch(()=>setOnline(false));
      try{
        const rows=await listSamples();setRecent(rows);
        if(rows.length){const active=rows[0];setSample(active);setFruitType(active.fruit_type);await refresh(active.sample_id);}
        else{const s=await createSample('Banana');setSample(s);await refresh(s.sample_id);await loadRecent();}
      }catch(x){setErr(x.message)}
    })();
  },[]);

  useEffect(()=>{if(!sample)return;let ws;let retry;const connect=()=>{ws=new WebSocket(wsUrl(sample.sample_id));ws.onmessage=()=>refresh(sample.sample_id);ws.onclose=()=>{retry=setTimeout(connect,1500)}};connect();return()=>{clearTimeout(retry);ws?.close();};},[sample?.sample_id]);
  useEffect(()=>{if(sample)context(sample.fruit_type).then(setExternal).catch(()=>{});},[sample?.sample_id]);

  return <div className="appShell">
    <aside className="sidebar">
      <div className="brand"><div className="brandMark"><Leaf/></div><div><b>FreshFusion</b><span>Fruit Intelligence OS</span></div></div>
      <nav>{[[Gauge,'Overview'],[Camera,'Live Scan'],[Leaf,'3D Twin'],[FlaskConical,'Vision Lab'],[Radio,'Sensor Lab'],[Activity,'Fusion Engine'],[Database,'History'],[Cloud,'External Data']].map(([I,t],i)=><button className={i===0?'active':''} key={t}><I size={17}/>{t}</button>)}</nav>
      <div className="sideStatus"><span className={online?'dot on':'dot'}></span><div><b>{online?'Backend online':'Backend offline'}</b><small>{API_ROOT}</small></div></div>
    </aside>

    <main>
      <header>
        <div><span className="eyebrow">REAL-TIME MULTIMODAL FRESHNESS LAB</span><h1>Fruit intelligence,<br/><em>streamed continuously.</em></h1><p>ESP32 telemetry arrives automatically while a phone acts as a live vision node, sending camera frames into the same fruit sample.</p></div>
        <div className="headerActions"><select value={fruitType} onChange={e=>setFruitType(e.target.value)}><option>Banana</option><option>Apple</option><option>Orange</option><option>Mango</option></select><button className="ghost" onClick={newSample} disabled={busy==='sample'}>+ New sample</button><button className="primary" onClick={recompute}><RefreshCw size={16}/> Recompute</button></div>
      </header>

      <div className="systemStrip glass">
        <div><span className={online?'statusOrb on':'statusOrb'}></span><b>Backend</b><small>{online?'connected':'offline'}</small></div>
        <div><span className={sensorConnected?'statusOrb on':'statusOrb'}></span><b>ESP32</b><small>{sensorConnected?latest.device_id:'waiting for telemetry'}</small></div>
        <div><span className={data.images.length?'statusOrb on':'statusOrb'}></span><b>Vision node</b><small>{data.images.length?`${data.images.length} frames in active buffer`:'waiting for phone'}</small></div>
        <div><span className="statusOrb on"></span><b>Active sample</b><small>{sample?.sample_id||'initialising'}</small></div>
      </div>
      {err&&<div className="error">{err}</div>}

      <section className="heroGrid">
        <div className="twin glass"><div className="panelTitle"><div><span>DIGITAL TWIN</span><h2>{sample?.fruit_type||'Fruit'} · {sample?.sample_id||'...'}</h2></div><div className="liveChip"><span></span>3D DATA TWIN</div></div><div className="canvasWrap"><FruitTwin fruit={sample?.fruit_type} score={score}/><div className="scanLines"></div></div><div className="twinFoot"><span>Drag to rotate</span><span>Surface reacts to score</span><span>{data.images.length} vision frames</span></div></div>
        <div className="scorePanel glass"><span className="eyebrow">FUSION ENGINE</span><Ring value={score}/><h3 className={`label ${fusion.label||'collecting'}`}>{(fusion.label||'COLLECTING').toUpperCase()}</h3><div className="confidence"><span>Confidence</span><b>{fmt(fusion.confidence,0)}%</b></div><div className="scoreSplit"><div><small>Sensor</small><b>{fmt(fusion.sensor_score,0)}</b></div><div><small>Vision</small><b>{fmt(fusion.vision_score,0)}</b></div><div><small>Risk</small><b>{fusion.risk||'--'}</b></div></div><p className="disclaimer">Prototype intelligence score; calibrate on labelled experimental data before scientific claims.</p></div>
      </section>

      <section className="metrics">
        <Metric icon={Thermometer} label="Temperature" value={fmt(latest.temperature)} unit="°C" sub="ESP32 chamber" live={sensorConnected}/>
        <Metric icon={Activity} label="Humidity" value={fmt(latest.humidity)} unit="%" sub="ESP32 chamber" live={sensorConnected}/>
        <Metric icon={Gauge} label="Gas signal" value={fmt(latest.gas_ppm ?? latest.mq135_raw,0)} unit={latest.gas_ppm?' ppm':' raw'} sub="MQ sensor" live={sensorConnected}/>
        <Metric icon={sensorConnected?Wifi:WifiOff} label="ESP32 link" value={fmt(latest.rssi,0)} unit=" dBm" sub={latest.device_id||'connect board + Wi-Fi'} live={sensorConnected}/>
      </section>

      <section className="liveGrid">
        <div className="glass cameraCard"><CameraStream sampleId={sample?.sample_id} groundTruth={truth} onFrame={()=>refresh()}/><div className="truthRow"><span>Optional ground-truth label for dataset building</span><select value={truth} onChange={e=>setTruth(e.target.value)}><option value="">Unlabelled</option><option value="fresh">Fresh</option><option value="ripe">Ripe</option><option value="overripe">Overripe</option><option value="spoiled">Spoiled</option></select></div></div>
        <div className="telemetry glass"><div className="panelTitle"><div><span>ESP32 LIVE BUS</span><h2>Sensor telemetry</h2></div><button className="mini" onClick={simulate}>Test packet</button></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#62f59c" stopOpacity=".35"/><stop offset="1" stopColor="#62f59c" stopOpacity="0"/></linearGradient></defs><CartesianGrid stroke="#173326" vertical={false}/><XAxis dataKey="i" hide/><YAxis stroke="#5a7568" fontSize={11}/><Tooltip contentStyle={{background:'#07120d',border:'1px solid #234737'}}/><Area type="monotone" dataKey="temperature" stroke="#62f59c" fill="url(#g1)" strokeWidth={2}/><Area type="monotone" dataKey="humidity" stroke="#8dd7ff" fillOpacity={0}/><Area type="monotone" dataKey="gas" stroke="#ffd76b" fillOpacity={0}/></AreaChart></ResponsiveContainer></div><div className="legend"><span className="green">Temperature</span><span className="blue">Humidity</span><span className="yellow">Gas</span><span>{data.sensors.length} readings buffered</span></div></div>
      </section>

      <section className="visionLab glass"><div className="panelTitle"><div><span>VISION LAB</span><h2>Latest streamed frame · processing artifacts · AI</h2></div><FlaskConical size={20}/></div><div className="visionGrid"><div className="visionCard"><span>LIVE FRAME</span>{data.images?.[0]?.url?<img src={data.images[0].url}/>:<div className="placeholder">Waiting for phone stream</div>}</div><div className="visionCard"><span>FRUIT MASK</span>{analysis.artifacts?.mask?<img src={analysis.artifacts.mask}/>:<div className="placeholder">Waiting</div>}</div><div className="visionCard"><span>DEFECT OVERLAY</span>{analysis.artifacts?.defect_overlay?<img src={analysis.artifacts.defect_overlay}/>:<div className="placeholder">Waiting</div>}</div><div className="visionCard"><span>EDGE MAP</span>{analysis.artifacts?.edges?<img src={analysis.artifacts.edges}/>:<div className="placeholder">Waiting</div>}</div></div><div className="aiStrip"><div><span className="eyebrow">AI MODEL</span><h3>{analysis.ai?.status==='ready'?`${analysis.ai.prediction} · ${fmt(analysis.ai.confidence)}%`:'Training-ready vision pipeline'}</h3><p>{analysis.ai?.status==='ready'?'Deep-learning output is included in the live vision score.':'Computer vision works now; real deep-learning prediction activates after labelled dataset training.'}</p></div><div className="probabilities">{Object.entries(analysis.ai?.probabilities||{}).map(([k,v])=><div key={k}><span>{k}</span><b>{fmt(v)}%</b></div>)}</div></div></section>

      <section className="intelligenceGrid"><div className="glass intel"><span className="eyebrow">COLOR INTELLIGENCE</span><h2>Surface chromatics</h2><div className="bars">{[['Yellow',color.yellow_pct],['Green',color.green_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]].map(([n,v])=><div key={n}><div><span>{n}</span><b>{fmt(v)}%</b></div><i><u style={{width:`${Math.min(100,v||0)}%`}}/></i></div>)}</div></div><div className="glass intel"><span className="eyebrow">TEXTURE INTELLIGENCE</span><h2>Surface structure</h2><div className="statRows"><div><span>Entropy</span><b>{fmt(texture.entropy,2)}</b></div><div><span>Roughness</span><b>{fmt(texture.roughness_index)}</b></div><div><span>Edge density</span><b>{fmt(texture.edge_density_pct)}%</b></div><div><span>Laplacian variance</span><b>{fmt(texture.laplacian_variance,0)}</b></div></div></div><div className="glass intel"><span className="eyebrow">DEFECT INTELLIGENCE</span><h2>Visible damage</h2><div className="bigStat">{fmt(defects.healthy_surface_estimate_pct,0)}<small>% healthy</small></div><div className="statRows"><div><span>Brown regions</span><b>{fmt(defects.brown_region_pct)}%</b></div><div><span>Dark regions</span><b>{fmt(defects.dark_region_pct)}%</b></div><div><span>Damage estimate</span><b>{fmt(defects.visible_damage_estimate_pct)}%</b></div></div></div></section>

      <section className="bottomGrid"><div className="glass external"><div className="panelTitle"><div><span>ONLINE CONTEXT</span><h2>Reference + live outside environment</h2></div><Cloud size={20}/></div><div className="externalStats"><div><small>Outside temp</small><b>{fmt(external?.weather?.temperature_c)}°C</b></div><div><small>Outside RH</small><b>{fmt(external?.weather?.humidity_pct)}%</b></div><div><small>Storage reference</small><b>{external?.baseline?.storage_temp_c||'--'}°C</b></div><div><small>Reference RH</small><b>{external?.baseline?.relative_humidity_pct||'--'}%</b></div></div><button className="ghost" onClick={getWeather}>Enable local live weather</button><p>{external?.weather?.source?`Live source: ${external.weather.source}. `:''}{external?.baseline?.note}</p></div><div className="glass phone"><div><span className="eyebrow">PHONE VISION PAIRING</span><h2>Scan → grant camera once → stream automatically</h2><p>Use the HTTPS dashboard address shown here. The first visit requires browser camera permission; after permission is granted the rear camera starts automatically on supported phones.</p></div><div className="qr"><QRCodeSVG value={window.location.href} size={126} bgColor="#07120d" fgColor="#66f3a3"/><small>{window.location.href}</small></div></div></section>

      <section className="history glass"><div className="panelTitle"><div><span>SAMPLE HISTORY</span><h2>Recent fruit sessions</h2></div><Database size={20}/></div><div className="historyRows">{recent.slice(0,8).map(s=><button key={s.sample_id} onClick={()=>{setSample(s);setFruitType(s.fruit_type);refresh(s.sample_id)}} className={s.sample_id===sample?.sample_id?'selected':''}><b>{s.sample_id}</b><span>{s.fruit_type}</span><small>{s.status||'collecting'}</small></button>)}</div></section>
    </main>
  </div>;
}
