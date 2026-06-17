import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, Grid, Bounds } from '@react-three/drei';
import { useState } from 'react';
import { CADModel } from './CADModel';
import { usePLCStore } from './store';

// Dedicated page for CAD model viewing
export default function CADViewer() {
    const plcData = usePLCStore();
    const [modelInfo, setModelInfo] = useState<any>(null);

    return (
        <div className="relative w-full h-full bg-[#020408]">
            {/* 3D Canvas */}
            <Canvas shadows>
                <PerspectiveCamera makeDefault position={[3, 3, 3]} fov={75} />
                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={1}
                    maxDistance={50}
                    target={[0, 0, 0]}
                />

                {/* Lighting - Very bright for CAD model */}
                <ambientLight intensity={2.0} />
                <hemisphereLight args={['#ffffff', '#444444', 1.5]} />
                <directionalLight
                    position={[10, 20, 10]}
                    intensity={3}
                    castShadow
                    shadow-mapSize-width={4096}
                    shadow-mapSize-height={4096}
                />
                <directionalLight position={[-10, 15, -10]} intensity={2} />
                <pointLight position={[0, 10, 0]} intensity={2} />

                {/* Environment for realistic reflections */}
                <Environment preset="warehouse" />

                {/* Scene */}
                <Grid
                    args={[30, 30]}
                    cellColor="#00d4ff"
                    sectionColor="#00f2ff"
                    fadeDistance={50}
                />

                {/* Your CAD Model - Auto-centered and fitted! */}
                <Bounds fit clip observe margin={1.2}>
                    <CADModel
                        position={[0, 0, 0]}
                        scale={1.0}
                        onClick={() => setModelInfo({ name: 'Engineering Design', file: 'FINAL DRW 26 MARCH VIG 2023.glb' })}
                    />
                </Bounds>

                {/* Title */}
                <mesh position={[0, 12, 0]}>
                    <meshBasicMaterial color="#00f2ff" />
                </mesh>
            </Canvas>

            {/* Page Header */}
            <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-[#020408] to-transparent p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-black text-cyan-400 tracking-wider mb-1">
                            CAD MODEL VIEWER
                        </h1>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                            Engineering Design Visualization
                        </p>
                    </div>
                    <div className="flex items-center gap-2 bg-[#0a0d14]/90 backdrop-blur-xl border border-white/10 rounded-lg px-4 py-2">
                        <div className={`w-2 h-2 rounded-full ${plcData.isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            {plcData.isConnected ? 'SYSTEM ONLINE' : 'OFFLINE MODE'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Model Info Panel */}
            {modelInfo && (
                <div className="absolute top-24 right-4 w-80 bg-[#0a0d14]/95 backdrop-blur-xl border border-cyan-500/30 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-black text-cyan-400 tracking-wider">
                            📐 MODEL INFO
                        </h3>
                        <button
                            onClick={() => setModelInfo(null)}
                            className="text-slate-500 hover:text-white"
                        >
                            ✕
                        </button>
                    </div>

                    <div className="space-y-3">
                        <div className="p-3 bg-black/40 rounded-lg">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">File Name</span>
                            <span className="text-sm font-black text-white">{modelInfo.file}</span>
                        </div>
                        <div className="p-3 bg-black/40 rounded-lg">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Format</span>
                            <span className="text-sm font-black text-cyan-400">glTF Binary (.glb)</span>
                        </div>
                        <div className="p-3 bg-black/40 rounded-lg">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Size</span>
                            <span className="text-sm font-black text-cyan-400">33.6 MB</span>
                        </div>
                        <div className="p-3 bg-black/40 rounded-lg">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Status</span>
                            <span className="text-sm font-black text-green-400">✓ LOADED</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Controls Info */}
            <div className="absolute bottom-4 left-4 bg-[#0a0d14]/90 backdrop-blur-xl border border-white/10 rounded-lg px-4 py-3">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider space-y-1">
                    <p>🖱️ Left Click + Drag: Rotate View</p>
                    <p>🖱️ Right Click + Drag: Pan</p>
                    <p>🔄 Scroll: Zoom In/Out</p>
                    <p>👆 Click Model: View Details</p>
                </div>
            </div>

            {/* View Controls */}
            <div className="absolute bottom-4 right-4 flex gap-2">
                <button
                    className="px-4 py-2 bg-[#0a0d14]/90 backdrop-blur-xl border border-cyan-500/30 rounded-lg text-xs font-black text-cyan-400 hover:bg-cyan-500/10 transition"
                    onClick={() => {/* Reset camera view */ }}
                >
                    🔄 RESET VIEW
                </button>
                <button
                    className="px-4 py-2 bg-[#0a0d14]/90 backdrop-blur-xl border border-cyan-500/30 rounded-lg text-xs font-black text-cyan-400 hover:bg-cyan-500/10 transition"
                    onClick={() => setModelInfo({ name: 'Engineering Design', file: 'FINAL DRW 26 MARCH VIG 2023.glb' })}
                >
                    ℹ️ MODEL INFO
                </button>
            </div>
        </div>
    );
}
