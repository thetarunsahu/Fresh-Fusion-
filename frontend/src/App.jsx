import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Camera, Cloud, Database, FlaskConical, Gauge, ImagePlus, Leaf, Radio, RefreshCw, Smartphone, Thermometer, Wifi } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { QRCodeSVG } from 'qrcode.react';
import FruitTwin from './components/FruitTwin';
import { API_ROOT, bundle, context, createSample, fuse, health, listSamples, pushReading, uploadImage, wsUrl } from './api';

const angles=['front','back','left','right','top'];
const fmt=(v,d=1)=> v==null ? '--' : Number(v).toFixed(d);

function Metric({icon:Icon,label,value,unit,sub}){return <div className="metric glass"><div className="metricIcon"><Icon size={18}/></div><div><span>{label}</span><strong>{value}<small>{unit}</small></strong><p>{sub}</p></div></div>}
function Ring({value=0,label}){return <div className="ring" style={{'--p':`${Math.max(0,Math.min(100,value))}%`}}><div><strong>{Math.round(value)}</strong><span>/100</span><small>{label}</small></div></div>}

export default function App(){
  const [online,setOnline]=useState(false), [healthInfo,setHealthInfo]=useState(null), [sample,setSample]=useState(null), [data,setData]=useState({sensors:[],images:[],fusion:null}), [external,setExternal]=useState(null), [angle,setAngle]=useState('front'), [fruitType,setFruitType]=useState('Banana'), [truth,setTruth]=useState(''), [recent,setRecent]=useState([]), [busy,setBusy]=useState(''), [err,setErr]=useState('');
  const fileRef=useRef(); const booted=useRef(false);
  const latest=data.sensors.at(-1)||{}; const fusion=data.fusion||{}; const score=fusion.freshness_score ?? 68;
  const chart=useMemo(()=>data.sensors.slice(-60).map((r,i)=>({i,temperature:r.temperature,humidity:r.humidity,gas:r.gas_ppm ?? r.mq135_raw})),[data.sensors]);

  const refresh=async(id=sample?.sample_id)=>{if(!id)return; const b=await bundle(id); setData(b);};
  const loadRecent=async()=>{try{setRecent(await listSamples())}catch{}};
  const newSample=async()=>{setBusy('sample');try{const s=await createSample(fruitType);setSample(s);await refresh(s.sample_id);await loadRecent();}finally{setBusy('')}};
  const simulate=async()=>{if(!sample)return; const t=26+Math.random()*2,h=58+Math.random()*12,raw=650+Math.random()*400; await pushReading({sample_id:sample.sample_id,device_id:'SIMULATOR',temperature:t,humidity:h,mq135_raw:raw,gas_ppm:raw*.55,voc_index:Math.max(0,(raw-500)/10),rssi:-48}); await refresh();};
  const doFuse=async()=>{if(!sample)return;setBusy('fusion');try{await fuse(sample.sample_id);await refresh();}finally{setBusy('')}};
  const onFile=async(e)=>{const f=e.target.files?.[0]; if(!f||!sample)return;setBusy('image');setErr('');try{await uploadImage(sample.sample_id,angle,truth,f);await doFuse();}catch(x){setErr(x.message)}finally{setBusy('');e.target.value=''}};
  const loadExternal=()=>navigator.geolocation?.getCurrentPosition(async p=>setExternal(await context(sample?.fruit_type||'Banana',p.coords.latitude,p.coords.longitude)),async()=>setExternal(await context(sample?.fruit_type||'Banana')),{timeout:5000});

  useEffect(()=>{
    if(booted.current)return; booted.current=true;
    (async()=>{
      health().then(h=>{setOnline(true);setHealthInfo(h)}).catch(()=>setOnline(false));
      try{
        const rows=await listSamples(); setRecent(rows);
        if(rows.length){
          const active=rows[0]; setSample(active); setFruitType(active.fruit_type); await refresh(active.sample_id);
        }else{
          const s=await createSample('Banana'); setSample(s); await refresh(s.sample_id); await loadRecent();
        }
      }catch(x){setErr(x.message)}
    })();
  },[]);
  useEffect(()=>{if(!sample)return; const ws=new WebSocket(wsUrl(sample.sample_id)); ws.onmessage=()=>refresh(sample.sample_id); return()=>ws.close();},[sample?.sample_id]);
  useEffect(()=>{if(sample)loadExternal();},[sample?.sample_id]);

  const analysis=data.images?.[0]?.analysis||{}; const color=analysis.color||{}, texture=analysis.texture||{}, defects=analysis.defects||{};
  return <div className="appShell">
    <aside className="sidebar">
      <div className="brand"><div className="brandMark"><Leaf/></div><div><b>FreshFusion</b><span>Fruit Intelligence OS</span></div></div>
      <nav>{[[Gauge,'Overview'],[Camera,'Live Scan'],[Leaf,'3D Twin'],[FlaskConical,'Vision Lab'],[Radio,'Sensor Lab'],[Activity,'Fusion Engine'],[Database,'History'],[Cloud,'External Data']].map(([I,t],i)=><button className={i===0?'active':''} key={t}><I size={17}/>{t}</button>)}</nav>
      <div className="sideStatus"><span className={online?'dot on':'dot'}></span><div><b>{online?'Backend online':'Backend offline'}</b><small>{API_ROOT}</small></div></div>
    </aside>

    <main>
      <header><div><span className="eyebrow">LIVE MULTIMODAL ANALYSIS</span><h1>Fruit intelligence,<br/><em>not just classification.</em></h1><p>Sensor telemetry, phone imaging, computer vision, 3D digital twin, online context and multimodal freshness scoring in one system.</p></div><div className="headerActions"><select className="fruitSelect" value={fruitType} onChange={e=>setFruitType(e.target.value)}><option>Banana</option><option>Apple</option><option>Orange</option><option>Mango</option></select><button className="ghost" onClick={newSample}>+ New sample</button><button className="primary" onClick={doFuse}><RefreshCw size={16}/> Recompute fusion</button></div></header>

      {err&&<div className="error">{err}</div>}
      <section className="heroGrid">
        <div className="twin glass"><div className="panelTitle"><div><span>DIGITAL TWIN</span><h2>{sample?.fruit_type||'Fruit'} / {sample?.sample_id||'...'}</h2></div><div className="liveChip"><span></span>interactive 3D</div></div><div className="canvasWrap"><FruitTwin fruit={sample?.fruit_type} score={score}/><div className="scanLines"></div></div><div className="twinFoot"><span>Drag to rotate</span><span>Scroll to zoom</span><span>Score-linked surface</span></div></div>
        <div className="scorePanel glass"><span className="eyebrow">FUSION RESULT</span><Ring value={score} label="Freshness"/><h3 className={`label ${fusion.label||'collecting'}`}>{(fusion.label||'COLLECTING').toUpperCase()}</h3><div className="confidence"><span>Confidence</span><b>{fmt(fusion.confidence,0)}%</b></div><div className="scoreSplit"><div><small>Sensor score</small><b>{fmt(fusion.sensor_score,0)}</b></div><div><small>Vision score</small><b>{fmt(fusion.vision_score,0)}</b></div><div><small>Risk</small><b>{fusion.risk||'--'}</b></div></div><p className="disclaimer">Experimental score for prototype validation; not a food-safety verdict.</p></div>
      </section>

      <section className="metrics"><Metric icon={Thermometer} label="Temperature" value={fmt(latest.temperature)} unit="°C" sub="Chamber live"/><Metric icon={Activity} label="Humidity" value={fmt(latest.humidity)} unit="%" sub="Relative humidity"/><Metric icon={Gauge} label="Gas signal" value={fmt(latest.gas_ppm ?? latest.mq135_raw,0)} unit={latest.gas_ppm?' ppm':' raw'} sub="MQ telemetry"/><Metric icon={Wifi} label="ESP32 link" value={fmt(latest.rssi,0)} unit=" dBm" sub={latest.device_id||'Awaiting device'}/></section>

      <section className="workGrid">
        <div className="telemetry glass"><div className="panelTitle"><div><span>SENSOR TELEMETRY</span><h2>Live degradation environment</h2></div><button className="mini" onClick={simulate}>Push test reading</button></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#62f59c" stopOpacity=".35"/><stop offset="1" stopColor="#62f59c" stopOpacity="0"/></linearGradient></defs><CartesianGrid stroke="#173326" vertical={false}/><XAxis dataKey="i" hide/><YAxis stroke="#5a7568" fontSize={11}/><Tooltip contentStyle={{background:'#07120d',border:'1px solid #234737'}}/><Area type="monotone" dataKey="temperature" stroke="#62f59c" fill="url(#g1)" strokeWidth={2}/><Area type="monotone" dataKey="humidity" stroke="#8dd7ff" fillOpacity={0}/><Area type="monotone" dataKey="gas" stroke="#ffd76b" fillOpacity={0}/></AreaChart></ResponsiveContainer></div><div className="legend"><span className="green">Temperature</span><span className="blue">Humidity</span><span className="yellow">Gas</span><span>{data.sensors.length} readings stored</span></div></div>

        <div className="capture glass"><div className="panelTitle"><div><span>PHONE / CAMERA INPUT</span><h2>Multi-angle fruit scan</h2></div><Smartphone size={20}/></div><div className="angles">{angles.map(a=><button onClick={()=>setAngle(a)} className={angle===a?'sel':''} key={a}>{a}</button>)}</div><div className="labelRow"><span>Optional training label</span><select value={truth} onChange={e=>setTruth(e.target.value)}><option value="">Unlabelled</option><option value="fresh">Fresh</option><option value="ripe">Ripe</option><option value="overripe">Overripe</option><option value="spoiled">Spoiled</option></select></div><button className="captureButton" onClick={()=>fileRef.current?.click()} disabled={!sample||busy==='image'}><ImagePlus size={28}/><b>{busy==='image'?'Analysing image...':'Capture / upload image'}</b><span>Opens phone camera on supported devices</span></button><input ref={fileRef} type="file" accept="image/*" capture="environment" hidden onChange={onFile}/><div className="thumbs">{data.images.slice(0,5).map(img=><div key={img.id}><img src={img.url}/><span>{img.angle}</span></div>)}{!data.images.length&&<p>No fruit images yet. Capture front, back, left, right and top.</p>}</div></div>
      </section>

      <section className="visionLab glass">
        <div className="panelTitle"><div><span>VISION LAB</span><h2>Original image + processing artifacts + AI output</h2></div><FlaskConical size={20}/></div>
        <div className="visionGrid">
          <div className="visionCard"><span>ORIGINAL</span>{data.images?.[0]?.url ? <img src={data.images[0].url}/> : <div className="placeholder">Capture an image</div>}</div>
          <div className="visionCard"><span>FRUIT MASK</span>{analysis.artifacts?.mask ? <img src={analysis.artifacts.mask}/> : <div className="placeholder">Waiting</div>}</div>
          <div className="visionCard"><span>DEFECT OVERLAY</span>{analysis.artifacts?.defect_overlay ? <img src={analysis.artifacts.defect_overlay}/> : <div className="placeholder">Waiting</div>}</div>
          <div className="visionCard"><span>EDGE MAP</span>{analysis.artifacts?.edges ? <img src={analysis.artifacts.edges}/> : <div className="placeholder">Waiting</div>}</div>
        </div>
        <div className="aiStrip"><div><span className="eyebrow">AI MODEL</span><h3>{analysis.ai?.status==='ready' ? `${analysis.ai.prediction} · ${fmt(analysis.ai.confidence)}%` : 'Training-ready model pipeline'}</h3><p>{analysis.ai?.status==='ready' ? 'Deep-learning prediction is included in the vision score.' : 'Add labelled data and run ai/train.py to produce the real MobileNet freshness weights. Until then the system uses measurable CV + sensor fusion without pretending a model is trained.'}</p></div><div className="probabilities">{Object.entries(analysis.ai?.probabilities||{}).map(([k,v])=><div key={k}><span>{k}</span><b>{fmt(v)}%</b></div>)}</div></div>
      </section>

      <section className="intelligenceGrid">
        <div className="glass intel"><span className="eyebrow">COLOR INTELLIGENCE</span><h2>Surface chromatics</h2><div className="bars">{[['Yellow',color.yellow_pct],['Green',color.green_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]].map(([n,v])=><div key={n}><div><span>{n}</span><b>{fmt(v)}%</b></div><i><u style={{width:`${Math.min(100,v||0)}%`}}/></i></div>)}</div></div>
        <div className="glass intel"><span className="eyebrow">TEXTURE INTELLIGENCE</span><h2>Surface structure</h2><div className="statRows"><div><span>Entropy</span><b>{fmt(texture.entropy,2)}</b></div><div><span>Roughness index</span><b>{fmt(texture.roughness_index)}</b></div><div><span>Edge density</span><b>{fmt(texture.edge_density_pct)}%</b></div><div><span>Laplacian variance</span><b>{fmt(texture.laplacian_variance,0)}</b></div></div></div>
        <div className="glass intel"><span className="eyebrow">DEFECT INTELLIGENCE</span><h2>Visible damage estimate</h2><div className="bigStat">{fmt(defects.healthy_surface_estimate_pct,0)}<small>% healthy</small></div><div className="statRows"><div><span>Brown regions</span><b>{fmt(defects.brown_region_pct)}%</b></div><div><span>Dark regions</span><b>{fmt(defects.dark_region_pct)}%</b></div><div><span>Damage estimate</span><b>{fmt(defects.visible_damage_estimate_pct)}%</b></div></div></div>
      </section>

      <section className="bottomGrid">
        <div className="glass external"><div className="panelTitle"><div><span>ONLINE CONTEXT</span><h2>Outside world vs chamber</h2></div><Cloud size={20}/></div><div className="externalStats"><div><small>Outside temperature</small><b>{fmt(external?.weather?.temperature_c)}°C</b></div><div><small>Outside humidity</small><b>{fmt(external?.weather?.humidity_pct)}%</b></div><div><small>Reference storage</small><b>{external?.baseline?.storage_temp_c||'--'}°C</b></div><div><small>Reference RH</small><b>{external?.baseline?.relative_humidity_pct||'--'}%</b></div></div><p>{external?.weather?.source ? `Live weather source: ${external.weather.source}. `:''}{external?.baseline?.note}</p></div>
        <div className="glass phone"><div><span className="eyebrow">PHONE PAIRING</span><h2>Open this dashboard on your phone</h2><p>Phone and laptop must be on the same Wi‑Fi. Start Vite with <code>npm run dev -- --host 0.0.0.0</code> and backend with <code>uvicorn app.main:app --host 0.0.0.0 --reload</code>.</p></div><div className="qr"><QRCodeSVG value={healthInfo?.phone_dashboard || window.location.href} size={118} bgColor="#07120d" fgColor="#66f3a3"/><small>{healthInfo?.phone_dashboard || "Scan dashboard URL"}</small></div></div>
      </section>

      <section className="recent glass"><div className="panelTitle"><div><span>SAMPLE HISTORY</span><h2>Recent fruit records</h2></div><Database size={20}/></div><div className="recentRows">{recent.slice(0,8).map(r=><button key={r.sample_id} onClick={async()=>{setSample(r);setFruitType(r.fruit_type);await refresh(r.sample_id)}}><div><b>{r.sample_id}</b><span>{r.fruit_type}</span></div><em>{r.status}</em></button>)}</div></section>
    </main>
  </div>
}
