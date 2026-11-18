import React, { useRef, useMemo, Suspense, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

const MODEL_SCALE = 0.34;
const MODEL_BASE_Y = 0.72;
const WAVEFORM_PROFILE = [
  0.14, 0.24, 0.18, 0.42, 0.86, 0.96, 0.34, 0.18, 0.62, 0.16,
  0.12, 0.22, 0.3, 0.22, 0.16, 0.68, 0.18, 0.14, 0.88, 0.18,
  0.12, 0.26, 0.18, 0.24, 0.56, 0.72, 0.48, 0.2, 0.14
];

// Fallback component if the GLB fails to load
const FallbackOrb = ({ orbState }) => {
  const meshRef = useRef();
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (meshRef.current) {
      meshRef.current.position.y = Math.sin(t * 1.5) * 0.1;
      if (orbState === 'speaking') {
        const scale = 1 + Math.sin(t * 15) * 0.05;
        meshRef.current.scale.set(scale, scale, scale);
      } else {
        meshRef.current.scale.set(1, 1, 1);
      }
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.8, 32, 32]} />
      <meshStandardMaterial 
        color="#00ffff" 
        emissive="#00ffff" 
        emissiveIntensity={2} 
        wireframe={true}
        transparent={true}
        opacity={0.3}
      />
    </mesh>
  );
};

