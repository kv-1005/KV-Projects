import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text, Box, Cylinder, Sphere } from '@react-three/drei';
import { usePLCStore } from './store';
import { useState, useRef } from 'react';

// Equipment Models

// Realistic Motor Component with detailed geometry and animation
function Motor({ position, status, speed, name, onClick }: any) {
    const isRunning = status === 1;
    const statusColor = isRunning ? '#00ff85' : '#ff3c3c';

    // Refs for animated parts
    const shaftRef = useRef<any>();
    const fanRef = useRef<any>();

    // Continuous rotation animation (like Panda3D's taskMgr)
    useFrame((_, delta) => {
        if (isRunning) {
            // Rotate shaft continuously when running
            if (shaftRef.current) {
                shaftRef.current.rotation.z += delta * 10; // 10 rad/sec
            }
            // Rotate cooling fan
            if (fanRef.current) {
                fanRef.current.rotation.z += delta * 15; // 15 rad/sec (faster)
            }
        }
    });

    return (
        <group position={position} onClick={onClick}>
            {/* Motor main housing - larger and more detailed */}
            <group>
                {/* Main cylindrical body */}
                <Cylinder args={[0.6, 0.65, 1.2, 32]} rotation={[Math.PI / 2, 0, 0]}>
                    <meshStandardMaterial
                        color="#2c3e50"
                        metalness={0.9}
                        roughness={0.3}
                    />
                </Cylinder>

                {/* Cooling fins (realistic detail) */}
                {[...Array(8)].map((_, i) => (
                    <Box
                        key={i}
                        args={[0.05, 1.3, 0.02]}
                        position={[
                            Math.cos((i / 8) * Math.PI * 2) * 0.62,
                            0,
                            Math.sin((i / 8) * Math.PI * 2) * 0.62
                        ]}
                        rotation={[0, (i / 8) * Math.PI * 2, Math.PI / 2]}
                    >
                        <meshStandardMaterial color="#34495e" metalness={0.8} roughness={0.4} />
                    </Box>
                ))}

                {/* Front end bell */}
                <Cylinder args={[0.5, 0.6, 0.15, 32]} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0.65]}>
                    <meshStandardMaterial color="#34495e" metalness={0.85} roughness={0.25} />
                </Cylinder>

                {/* Rear end bell */}
                <Cylinder args={[0.5, 0.65, 0.15, 32]} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, -0.65]}>
                    <meshStandardMaterial color="#34495e" metalness={0.85} roughness={0.25} />
                </Cylinder>
            </group>

            {/* Terminal/Junction box on top */}
            <Box args={[0.3, 0.25, 0.2]} position={[0, 0.75, 0.3]}>
                <meshStandardMaterial color="#1a1a1a" metalness={0.6} roughness={0.5} />
            </Box>

            {/* Terminal box cover screws */}
            <Cylinder args={[0.02, 0.02, 0.03, 8]} position={[0.12, 0.85, 0.3]}>
                <meshStandardMaterial color="#888" metalness={0.9} roughness={0.1} />
            </Cylinder>
            <Cylinder args={[0.02, 0.02, 0.03, 8]} position={[-0.12, 0.85, 0.3]}>
                <meshStandardMaterial color="#888" metalness={0.9} roughness={0.1} />
            </Cylinder>

            {/* Mounting feet (realistic base) */}
            <Box args={[1.2, 0.08, 0.3]} position={[0, -0.7, 0]}>
                <meshStandardMaterial color="#555" metalness={0.7} roughness={0.6} />
            </Box>

            {/* Mounting bolt holes */}
            {[[-0.5, -0.74, 0.1], [0.5, -0.74, 0.1], [-0.5, -0.74, -0.1], [0.5, -0.74, -0.1]].map((pos, i) => (
                <Cylinder key={i} args={[0.04, 0.04, 0.08, 8]} position={pos as any}>
                    <meshStandardMaterial color="#222" metalness={0.9} roughness={0.2} />
                </Cylinder>
            ))}

            {/* Extended shaft (drive end) - ANIMATED */}
            <group ref={shaftRef} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 1.55]}>
                <Cylinder args={[0.12, 0.12, 1.8, 16]}>
                    <meshStandardMaterial color="#c0c0c0" metalness={0.95} roughness={0.05} />
                </Cylinder>

                {/* Shaft keyway (realistic detail) */}
                <Box args={[0.04, 1.5, 0.02]} position={[0.12, 0, 0]}>
                    <meshStandardMaterial color="#888" metalness={0.9} roughness={0.1} />
                </Box>
            </group>

            {/* Cooling fan (visible on rear) - ANIMATED */}
            <group ref={fanRef} position={[0, 0, -0.75]} rotation={[Math.PI / 2, 0, 0]}>
                {/* Fan hub */}
                <Cylinder args={[0.15, 0.15, 0.05, 16]}>
                    <meshStandardMaterial color="#666" metalness={0.7} roughness={0.3} />
                </Cylinder>

                {/* Fan blades - 6 blades */}
                {[...Array(6)].map((_, i) => (
                    <Box
                        key={i}
                        args={[0.08, 0.4, 0.02]}
                        position={[
                            Math.cos((i / 6) * Math.PI * 2) * 0.25,
                            Math.sin((i / 6) * Math.PI * 2) * 0.25,
                            0
                        ]}
                        rotation={[0, 0, (i / 6) * Math.PI * 2 + Math.PI / 2]}
                    >
                        <meshStandardMaterial color="#444" metalness={0.6} roughness={0.4} />
                    </Box>
                ))}
            </group>

            {/* Status indicator LED (more realistic position) */}
            <Sphere args={[0.08, 16, 16]} position={[0.15, 0.82, 0.3]}>
                <meshStandardMaterial
                    color={statusColor}
                    emissive={statusColor}
                    emissiveIntensity={isRunning ? 3 : 0.3}
                />
            </Sphere>

            {/* Nameplate (realistic industrial label) */}
            <Box args={[0.4, 0.15, 0.01]} position={[0, 0.3, 0.61]} rotation={[Math.PI / 2, 0, 0]}>
                <meshStandardMaterial color="#f0f0f0" metalness={0.1} roughness={0.8} />
            </Box>

            {/* Equipment label */}
            <Text
                position={[0, -1.0, 0]}
                fontSize={0.18}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                {name}
            </Text>

            {/* Status text */}
            <Text
                position={[0, -1.25, 0]}
                fontSize={0.14}
                color={statusColor}
                anchorX="center"
                anchorY="middle"
            >
                {isRunning ? `⚡ ${speed} RPM` : '● STOPPED'}
            </Text>
        </group>
    );
}

