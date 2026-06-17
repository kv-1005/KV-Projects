import { useGLTF } from '@react-three/drei';
import { useRef } from 'react';

// Component to load and display your CAD model
export function CADModel({ position = [0, 0, 0], scale = 1, onClick }: any) {
    const modelRef = useRef<any>();

    // Load your actual CAD model
    const { scene } = useGLTF('/FINAL DRW 26 MARCH VIG 2023.glb');

    return (
        <group ref={modelRef} position={position} scale={scale} onClick={onClick}>
            <primitive object={scene.clone()} />
        </group>
    );
}

// Preload the model for better performance
useGLTF.preload('/FINAL DRW 26 MARCH VIG 2023.glb');
