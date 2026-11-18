import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Icosahedron, MeshDistortMaterial } from '@react-three/drei';

const Orb = ({ state }) => {
  const meshRef = useRef();
  
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    if (meshRef.current) {
      meshRef.current.rotation.y = time * 0.2;
      meshRef.current.rotation.z = time * 0.1;
    }
  });

  // Keep colors rich but keep distortion stable so it doesn't balloon in size
  let hexColor = "#00ffff"; // idle (blue/cyan)
  let speed = 1.0;
  let distort = 0.05; // very minimal distortion to keep it totally stable
  
  if (state === 'listening') {
    hexColor = "#00ff00"; // green
    speed = 2.0;
    distort = 0.1;
  } else if (state === 'processing') {
    hexColor = "#ffaa00"; // amber
    speed = 3.0;
    distort = 0.15;
  } else if (state === 'speaking') {
    hexColor = "#0088ff"; // Deep blue
    speed = 1.5;
    distort = 0.08;
  }

  return (
    // Instead of a Sphere which creates weird "M dots" and star glitches at the top/bottom poles, 
    // an Icosahedron creates a perfectly even, beautiful sci-fi geodesic mesh!
    <Icosahedron ref={meshRef} args={[1, 15]} scale={1.8}>
      <MeshDistortMaterial 
        color={hexColor}
        emissive={hexColor}
        emissiveIntensity={1.0}
        wireframe={true}
        transparent={true}
        opacity={0.6}
        distort={distort}
        speed={speed}
      />
    </Icosahedron>
  );
};

const OrbScene = ({ orbState }) => {
  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}>
      <Canvas camera={{ position: [0, 0, 7], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={2} color="#ffffff" />
        <pointLight position={[-5, -5, -5]} intensity={3} color={orbState === 'idle' ? '#00ffff' : '#ffffff'} />
        <Orb state={orbState} />
      </Canvas>
    </div>
  );
};

export default OrbScene;