// Pump Component
function Pump({ position, status, flowRate, name, onClick }: any) {
    const isRunning = status === 1;
    const color = isRunning ? '#00f2ff' : '#64748b';

    return (
        <group position={position} onClick={onClick}>
            {/* Pump casing */}
            <Sphere args={[0.6, 32, 32]}>
                <meshStandardMaterial color={color} metalness={0.7} roughness={0.3} />
            </Sphere>

            {/* Inlet pipe */}
            <Cylinder args={[0.15, 0.15, 1, 12]} rotation={[0, 0, Math.PI / 2]} position={[-0.8, 0, 0]}>
                <meshStandardMaterial color="#4a5568" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Outlet pipe */}
            <Cylinder args={[0.15, 0.15, 1, 12]} rotation={[0, 0, Math.PI / 2]} position={[0.8, 0, 0]}>
                <meshStandardMaterial color="#4a5568" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Status light */}
            <Sphere args={[0.12, 16, 16]} position={[0, 0.7, 0]}>
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isRunning ? 2 : 0.2}
                />
            </Sphere>

            {/* Label */}
            <Text
                position={[0, -0.9, 0]}
                fontSize={0.2}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                {name}
            </Text>

            {/* Flow rate */}
            {isRunning && flowRate && (
                <Text
                    position={[0, -1.2, 0]}
                    fontSize={0.15}
                    color="#00f2ff"
                    anchorX="center"
                    anchorY="middle"
                >
                    {flowRate} L/min
                </Text>
            )}
        </group>
    );
}

// Valve Component
function Valve({ position, status, name, onClick }: any) {
    const isOpen = status === 1;
    const color = isOpen ? '#00ff85' : '#ff3c3c';
    const rotation = isOpen ? Math.PI / 2 : 0;

    return (
        <group position={position} onClick={onClick}>
            {/* Valve body */}
            <Box args={[0.4, 0.4, 0.4]}>
                <meshStandardMaterial color="#718096" metalness={0.8} roughness={0.2} />
            </Box>

            {/* Valve plate/disk - rotates based on open/close */}
            <Box args={[0.35, 0.05, 0.35]} rotation={[0, rotation, 0]}>
                <meshStandardMaterial color={color} metalness={0.7} roughness={0.3} />
            </Box>

            {/* Actuator */}
            <Cylinder args={[0.15, 0.15, 0.5, 16]} position={[0, 0.45, 0]}>
                <meshStandardMaterial color="#4a5568" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Status light */}
            <Sphere args={[0.08, 16, 16]} position={[0, 0.35, 0]}>
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={2}
                />
            </Sphere>

            {/* Label */}
            <Text
                position={[0, -0.4, 0]}
                fontSize={0.15}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                {name}
            </Text>

            {/* Status text */}
            <Text
                position={[0, -0.65, 0]}
                fontSize={0.12}
                color={color}
                anchorX="center"
                anchorY="middle"
            >
                {isOpen ? 'OPEN' : 'CLOSED'}
            </Text>
        </group>
    );
}

