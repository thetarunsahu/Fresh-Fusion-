import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, Float, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { useMemo, useRef } from 'react';

function Banana({score=70}) {
  const ref = useRef();
  const curve = useMemo(() => new THREE.CatmullRomCurve3([
    new THREE.Vector3(-1.8,-.4,0), new THREE.Vector3(-1.1,.2,.12), new THREE.Vector3(-.2,.62,0), new THREE.Vector3(.8,.52,-.08), new THREE.Vector3(1.65,.05,0)
  ]), []);
  const geometry = useMemo(() => new THREE.TubeGeometry(curve, 90, .42, 16, false), [curve]);
  const color = score > 80 ? '#d7ff63' : score > 60 ? '#f5d84a' : score > 38 ? '#d49a35' : '#72512d';
  useFrame((_,d)=>{ if(ref.current) ref.current.rotation.y += d*.12; });
  return <group ref={ref} rotation={[0.2,0,-0.2]}>
    <mesh geometry={geometry} castShadow receiveShadow><meshStandardMaterial color={color} roughness={.5} metalness={.02}/></mesh>
    <mesh position={[-1.93,-.48,0]} rotation={[0,0,-.8]}><cylinderGeometry args={[.16,.24,.55,14]}/><meshStandardMaterial color="#5f4a22" roughness={.9}/></mesh>
    <mesh position={[1.78,.12,0]} rotation={[0,0,-.6]}><cylinderGeometry args={[.11,.15,.4,14]}/><meshStandardMaterial color="#4c3b1e" roughness={.9}/></mesh>
    {score < 70 && <><mesh position={[.45,.82,.37]}><sphereGeometry args={[.16,16,16]}/><meshStandardMaterial color="#5b2d19" roughness={1}/></mesh><mesh position={[-.7,.55,.34]}><sphereGeometry args={[.11,16,16]}/><meshStandardMaterial color="#7a3b20"/></mesh></>}
  </group>;
}

function Apple({score=70}) {
  const c = score > 65 ? '#65d45f' : '#d85a3b';
  return <group><mesh scale={[1,1.05,1]}><sphereGeometry args={[1.25,64,64]}/><meshStandardMaterial color={c} roughness={.48}/></mesh><mesh position={[0,1.35,0]} rotation={[0,0,.15]}><cylinderGeometry args={[.08,.11,.52,12]}/><meshStandardMaterial color="#54381f"/></mesh></group>
}

function Orange({score=70}) { return <mesh><sphereGeometry args={[1.25,64,64]}/><meshStandardMaterial color={score > 45 ? '#ff9738':'#a65b2c'} roughness={.72}/></mesh>; }
function Mango({score=70}) { return <group rotation={[0,0,-.25]}><mesh scale={[1.05,1.42,.9]}><sphereGeometry args={[1.05,64,64]}/><meshStandardMaterial color={score>65?'#efb83f':'#b96932'} roughness={.58}/></mesh><mesh position={[0,1.55,0]}><cylinderGeometry args={[.07,.10,.32,12]}/><meshStandardMaterial color="#4b341f"/></mesh></group>; }

function Scene({fruit, score}) {
  const key=(fruit||'banana').toLowerCase();
  return <>
    <ambientLight intensity={.55}/><directionalLight position={[4,6,3]} intensity={2.1} castShadow/>
    <pointLight position={[-4,-1,4]} intensity={10} color="#4dff9a"/>
    <Float speed={1.5} rotationIntensity={.15} floatIntensity={.25}>
      {key.includes('apple') ? <Apple score={score}/> : key.includes('orange') ? <Orange score={score}/> : key.includes('mango') ? <Mango score={score}/> : <Banana score={score}/>} 
    </Float>
    <OrbitControls enablePan={false} minDistance={3.5} maxDistance={7} autoRotate autoRotateSpeed={.6}/>
    <Environment preset="studio"/>
  </>;
}

export default function FruitTwin({fruit, score}) { return <Canvas camera={{position:[0,0,5.3], fov:42}} shadows dpr={[1,2]}><Scene fruit={fruit} score={score}/></Canvas>; }