function AvatarModel({ orbState, waveformLevel, waveformActive, waveformStamp }) {
  const masterGroupRef = useRef();
  const { scene } = useGLTF('/male.glb', true);
  const clonedScene = useMemo(() => scene.clone(), [scene]);

  const customMaterial = useMemo(() => new THREE.MeshPhysicalMaterial({
    color: new THREE.Color('#3caeac'),
    roughness: 0.5,
    metalness: 0.2,
    clearcoat: 0.1,
  }), []);

  useEffect(() => {
    clonedScene.traverse((child) => {
      if (child.isMesh || child.isSkinnedMesh) {
        child.material = customMaterial;
      }
    });
  }, [clonedScene, customMaterial]);

  const leftEyelidRef = useRef();
  const rightEyelidRef = useRef();
  const mouthBarsRef = useRef([]);
  const waveformBarsRef = useRef([]);
  const waveformLineRef = useRef();
  const waveformOffsets = useMemo(
    () => WAVEFORM_PROFILE.map((_, i) => (i - (WAVEFORM_PROFILE.length - 1) / 2) * 0.052),
    []
  );

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (masterGroupRef.current) {
      masterGroupRef.current.position.y = MODEL_BASE_Y + Math.sin(t * 1.2) * 0.08;
      
      // State-based animation (Head Nod)
      if (orbState === 'speaking') {
        masterGroupRef.current.rotation.x = THREE.MathUtils.lerp(masterGroupRef.current.rotation.x, 0.05 + Math.sin(t * 12) * 0.012, 0.1);
        mouthBarsRef.current.forEach((bar, i) => {
          if (bar) bar.scale.y = THREE.MathUtils.lerp(bar.scale.y, 1 + Math.max(0, Math.sin(t * (10 + i * 2)) * 6), 0.2);
        });
      } else {
        masterGroupRef.current.rotation.x = THREE.MathUtils.lerp(masterGroupRef.current.rotation.x, 0.05 + Math.sin(t * 1.2) * 0.02, 0.05);
        mouthBarsRef.current.forEach((bar) => {
          if (bar) bar.scale.y = THREE.MathUtils.lerp(bar.scale.y, 0.1, 0.1);
        });
      }

      waveformBarsRef.current.forEach((bar, i) => {
        if (!bar) return;
        const profile = WAVEFORM_PROFILE[i];
        const liveFresh = waveformStamp > 0 && Date.now() - waveformStamp < 220;
        const fallbackLevel = orbState === 'speaking'
          ? 0.35 + Math.abs(Math.sin(t * 9 + i * 0.48)) * 0.65
          : 0;
        const level = liveFresh ? waveformLevel : fallbackLevel;
        const active = liveFresh ? waveformActive : orbState === 'speaking';
        const targetScale = active
          ? 0.3 + profile * (0.8 + level * 5.8)
          : 0.16 + profile * 0.28;
        bar.scale.y = THREE.MathUtils.lerp(bar.scale.y, targetScale, active ? 0.4 : 0.14);
        if (bar.material) {
          bar.material.emissiveIntensity = THREE.MathUtils.lerp(
            bar.material.emissiveIntensity,
            active ? 1.5 + level * 3.6 : 0.9,
            active ? 0.34 : 0.12
          );
          bar.material.opacity = THREE.MathUtils.lerp(
            bar.material.opacity,
            active ? 0.55 + level * 0.35 : 0.36,
            active ? 0.34 : 0.12
          );
        }
      });

      if (waveformLineRef.current?.material) {
        const liveFresh = waveformStamp > 0 && Date.now() - waveformStamp < 220;
        const lineLevel = liveFresh ? waveformLevel : (orbState === 'speaking' ? 0.55 : 0);
        const lineActive = liveFresh ? waveformActive : orbState === 'speaking';
        waveformLineRef.current.material.opacity = THREE.MathUtils.lerp(
          waveformLineRef.current.material.opacity,
          lineActive ? 0.34 + lineLevel * 0.28 : 0.2,
          0.16
        );
      }

      // Eyelids logic
      const isOff = orbState === 'off' || orbState === 'offline';
      const eyelidScale = isOff ? 1 : 0.001;
      if (leftEyelidRef.current) leftEyelidRef.current.scale.setScalar(THREE.MathUtils.lerp(leftEyelidRef.current.scale.x, eyelidScale, 0.1));
      if (rightEyelidRef.current) rightEyelidRef.current.scale.setScalar(THREE.MathUtils.lerp(rightEyelidRef.current.scale.x, eyelidScale, 0.1));
    }
  });

  return (
    <group ref={masterGroupRef} scale={[MODEL_SCALE, MODEL_SCALE, MODEL_SCALE]} position={[0, MODEL_BASE_Y, 0]}>
      {/* 
          All components are now children of the master group. 
          Positions are relative to the model's pivot.
      */}
      <primitive object={clonedScene} position={[0, -3.2, 0]} />
      
      {/* Hair (Procedural) - Larger and better integrated */}
      <mesh position={[0, 0.6, -0.4]} scale={[0.7, 0.55, 0.7]}>
        <sphereGeometry args={[1, 32, 16]} />
        <meshStandardMaterial color="#050505" roughness={0.9} />
      </mesh>
      
      {/* Simulated Eyelids - Fine-tuned position */}
      <mesh ref={leftEyelidRef} position={[-0.18, 0.16, 0.36]}>
        <sphereGeometry args={[0.07, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshPhysicalMaterial color="#3caeac" />
      </mesh>
      <mesh ref={rightEyelidRef} position={[0.18, 0.16, 0.36]}>
        <sphereGeometry args={[0.07, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshPhysicalMaterial color="#3caeac" />
      </mesh>

      {/* Mouth Visualizer - Lowered for better chin alignment */}
      <group position={[0, -0.44, 0.42]}>
        {[-0.1, -0.05, 0, 0.05, 0.1].map((x, i) => (
          <mesh key={i} position={[x, 0, 0]} ref={el => (mouthBarsRef.current[i] = el)}>
            <boxGeometry args={[0.02, 0.04, 0.015]} />
            <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={2} transparent={true} opacity={0.8} />
          </mesh>
        ))}
      </group>

      <group position={[0, 1.14, 0.18]}>
        <mesh ref={waveformLineRef} position={[0, 0, -0.01]}>
          <boxGeometry args={[1.72, 0.014, 0.012]} />
          <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={0.9} transparent={true} opacity={0.24} />
        </mesh>
        {waveformOffsets.map((x, i) => (
          <mesh key={i} position={[x, 0, 0]} ref={el => (waveformBarsRef.current[i] = el)}>
            <boxGeometry args={[0.022, 0.32, 0.014]} />
            <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={1.2} transparent={true} opacity={0.5} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

const SceneContent = ({ orbState, waveformLevel, waveformActive, waveformStamp }) => {
  return (
    <Suspense fallback={<FallbackOrb orbState={orbState} />}>
      <AvatarModel orbState={orbState} waveformLevel={waveformLevel} waveformActive={waveformActive} waveformStamp={waveformStamp} />
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 10, 5]} intensity={2} color="#00ffff" />
      <pointLight position={[-5, -5, 5]} intensity={0.5} color="#ffffff" />
    </Suspense>
  );
};

export default function AvatarScene({ orbState, waveformLevel = 0, waveformActive = false, waveformStamp = 0 }) {
  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#050505' }}>
      <Canvas 
        camera={{ position: [0, 0.2, 4.7], fov: 40 }}
        style={{ width: '100%', height: '100%' }}
        onCreated={({ gl }) => {
          gl.setClearColor(new THREE.Color('#050505'));
        }}
      >
        <SceneContent orbState={orbState} waveformLevel={waveformLevel} waveformActive={waveformActive} waveformStamp={waveformStamp} />
        <OrbitControls enableZoom={false} maxPolarAngle={Math.PI / 2} minPolarAngle={Math.PI / 2 - 0.5} />
      </Canvas>
      <div style={{ position: 'absolute', bottom: '10px', width: '100%', textAlign: 'center', pointerEvents: 'none' }}>
        <p style={{ color: 'rgba(0, 255, 255, 0.3)', fontSize: '10px', letterSpacing: '4px', fontFamily: 'monospace' }}>
          {orbState === 'offline' || orbState === 'off' ? 'NEURAL LINK STANDBY' : 'AVATAR SYNCED // ALPHA ONLINE'}
        </p>
      </div>
    </div>
  );
}