// Tank Component
function Tank({ position, level, name, onClick }: any) {
    const levelPercent = (level / 100) * 2; // Tank height is 2 units
    const color = level > 80 ? '#ff3c3c' : level > 50 ? '#ffb800' : '#00f2ff';

    return (
        <group position={position} onClick={onClick}>
            {/* Tank body (transparent) */}
            <Cylinder args={[0.8, 0.8, 2, 32]} position={[0, 1, 0]}>
                <meshStandardMaterial
                    color="#ffffff"
                    transparent
                    opacity={0.2}
                    metalness={0.1}
                    roughness={0.1}
                />
            </Cylinder>

            {/* Liquid level */}
            <Cylinder args={[0.75, 0.75, levelPercent, 32]} position={[0, levelPercent / 2, 0]}>
                <meshStandardMaterial
                    color={color}
                    transparent
                    opacity={0.7}
                    emissive={color}
                    emissiveIntensity={0.3}
                />
            </Cylinder>

            {/* Tank base */}
            <Cylinder args={[0.82, 0.82, 0.1, 32]} position={[0, 0.05, 0]}>
                <meshStandardMaterial color="#4a5568" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Tank top */}
            <Cylinder args={[0.82, 0.82, 0.1, 32]} position={[0, 2.05, 0]}>
                <meshStandardMaterial color="#4a5568" metalness={0.8} roughness={0.2} />
            </Cylinder>

            {/* Label */}
            <Text
                position={[0, -0.3, 0]}
                fontSize={0.2}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                {name}
            </Text>

            {/* Level percentage */}
            <Text
                position={[0, -0.6, 0]}
                fontSize={0.18}
                color={color}
                anchorX="center"
                anchorY="middle"
            >
                {level.toFixed(1)}%
            </Text>
        </group>
    );
}

// Floor/Platform
function Floor() {
    return (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
            <planeGeometry args={[20, 20]} />
            <meshStandardMaterial
                color="#1a2332"
                metalness={0.3}
                roughness={0.8}
            />
        </mesh>
    );
}

// Grid Helper
function GridHelper() {
    return (
        <gridHelper args={[20, 20, '#00d4ff', '#3a4d5f']} position={[0, 0, 0]} />
    );
}

