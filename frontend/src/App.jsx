import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Camera, CheckCircle2, CloudSun, Database, FlaskConical, Gauge, Leaf, RefreshCw, ShieldCheck, Smartphone, Thermometer, TriangleAlert, Wifi, WifiOff } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { QRCodeSVG } from 'qrcode.react';
import CameraStream from './components/CameraStream';
import { bundle, context, createSample, datasetRegistry, fuse, health, listSamples, pushReading, wsUrl } from './api';

const fmt = (v, d=1) => v == null ? '--' : Number(v).toFixed(d);
const isPhone = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(navigator.userAgent));
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

function physicalTitle(status){
  if(status==='physical_fruit_likely') return 'Physical fruit likely';
  if(status==='suspected_2d_display') return 'Screen / display suspected';
  if(status==='suspected_flat_reference') return 'Flat image suspected';
  if(status==='no_fruit') return 'No fruit verified';
  return 'Collecting physical evidence';
}

export default function App(){
  const [online,setOnline]=useState(false);
  const [healthInfo,setHealthInfo]=useState(null);
  const [sample,setSample]=useState(null);
  const [data,setData]=useState({sensors:[],images:[],fusion:null});
  const [external,setExternal]=useState(null);
  const [datasetInfo,setDatasetInfo]=useState(null);
  const [fruitType,setFruitType]=useState('Auto');
  const [truth,setTruth]=useState('');
  const [recent,setRecent]=useState([]);
  const [busy,setBusy]=useState('');
  const [err,setErr]=useState('');
  const booted=useRef(false);
  const phoneClient=isPhone();

  const latest=data.sensors.at(-1)||{};
  const latestImage=data.images?.[0]||null;
  const analysis=latestImage?.analysis||{};
  const identity=analysis.identity||{};
  const quality=analysis.quality||{};
  const presentation=analysis.presentation||{};
  const reference=analysis.reference_match||{};
  const color=analysis.color||{};
  const texture=analysis.texture||{};
  const defects=analysis.defects||{};
  const issues=analysis.issues||[];
  const fusion=data.fusion||{};
  const validation=fusion.components?.validation||{};
  const sensorConnected=Boolean(latest.device_id);
  const phoneConnected=Boolean(latestImage && (Date.now()-new Date(latestImage.uploaded_at).getTime()) < 20000);
  const fruitPresent=quality.fruit_present===true;
  const detectedFruit=identity.fruit && identity.fruit!=='Unknown' ? identity.fruit : null;
  const effectiveFruit=detectedFruit || (sample?.fruit_type && sample.fruit_type!=='Auto' ? sample.fruit_type : null);
  const verdictReady=validation.verdict_ready===true;
  const score=verdictReady ? fusion.freshness_score : null;
  const chart=useMemo(()=>data.sensors.slice(-80).map((r,i)=>({i,temperature:r.temperature,humidity:r.humidity,gas:r.gas_ppm ?? r.mq135_raw})),[data.sensors]);
  const phoneUrl=healthInfo?.phone_dashboard || window.location.href;
  const colorRows=(effectiveFruit||'').toLowerCase()==='apple'
    ? [['Red',color.red_pct],['Green',color.green_pct],['Yellow',color.yellow_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]]
    : [['Yellow',color.yellow_pct],['Green',color.green_pct],['Brown',color.brown_pct],['Dark',color.dark_pct]];

  const frameFor=view=>data.images.find(img=>img.angle===view||img.angle===`live-${view}`);
  const refresh=async(id=sample?.sample_id)=>{
    if(!id)return;
    try{
      const payload=await bundle(id);
      setData(payload);
      if(payload.sample){
        setSample(current=>current?.sample_id===payload.sample.sample_id?{...current,...payload.sample}:current);
        if(payload.sample.fruit_type)setFruitType(payload.sample.fruit_type);
      }
    }catch(x){setErr(x.message)}
  };
  const loadRecent=async()=>{try{const rows=await listSamples();setRecent(rows);return rows}catch{return[]}};
  const newSample=async()=>{setBusy('sample');setErr('');try{const s=await createSample(fruitType||'Auto');setSample(s);setData({sensors:[],images:[],fusion:null});await refresh(s.sample_id);await loadRecent();}catch(x){setErr(x.message)}finally{setBusy('')}};
  const recompute=async()=>{if(!sample)return;setBusy('fusion');try{await fuse(sample.sample_id);await refresh();}finally{setBusy('')}};
  const simulate=async()=>{if(!sample)return;const raw=680+Math.random()*450;await pushReading({sample_id:sample.sample_id,device_id:'SIMULATOR',temperature:25+Math.random()*4,humidity:56+Math.random()*16,mq135_raw:raw,gas_ppm:raw*.5,voc_index:Math.max(0,(raw-500)/10),rssi:-48});};
  const getWeather=()=>navigator.geolocation?.getCurrentPosition(async p=>setExternal(await context(effectiveFruit||'Banana',p.coords.latitude,p.coords.longitude)),async()=>setExternal(await context(effectiveFruit||'Banana')),{timeout:5000});

  useEffect(()=>{
    if(booted.current)return;booted.current=true;
    (async()=>{
      health().then(h=>{setOnline(true);setHealthInfo(h)}).catch(()=>setOnline(false));
      try{
        const rows=await listSamples();setRecent(rows);
        if(rows.length){const active=rows[0];setSample(active);setFruitType(active.fruit_type||'Auto');await refresh(active.sample_id);}
        else{const s=await createSample('Auto');setSample(s);setFruitType('Auto');await refresh(s.sample_id);await loadRecent();}
      }catch(x){setErr(x.message)}
    })();
  },[]);

  useEffect(()=>{
    const timer=setInterval(async()=>{
      try{
        const rows=await listSamples();setRecent(rows);
        const active=rows[0];
        if(active && active.sample_id!==sample?.sample_id){
          setSample(active);setFruitType(active.fruit_type||'Auto');await refresh(active.sample_id);
        }
      }catch{}
    },2500);
    return()=>clearInterval(timer);
  },[sample?.sample_id]);

  useEffect(()=>{if(!sample)return;let ws;let retry;const connect=()=>{ws=new WebSocket(wsUrl(sample.sample_id));ws.onmessage=()=>refresh(sample.sample_id);ws.onclose=()=>{retry=setTimeout(connect,1500)}};connect();return()=>{clearTimeout(retry);ws?.close();};},[sample?.sample_id]);
  useEffect(()=>{if(effectiveFruit)context(effectiveFruit).then(setExternal).catch(()=>{});},[effectiveFruit]);
  useEffect(()=>{datasetRegistry(effectiveFruit||undefined).then(setDatasetInfo).catch(()=>setDatasetInfo(null));},[effectiveFruit]);

  if(phoneClient){
    return <div className="phoneNodePage">
      <div className="phoneTopbar"><div className="brandLine"><div className="logoMark"><Leaf size={18}/></div><div><b>FreshFusion</b><span>Phone Vision Node</span></div></div><span className={online?'phoneOnline on':'phoneOnline'}>{online?'connected':'offline'}</span></div>
      <div className="phoneSample"><span>Active sample</span><b>{sample?.fruit_type||'Auto'} · {sample?.sample_id||'connecting...'}</b><small>Use the real fruit, not a photo or another screen. FreshFusion needs at least three genuinely different viewpoints before it releases a freshness verdict.</small></div>
      {err&&<div className="errorBox">{err}</div>}
      <CameraStream sampleId={sample?.sample_id} groundTruth={truth} compact autoStart onFrame={()=>refresh()}/>
      <label className="truthSelect"><span>Dataset label (optional)</span><select value={truth} onChange={e=>setTruth(e.target.value)}><option value="">Unlabelled</option><option value="fresh">Fresh</option><option value="ripe">Ripe</option><option value="overripe">Overripe</option><option value="spoiled">Spoiled</option></select></label>
      <div className="phoneHelp"><ShieldCheck size={17}/><p>Physical check: capture Front + Left/Right + Back/Top while moving around the actual fruit. A repeated flat image or obvious display can block the final verdict.</p></div>
      <div className="phoneHelp"><CheckCircle2 size={17}/><p>Images continue sending automatically as you change the selected view.</p></div>
    </div>;
  }

  return <div className="dashboard">
    <header className="topbar">
      <div className="brandLine"><div className="logoMark"><Leaf size={18}/></div><div><b>FreshFusion</b><span>Fruit quality analysis</span></div></div>
      <div className="topActions"><select value={fruitType} onChange={e=>setFruitType(e.target.value)}><option>Auto</option><option>Banana</option><option>Apple</option><option>Orange</option><option>Mango</option></select><button className="secondary" onClick={newSample} disabled={busy==='sample'}>New sample</button><button className="primary" onClick={recompute}><RefreshCw size={15}/> Recompute</button></div>
    </header>

    <main className="content">
      <section className="contextRow">
        <div><span className="sectionKicker">ACTIVE ANALYSIS</span><h1>{effectiveFruit||'Detecting fruit'} <small>{sample?.sample_id||'initialising'}</small></h1><p>{verdictReady?`Physical ${effectiveFruit||'fruit'} evidence and ESP32 telemetry are verified for the current multimodal result.`:fruitPresent?`Visual identity is ${effectiveFruit||'detected'}, but FreshFusion is still verifying that the camera is seeing a physical 3D fruit.`:'Place one real fruit inside the scan guide. Freshness scoring stays locked until physical evidence is verified.'}</p></div>
        <div className="statusBar"><Status ok={online} label="Backend" detail={online?'online':'offline'}/><Status ok={sensorConnected} label="ESP32" detail={sensorConnected?latest.device_id:'waiting'}/><Status ok={phoneConnected} label="Phone camera" detail={phoneConnected?'streaming':'waiting'}/></div>
      </section>

      {err&&<div className="errorBox">{err}</div>}

      <section className="identityStrip panel">
        <div><span className="sectionKicker">AUTO FRUIT IDENTITY</span><h2>{fruitPresent?(detectedFruit||'Fruit-like object detected'):'No reliable fruit detected'}</h2><p>{fruitPresent?`Visual identity confidence ${fmt(identity.confidence,0)}%. This identifies appearance only; it does not by itself prove the fruit is physically present.`:(quality.message||'Keep a single real fruit centered in the phone guide.')}</p></div>
        <div className="identityMeta"><div><span>Mode</span><b>Automatic</b></div><div><span>Supported now</span><b>Apple · Banana</b></div><div><span>Reference source</span><b>Fruits-360 + freshness data</b></div></div>
      </section>

      <section className={`validationStrip panel ${validation.status||'collecting_physical_evidence'}`}>
        <div className="validationLead">
          <div className="validationIcon">{validation.status==='physical_fruit_likely'?<ShieldCheck size={22}/>:<TriangleAlert size={22}/>}</div>
          <div><span className="sectionKicker">PHYSICAL FRUIT CHECK</span><h2>{physicalTitle(validation.status)}</h2><p>{validation.message||'Capture at least three changed viewpoints of the real fruit.'}</p></div>
        </div>
        <div className="validationMetrics">
          <div><span>Views verified</span><b>{validation.views_count||0}/3</b><small>{(validation.views||[]).join(' · ')||'waiting'}</small></div>
          <div><span>Screen/photo suspicion</span><b>{fmt(validation.screen_suspicion_pct,0)}%</b><small>lower is better</small></div>
          <div><span>Appearance change</span><b>{fmt(validation.appearance_diversity_pct,0)}%</b><small>multi-view diversity</small></div>
          <div><span>ESP32 evidence</span><b>{sensorConnected?'Present':'Waiting'}</b><small>{verdictReady?'final verdict unlocked':'required for final verdict'}</small></div>
        </div>
      </section>

      <section className="primaryGrid">
        <div className="liveEvidence panel">
          <div className="panelHead"><div><span>VISUAL EVIDENCE</span><h2>What the camera sees now</h2></div><div className={phoneConnected?'liveBadge on':'liveBadge'}>{phoneConnected?'LIVE':'WAITING'}</div></div>
          <div className="mainImageWrap">{latestImage?<img src={latestImage.url} alt="Latest fruit frame"/>:<div className="largeEmpty"><Camera size={34}/><b>No phone image yet</b><span>Scan the phone QR and allow the camera.</span></div>}</div>
          <div className="viewRail">{views.map(view=>{const frame=frameFor(view);return <div className="viewThumb" key={view}>{frame?<img src={frame.url} alt={`${view} view`}/>:<div className="thumbEmpty">—</div>}<span>{view}</span></div>})}</div>
        </div>

        <div className="decisionPanel panel">
          <div className="panelHead"><div><span>SUMMARY</span><h2>{verdictReady?'Current condition':'Verification required'}</h2></div></div>
          <div className="scoreBlock"><strong>{score==null?'--':Math.round(score)}</strong><span>/100 freshness</span></div>
          <div className="resultLabel">{verdictReady?(fusion.label||'collecting').replaceAll('-', ' '):physicalTitle(validation.status)}</div>
          <div className="summaryRows"><div><span>Visual identity</span><b>{detectedFruit||'--'}</b></div><div><span>Identity confidence</span><b>{fmt(identity.confidence,0)}%</b></div><div><span>Physical check</span><b>{validation.physical_likely?'passed':'not passed'}</b></div><div><span>Fusion confidence</span><b>{verdictReady?`${fmt(fusion.confidence,0)}%`:'--'}</b></div><div><span>Sensor score</span><b>{fmt(fusion.sensor_score,0)}</b></div><div><span>Vision score</span><b>{fmt(fusion.vision_score,0)}</b></div><div><span>Risk</span><b>{verdictReady?(fusion.risk||'--'):'unverified'}</b></div></div>
          <p className="quietNote">A fruit photo may still be visually classified and compared with datasets, but it cannot unlock the FreshFusion freshness verdict. Final output requires multi-view physical evidence plus ESP32 telemetry.</p>
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

        <div className="pairPanel panel"><div className="panelHead"><div><span>PHONE CONNECTION</span><h2>Trusted camera link</h2></div><Smartphone size={20}/></div><div className="pairBody"><div><ol><li>Scan this code from the phone.</li><li>Open the trusted HTTPS link.</li><li>Allow camera once.</li><li>Use a real fruit and capture 3+ changed views; a flat screen/photo cannot unlock the final verdict.</li></ol><small>{phoneUrl}</small></div><div className="qrBox"><QRCodeSVG value={phoneUrl} size={132} bgColor="#ffffff" fgColor="#17221d"/></div></div></div>
      </section>

      <section className="panel datasetPanel"><div className="panelHead"><div><span>LIVE DATASET REFERENCES</span><h2>{effectiveFruit?`${effectiveFruit} comparison sources`:'Reference sources waiting for fruit identity'}</h2></div><Database size={20}/></div><div className="datasetGrid">
        {(datasetInfo?.datasets||[]).map(ds=><div className="datasetSource" key={ds.id}><div className="datasetSourceHead"><span className={ds.online?'statusDot ok':'statusDot'}></span><div><b>{ds.name}</b><small>{ds.purpose.replaceAll('_',' ')}</small></div></div><p>{ds.note}</p><div className="datasetFacts"><span>{ds.online?'Online now':'Offline/unreachable'}</span><span>{ds.updated_at?`Updated ${new Date(ds.updated_at).toLocaleDateString()}`:'Update unknown'}</span><span>{ds.license}</span></div></div>)}
        <div className="datasetSource referenceSource"><div className="datasetSourceHead"><span className={datasetInfo?.reference_index?.ready?'statusDot ok':'statusDot'}></span><div><b>Runtime reference index</b><small>{datasetInfo?.reference_index?.ready?'ready for live similarity':'not built yet'}</small></div></div>{reference.status==='ready'?<><div className="referenceResult"><strong>{reference.match}</strong><span>{fmt(reference.similarity,0)}% similarity</span></div><p>Nearest published visual reference class. This remains a visual comparison and does not bypass physical-fruit verification.</p></>:<p>{datasetInfo?.reference_index?.ready?'Waiting for a usable fruit-like frame.':'Run python ai/sync_public_reference.py once. It downloads the public labelled freshness dataset and builds a compact local comparison index.'}</p>}<div className="datasetFacts"><span>{datasetInfo?.reference_index?.samples||0} indexed images</span><span>{datasetInfo?.reference_index?.classes||0} classes</span><span>screen suspicion {fmt(presentation.screen_suspicion_pct,0)}%</span></div></div>
      </div><p className="datasetPolicy">{datasetInfo?.runtime_policy}</p></section>

      <section className="panel evidencePanel"><div className="panelHead"><div><span>IMAGE ANALYSIS</span><h2>{validation.physical_likely?'Evidence from the verified physical fruit':fruitPresent?'Provisional visual evidence':'Frame quality check'}</h2></div><FlaskConical size={20}/></div><div className="evidenceGrid"><EvidenceCard label="Original" image={latestImage?.url}/><EvidenceCard label="Defect overlay" image={analysis.artifacts?.defect_overlay}/><EvidenceCard label="Texture map" image={analysis.artifacts?.texture}/><EvidenceCard label="Fruit mask" image={analysis.artifacts?.mask}/><EvidenceCard label="Edge map" image={analysis.artifacts?.edges}/></div></section>

      <section className="analysisGrid">
        <div className="panel"><div className="panelHead"><div><span>OBSERVATIONS</span><h2>What needs attention</h2></div></div><div className="issueList">{!fruitPresent?<div className="noIssues">No fruit-quality observations until a centered fruit-like region is detected.</div>:issues.length?issues.map((issue,i)=><div className={`issue ${issue.severity}`} key={`${issue.label}-${i}`}><div><b>{issue.label}</b><span>{issue.note}</span></div><strong>{fmt(issue.value)}{issue.label.toLowerCase().includes('rough')?'':'%'}</strong></div>):<div className="noIssues">No strong visual warning has been detected in the latest usable frame.</div>}</div>{fruitPresent&&!validation.physical_likely&&<p className="provisionalNote">These are pixel-level observations only. They are not used as a final physical-fruit freshness verdict yet.</p>}</div>

        <div className="panel"><div className="panelHead"><div><span>COLOR</span><h2>{effectiveFruit||'Fruit'} surface profile</h2></div></div><div className="barList">{colorRows.map(([name,value])=><div key={name}><div><span>{name}</span><b>{fruitPresent?fmt(value):'--'}%</b></div><progress max="100" value={fruitPresent?(value||0):0}></progress></div>)}</div></div>

        <div className="panel"><div className="panelHead"><div><span>TEXTURE</span><h2>Surface structure</h2></div></div><div className="dataRows"><div><span>Entropy</span><b>{fruitPresent?fmt(texture.entropy,2):'--'}</b></div><div><span>Roughness</span><b>{fruitPresent?fmt(texture.roughness_index):'--'}</b></div><div><span>Edge density</span><b>{fruitPresent?`${fmt(texture.edge_density_pct)}%`:'--'}</b></div><div><span>Laplacian variance</span><b>{fruitPresent?fmt(texture.laplacian_variance,0):'--'}</b></div><div><span>Healthy surface estimate</span><b>{fruitPresent?`${fmt(defects.healthy_surface_estimate_pct,0)}%`:'--'}</b></div></div></div>
      </section>

      <details className="detailPanel panel"><summary>External context and experimental details</summary><div className="detailContent"><div><h3>Outside environment</h3><p>Temperature: <b>{fmt(external?.weather?.temperature_c)}°C</b> · Humidity: <b>{fmt(external?.weather?.humidity_pct)}%</b></p><p>Reference storage: <b>{external?.baseline?.storage_temp_c||'--'}°C</b> · RH: <b>{external?.baseline?.relative_humidity_pct||'--'}%</b></p><button className="secondary" onClick={getWeather}><CloudSun size={15}/> Use current location</button></div><div><h3>Recent samples</h3><div className="recentSamples">{recent.slice(0,8).map(s=><button key={s.sample_id} onClick={()=>{setSample(s);setFruitType(s.fruit_type||'Auto');refresh(s.sample_id)}}>{s.fruit_type}<small>{s.sample_id}</small></button>)}</div></div></div></details>
    </main>
  </div>;
}