import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Camera, CheckCircle2, CloudSun, FlaskConical, Gauge, Leaf, RefreshCw, Smartphone, Thermometer, Wifi, WifiOff } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { QRCodeSVG } from 'qrcode.react';
import CameraStream from './components/CameraStream';
import { API_ROOT, bundle, context, createSample, fuse, health, listSamples, pushReading, wsUrl } from './api';

const fmt = (v, d=1) => v == null ? '--' : Number(v).toFixed(d);
const isPhone = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
const views = ['front','back','left','right','top'];

function Status({ok,label,detail}) {
  return <div className="statusItem"><span className={ok ? 'statusDot ok' : 'statusDot'}></span><div><b>{label}</b><small>{detail}</small></div></div>;
}

function Metric({icon:Icon,label,value,unit,detail}) {
  return <div className="metricCard"><div className="metricIcon"><Icon size={18}/></div><div><span>{label}</span><strong>{value}<small>{unit}</small></strong><p>{detail}</p></div></div>;
}

function EvidenceCard({label,image,empty='Waiting for image'}) {
  return <div className="evidenceCard"><div className="evidenceLabel">{label}</div>{image ? <img src={image} alt={label}/> : <div className="imageEmpty">{empty}</div>}</div>;
}

export default function App(){
  const [online,setOnline]=useState(false);
  const [healthInfo,setHealthInfo]=useState(null);
  const [sample,setSample]=useState(null);
  const [data,setData]=useState({sensors:[],images:[],fusion:null});
  const [external,setExternal]=useState(null);
  const [fruitType,setFruitType]=useState('Banana');
  const [truth,setTruth]=useState('');
  const [recent,setRecent]=useState([]);
  const [busy,setBusy]=useState('');
  const [err,setErr]=useState('');
  const booted=useRef(false);
  const phoneClient=isPhone();

  const latest=data.sensors.at(-1)||{};
  const latestImage=data.images?.[0]||null;
  const analysis=latestImage?.analysis||{};
  const color=analysis.color||{};
  const texture=analysis.texture||{};
  const defects=analysis.defects||{};
  const issues=analysis.issues||[];
  const fusion=data.fusion||{};
  const score=fusion.freshness_score;
  const sensorConnected=Boolean(latest.device_id);
  const phoneConnected=Boolean(latestImage && (Date.now()-new Date(latestImage.uploaded_at).getTime()) < 20000);
  const chart=useMemo(()=>data.sensors.slice(-80).map((r,i)=>({i,temperature:r.temperature,humidity:r.humidity,gas:r.gas_ppm ?? r.mq135_raw})),[data.sensors]);
  const phoneUrl=healthInfo?.phone_dashboard || window.location.href;
  const colorRows=(sample?.fruit_type||fruitType).toLowerCase()==='apple'
    ? [['Red',color.red_pct],['Green',color.green_pct],['Yellow',color.yellow_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]]
    : [['Yellow',color.yellow_pct],['Green',color.green_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]];

  const frameFor=view=>data.images.find(img=>img.angle===view||img.angle===`live-${view}`);
  const refresh=async(id=sample?.sample_id)=>{if(!id)return;try{setData(await bundle(id));}catch(x){setErr(x.message)}};
  const loadRecent=async()=>{try{setRecent(await listSamples())}catch{}};
  const newSample=async()=>{setBusy('sample');setErr('');try{const s=await createSample(fruitType);setSample(s);setData({sensors:[],images:[],fusion:null});await refresh(s.sample_id);await loadRecent();}catch(x){setErr(x.message)}finally{setBusy('')}};
  const recompute=async()=>{if(!sample)return;setBusy('fusion');try{await fuse(sample.sample_id);await refresh();}finally{setBusy('')}};
  const simulate=async()=>{if(!sample)return;const raw=680+Math.random()*450;await pushReading({sample_id:sample.sample_id,device_id:'SIMULATOR',temperature:25+Math.random()*4,humidity:56+Math.random()*16,mq135_raw:raw,gas_ppm:raw*.5,voc_index:Math.max(0,(raw-500)/10),rssi:-48});};
  const getWeather=()=>navigator.geolocation?.getCurrentPosition(async p=>setExternal(await context(sample?.fruit_type||fruitType,p.coords.latitude,p.coords.longitude)),async()=>setExternal(await context(sample?.fruit_type||fruitType)),{timeout:5000});

  useEffect(()=>{
    if(booted.current)return;booted.current=true;
    (async()=>{
      health().then(h=>{setOnline(true);setHealthInfo(h)}).catch(()=>setOnline(false));
      try{
        const rows=await listSamples();setRecent(rows);
        if(rows.length){const active=rows[0];setSample(active);setFruitType(active.fruit_type);await refresh(active.sample_id);}
        else{const s=await createSample('Banana');setSample(s);await refresh(s.sample_id);await loadRecent();}
      }catch(x){setErr(x.message)}
    })();
  },[]);

  useEffect(()=>{if(!sample)return;let ws;let retry;const connect=()=>{ws=new WebSocket(wsUrl(sample.sample_id));ws.onmessage=()=>refresh(sample.sample_id);ws.onclose=()=>{retry=setTimeout(connect,1500)}};connect();return()=>{clearTimeout(retry);ws?.close();};},[sample?.sample_id]);
  useEffect(()=>{if(sample)context(sample.fruit_type).then(setExternal).catch(()=>{});},[sample?.sample_id]);

  if(phoneClient){
    return <div className="phoneNodePage">
      <div className="phoneTopbar"><div className="brandLine"><div className="logoMark"><Leaf size={18}/></div><div><b>FreshFusion</b><span>Phone Vision Node</span></div></div><span className={online?'phoneOnline on':'phoneOnline'}>{online?'connected':'offline'}</span></div>
      <div className="phoneSample"><span>Active sample</span><b>{sample?.fruit_type||'Fruit'} · {sample?.sample_id||'connecting...'}</b><small>Frames from this phone are attached to the same sample as ESP32 telemetry.</small></div>
      {err&&<div className="errorBox">{err}</div>}
      <CameraStream sampleId={sample?.sample_id} groundTruth={truth} compact onFrame={()=>refresh()}/>
      <label className="truthSelect"><span>Dataset label (optional)</span><select value={truth} onChange={e=>setTruth(e.target.value)}><option value="">Unlabelled</option><option value="fresh">Fresh</option><option value="ripe">Ripe</option><option value="overripe">Overripe</option><option value="spoiled">Spoiled</option></select></label>
      <div className="phoneHelp"><CheckCircle2 size={17}/><p>Keep the fruit inside the guide. Move around it and switch Front / Back / Left / Right / Top. Images continue sending automatically.</p></div>
    </div>;
  }

  return <div className="dashboard">
    <header className="topbar">
      <div className="brandLine"><div className="logoMark"><Leaf size={18}/></div><div><b>FreshFusion</b><span>Fruit quality analysis</span></div></div>
      <div className="topActions"><select value={fruitType} onChange={e=>setFruitType(e.target.value)}><option>Banana</option><option>Apple</option><option>Orange</option><option>Mango</option></select><button className="secondary" onClick={newSample} disabled={busy==='sample'}>New sample</button><button className="primary" onClick={recompute}><RefreshCw size={15}/> Recompute</button></div>
    </header>

    <main className="content">
      <section className="contextRow">
        <div><span className="sectionKicker">ACTIVE ANALYSIS</span><h1>{sample?.fruit_type||fruitType} <small>{sample?.sample_id||'initialising'}</small></h1><p>Live sensor evidence and phone images are combined into one sample record.</p></div>
        <div className="statusBar"><Status ok={online} label="Backend" detail={online?'online':'offline'}/><Status ok={sensorConnected} label="ESP32" detail={sensorConnected?latest.device_id:'waiting'}/><Status ok={phoneConnected} label="Phone camera" detail={phoneConnected?'streaming':'waiting'}/></div>
      </section>

      {err&&<div className="errorBox">{err}</div>}

      <section className="primaryGrid">
        <div className="liveEvidence panel">
          <div className="panelHead"><div><span>VISUAL EVIDENCE</span><h2>What the camera sees now</h2></div><div className={phoneConnected?'liveBadge on':'liveBadge'}>{phoneConnected?'LIVE':'WAITING'}</div></div>
          <div className="mainImageWrap">{latestImage?<img src={latestImage.url} alt="Latest fruit frame"/>:<div className="largeEmpty"><Camera size={34}/><b>No phone image yet</b><span>Scan the phone QR and allow the camera.</span></div>}</div>
          <div className="viewRail">{views.map(view=>{const frame=frameFor(view);return <div className="viewThumb" key={view}>{frame?<img src={frame.url} alt={`${view} view`}/>:<div className="thumbEmpty">—</div>}<span>{view}</span></div>})}</div>
        </div>

        <div className="decisionPanel panel">
          <div className="panelHead"><div><span>SUMMARY</span><h2>Current condition</h2></div></div>
          <div className="scoreBlock"><strong>{score==null?'--':Math.round(score)}</strong><span>/100 freshness</span></div>
          <div className="resultLabel">{(fusion.label||'collecting').replace('-', ' ')}</div>
          <div className="summaryRows"><div><span>Confidence</span><b>{fmt(fusion.confidence,0)}%</b></div><div><span>Sensor score</span><b>{fmt(fusion.sensor_score,0)}</b></div><div><span>Vision score</span><b>{fmt(fusion.vision_score,0)}</b></div><div><span>Risk</span><b>{fusion.risk||'--'}</b></div></div>
          <p className="quietNote">Prototype score for research and calibration; not a food-safety verdict.</p>
        </div>
      </section>

      <section className="metricGrid">
        <Metric icon={Thermometer} label="Temperature" value={fmt(latest.temperature)} unit="°C" detail="Chamber"/>
        <Metric icon={Activity} label="Humidity" value={fmt(latest.humidity)} unit="%" detail="Relative humidity"/>
        <Metric icon={Gauge} label="Gas signal" value={fmt(latest.gas_ppm ?? latest.mq135_raw,0)} unit={latest.gas_ppm?' ppm':' raw'} detail="MQ sensor"/>
        <Metric icon={sensorConnected?Wifi:WifiOff} label="ESP32 link" value={fmt(latest.rssi,0)} unit=" dBm" detail={latest.device_id||'Not connected'}/>
      </section>

      <section className="twoCol">
        <div className="panel telemetryPanel"><div className="panelHead"><div><span>SENSOR TREND</span><h2>Recent environment</h2></div><button className="textButton" onClick={simulate}>Send test packet</button></div><div className="chartWrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><CartesianGrid stroke="#e6e9ed" vertical={false}/><XAxis dataKey="i" hide/><YAxis stroke="#7b8490" fontSize={11}/><Tooltip/><Area type="monotone" dataKey="temperature" stroke="#247a57" fill="#247a5714" strokeWidth={2}/><Area type="monotone" dataKey="humidity" stroke="#3b6aa0" fillOpacity={0}/><Area type="monotone" dataKey="gas" stroke="#a56b20" fillOpacity={0}/></AreaChart></ResponsiveContainer></div><div className="legend"><span><i className="g"></i>Temperature</span><span><i className="b"></i>Humidity</span><span><i className="y"></i>Gas</span><small>{data.sensors.length} readings</small></div></div>

        <div className="pairPanel panel"><div className="panelHead"><div><span>PHONE CONNECTION</span><h2>Connect the camera node</h2></div><Smartphone size={20}/></div><div className="pairBody"><div><ol><li>Phone and laptop on the same Wi‑Fi.</li><li>Scan this code.</li><li>Allow camera once.</li><li>Camera starts sending frames automatically.</li></ol><small>{phoneUrl}</small></div><div className="qrBox"><QRCodeSVG value={phoneUrl} size={132} bgColor="#ffffff" fgColor="#17221d"/></div></div></div>
      </section>

      <section className="panel evidencePanel"><div className="panelHead"><div><span>IMAGE ANALYSIS</span><h2>Evidence, not decoration</h2></div><FlaskConical size={20}/></div><div className="evidenceGrid"><EvidenceCard label="Original" image={latestImage?.url}/><EvidenceCard label="Defect overlay" image={analysis.artifacts?.defect_overlay}/><EvidenceCard label="Texture map" image={analysis.artifacts?.texture}/><EvidenceCard label="Fruit mask" image={analysis.artifacts?.mask}/><EvidenceCard label="Edge map" image={analysis.artifacts?.edges}/></div></section>

      <section className="analysisGrid">
        <div className="panel"><div className="panelHead"><div><span>OBSERVATIONS</span><h2>What needs attention</h2></div></div><div className="issueList">{issues.length?issues.map((issue,i)=><div className={`issue ${issue.severity}`} key={`${issue.label}-${i}`}><div><b>{issue.label}</b><span>{issue.note}</span></div><strong>{fmt(issue.value)}{issue.label.toLowerCase().includes('rough')?'':'%'}</strong></div>):<div className="noIssues">No strong visual warning has been detected in the latest frame.</div>}</div></div>

        <div className="panel"><div className="panelHead"><div><span>COLOR</span><h2>{sample?.fruit_type||fruitType} surface profile</h2></div></div><div className="barList">{colorRows.map(([name,value])=><div key={name}><div><span>{name}</span><b>{fmt(value)}%</b></div><progress max="100" value={value||0}></progress></div>)}</div></div>

        <div className="panel"><div className="panelHead"><div><span>TEXTURE</span><h2>Surface structure</h2></div></div><div className="dataRows"><div><span>Entropy</span><b>{fmt(texture.entropy,2)}</b></div><div><span>Roughness</span><b>{fmt(texture.roughness_index)}</b></div><div><span>Edge density</span><b>{fmt(texture.edge_density_pct)}%</b></div><div><span>Laplacian variance</span><b>{fmt(texture.laplacian_variance,0)}</b></div><div><span>Healthy surface estimate</span><b>{fmt(defects.healthy_surface_estimate_pct,0)}%</b></div></div></div>
      </section>

      <details className="detailPanel panel"><summary>External context and experimental details</summary><div className="detailContent"><div><h3>Outside environment</h3><p>Temperature: <b>{fmt(external?.weather?.temperature_c)}°C</b> · Humidity: <b>{fmt(external?.weather?.humidity_pct)}%</b></p><p>Reference storage: <b>{external?.baseline?.storage_temp_c||'--'}°C</b> · RH: <b>{external?.baseline?.relative_humidity_pct||'--'}%</b></p><button className="secondary" onClick={getWeather}><CloudSun size={15}/> Use current location</button></div><div><h3>Recent samples</h3><div className="recentSamples">{recent.slice(0,6).map(s=><button key={s.sample_id} onClick={()=>{setSample(s);setFruitType(s.fruit_type);refresh(s.sample_id)}}>{s.fruit_type}<small>{s.sample_id}</small></button>)}</div></div></div></details>
    </main>
  </div>;
}