// Main 3D Plant Scene
export default function PlantVisualization3D() {
    const plcData = usePLCStore();
    const [selectedEquipment, setSelectedEquipment] = useState<any>(null);

    // Map PLC data to equipment
    const equipment = {
        motor1: { status: plcData.digitalBits[0], speed: 1450, name: 'Motor 1' },
        motor2: { status: plcData.digitalBits[1], speed: 1200, name: 'Motor 2' },
        pump1: { status: plcData.digitalBits[2], flowRate: 450, name: 'Pump 1' },
        valve1: { status: plcData.digitalBits[3], name: 'Valve 1' },
        valve2: { status: plcData.digitalBits[4], name: 'Valve 2' },
        tank: { level: plcData.analogValue, name: 'Tank 1' }
    };

    return (
        <div className="relative w-full h-full bg-[#020408]">
            {/* 3D Canvas */}
            <Canvas shadows>
                <PerspectiveCamera makeDefault position={[10, 8, 10]} fov={60} />
                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={5}
                    maxDistance={30}
                />

                {/* Lighting - Enhanced for visibility */}
                {/* Very bright ambient light for overall illumination */}
                <ambientLight intensity={1.5} />

                {/* Hemisphere light for natural sky/ground lighting */}
                <hemisphereLight
                    args={['#ffffff', '#444444', 1.2]}
                    position={[0, 10, 0]}
                />

                {/* Main directional light (sun) - very bright */}
                <directionalLight
                    position={[10, 15, 10]}
                    intensity={2.5}
                    castShadow
                    shadow-mapSize-width={2048}
                    shadow-mapSize-height={2048}
                    shadow-camera-left={-15}
                    shadow-camera-right={15}
                    shadow-camera-top={15}
                    shadow-camera-bottom={-15}
                />

                {/* Fill light from opposite side */}
                <directionalLight
                    position={[-10, 10, -5]}
                    intensity={1.5}
                />

                {/* Accent lights for equipment highlighting */}
                <pointLight position={[-5, 3, 0]} intensity={2} color="#00f2ff" />
                <pointLight position={[5, 3, 0]} intensity={2} color="#00ff85" />
                <pointLight position={[0, 5, 5]} intensity={1.5} color="#ffffff" />

                {/* Scene Elements */}
                <Floor />
                <GridHelper />

                {/* Equipment Layout */}
                <Motor
                    position={[-4, 0.5, -3]}
                    status={equipment.motor1.status}
                    speed={equipment.motor1.speed}
                    name={equipment.motor1.name}
                    onClick={() => setSelectedEquipment(equipment.motor1)}
                />

                <Motor
                    position={[-4, 0.5, 3]}
                    status={equipment.motor2.status}
                    speed={equipment.motor2.speed}
                    name={equipment.motor2.name}
                    onClick={() => setSelectedEquipment(equipment.motor2)}
                />

                <Pump
                    position={[0, 0.6, -3]}
                    status={equipment.pump1.status}
                    flowRate={equipment.pump1.flowRate}
                    name={equipment.pump1.name}
                    onClick={() => setSelectedEquipment(equipment.pump1)}
                />

                <Valve
                    position={[0, 0.2, 0]}
                    status={equipment.valve1.status}
                    name={equipment.valve1.name}
                    onClick={() => setSelectedEquipment(equipment.valve1)}
                />

                <Valve
                    position={[0, 0.2, 3]}
                    status={equipment.valve2.status}
                    name={equipment.valve2.name}
                    onClick={() => setSelectedEquipment(equipment.valve2)}
                />

                <Tank
                    position={[4, 0, 0]}
                    level={equipment.tank.level}
                    name={equipment.tank.name}
                    onClick={() => setSelectedEquipment(equipment.tank)}
                />

                {/* Title */}
                <Text
                    position={[0, 4, 0]}
                    fontSize={0.4}
                    color="#00f2ff"
                    anchorX="center"
                    anchorY="middle"
                >
                    PLC PLANT VISUALIZATION
                </Text>
            </Canvas>

            {/* Equipment Detail Panel */}
            {selectedEquipment && (
                <div className="absolute top-4 right-4 w-80 bg-[#0a0d14]/95 backdrop-blur-xl border border-cyan-500/30 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-black text-cyan-400 tracking-wider">
                            {selectedEquipment.name}
                        </h3>
                        <button
                            onClick={() => setSelectedEquipment(null)}
                            className="text-slate-500 hover:text-white"
                        >
                            ✕
                        </button>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-black/40 rounded-lg">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Status</span>
                            <span className={`text-sm font-black ${selectedEquipment.status ? 'text-green-400' : 'text-red-400'}`}>
                                {selectedEquipment.status ? 'RUNNING' : 'STOPPED'}
                            </span>
                        </div>

                        {selectedEquipment.speed && (
                            <div className="flex justify-between items-center p-3 bg-black/40 rounded-lg">
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Speed</span>
                                <span className="text-sm font-black text-cyan-400">{selectedEquipment.speed} RPM</span>
                            </div>
                        )}

                        {selectedEquipment.flowRate && (
                            <div className="flex justify-between items-center p-3 bg-black/40 rounded-lg">
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Flow Rate</span>
                                <span className="text-sm font-black text-cyan-400">{selectedEquipment.flowRate} L/min</span>
                            </div>
                        )}

                        {selectedEquipment.level !== undefined && (
                            <div className="flex justify-between items-center p-3 bg-black/40 rounded-lg">
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Level</span>
                                <span className="text-sm font-black text-cyan-400">{selectedEquipment.level.toFixed(1)}%</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Controls Info */}
            <div className="absolute bottom-4 left-4 bg-[#0a0d14]/90 backdrop-blur-xl border border-white/10 rounded-lg px-4 py-3">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider space-y-1">
                    <p>🖱️ Left Click + Drag: Rotate View</p>
                    <p>🖱️ Right Click + Drag: Pan</p>
                    <p>🔄 Scroll: Zoom In/Out</p>
                    <p>👆 Click Equipment: View Details</p>
                </div>
            </div>

            {/* Connection Status */}
            <div className="absolute top-4 left-4 flex items-center gap-2 bg-[#0a0d14]/90 backdrop-blur-xl border border-white/10 rounded-lg px-4 py-2">
                <div className={`w-2 h-2 rounded-full ${plcData.isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    {plcData.isConnected ? 'PLC CONNECTED' : 'PLC DISCONNECTED'}
                </span>
            </div>
        </div>
    );
}
