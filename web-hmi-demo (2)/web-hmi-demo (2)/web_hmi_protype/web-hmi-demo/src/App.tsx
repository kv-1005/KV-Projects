import { useState } from 'react';
import {
    Activity,
    Cpu,
    Zap,
    Sliders,
    Terminal,
    Database,
    Binary,
    Network,
    RefreshCw,
    Box,
    FileText
} from 'lucide-react';
import { usePLCStore } from './store';
import { useWebSocket } from './useWebSocket';
import PlantVisualization3D from './PlantVisualization3D';
import CADViewer from './CADViewer';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility for clean class merging
function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// --- SUB-COMPONENTS ---

const Card = ({ title, children, className, icon: Icon }: { title: string; children: React.ReactNode; className?: string; icon?: any }) => (
    <div className={cn("industrial-card p-6 group relative overflow-hidden", className)}>
        <div className="absolute top-0 right-0 p-1 opacity-10 group-hover:opacity-30 transition-opacity">
            {Icon && <Icon className="w-12 h-12 -mr-4 -mt-4 rotate-12" />}
        </div>
        <div className="flex items-center justify-between mb-6 relative z-10">
            <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded flex items-center justify-center bg-cyan-500/10 border border-cyan-500/20">
                    {Icon && <Icon className="w-3.5 h-3.5 text-cyan-400" />}
                </div>
                <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{title}</h3>
            </div>
            <div className="flex gap-1">
                <div className="w-1 h-3 bg-cyan-500/20 rounded-full" />
                <div className="w-1 h-3 bg-cyan-500/10 rounded-full" />
            </div>
        </div>
        <div className="relative z-10">
            {children}
        </div>
    </div>
);

const Metric = ({ label, value, unit, color = "text-white" }: { label: string; value: string | number; unit?: string; color?: string }) => (
    <div className="flex flex-col">
        <span className="text-slate-600 text-[9px] font-black uppercase tracking-wider mb-1">{label}</span>
        <div className="flex items-baseline gap-1.5">
            <span className={cn("text-3xl font-black font-mono tracking-tighter", color)}>{value}</span>
            {unit && <span className="text-slate-500 text-[10px] font-bold uppercase">{unit}</span>}
        </div>
    </div>
);

// --- VISUALIZATIONS ---

const AnalogGauge = ({ value }: { value: number }) => {
    const rotation = (value / 100) * 180 - 90;
    return (
        <div className="relative flex flex-col items-center">
            <div className="w-48 h-24 overflow-hidden relative">
                <div className="w-48 h-48 border-[12px] border-slate-800 rounded-full" />
                <div
                    className="absolute inset-0 w-48 h-48 border-[12px] border-cyan-500 rounded-full transition-all duration-500"
                    style={{
                        clipPath: 'polygon(0% 50%, 100% 50%, 100% 0%, 0% 0%)',
                        transform: `rotate(${(value / 100) * 180}deg)`,
                        transformOrigin: '50% 50%',
                        opacity: 0.8
                    }}
                />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-16 bg-white origin-bottom transition-all duration-500" style={{ transform: `rotate(${rotation}deg)` }} />
            </div>
            <div className="mt-2 text-center">
                <span className="text-2xl font-black font-mono text-cyan-400">{value.toFixed(1)}%</span>
                <p className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Scaling: 0-27648</p>
            </div>
        </div>
    );
};

const BitBoard = ({ bits, onToggle }: { bits: number[], onToggle: (idx: number) => void }) => (
    <div className="grid grid-cols-4 gap-4">
        {bits.map((bit, i) => (
            <button
                key={i}
                onClick={() => onToggle(i)}
                className={cn(
                    "flex flex-col items-center p-3 rounded-lg border transition-all duration-300",
                    bit ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400" : "bg-black/40 border-white/5 text-slate-600 hover:border-white/10"
                )}
            >
                <div className={cn("w-2 h-2 rounded-full mb-2", bit ? "bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]" : "bg-slate-800")} />
                <span className="text-[10px] font-black font-mono">BIT_{i}</span>
                <span className="text-[8px] font-bold mt-1 opacity-50">{bit ? 'HIGH' : 'LOW'}</span>
            </button>
        ))}
    </div>
);

// --- MAIN APP ---

export default function App() {
    const { sendCommand } = useWebSocket();
    const state = usePLCStore();
    const [activeTab, setActiveTab] = useState('overview');

    const handleBitToggle = (idx: number) => {
        sendCommand({ bitToggle: idx });
    };

    const handleAnalogChange = (val: number) => {
        sendCommand({ setAnalog: val });
    };

    return (
        <div className="flex flex-col h-screen bg-[#020408] text-slate-200 selection:bg-cyan-500/30">
            {/* Dynamic Background */}
            <div className="fixed inset-0 bg-grid-slate pointer-events-none opacity-40" />

            {/* Header */}
            <header className="h-16 glass-header flex items-center px-8 justify-between relative z-20">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-orange-500 flex items-center justify-center shadow-[0_0_20px_rgba(249,115,22,0.4)]">
                            <Cpu className="w-6 h-6 text-black stroke-[3]" />
                        </div>
                        <div>
                            <h1 className="text-base font-black tracking-[0.2em] text-white">PLC_SHOWCASE <span className="text-orange-500">S7-1200</span></h1>
                            <div className="flex items-center gap-2 mt-0.5">
                                <div className={cn("px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest", state.isConnected ? "bg-green-500/20 text-green-400 border border-green-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30")}>
                                    {state.isConnected ? 'ONLINE' : 'DISCONNECTED'}
                                </div>
                                <span className="text-[9px] font-mono text-slate-500 uppercase tracking-tighter">Gateway: 127.0.0.1:3001</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-8">
                    <div className="flex flex-col items-end">
                        <div className="text-[10px] font-black text-cyan-500 uppercase tracking-widest flex items-center gap-2">
                            CPU_STATUS: {state.plcStatus}
                        </div>
                        <div className="text-[11px] font-mono text-slate-500 mt-1 uppercase">
                            UPTIME: {state.uptime}s
                        </div>
                    </div>
                    <button
                        onClick={() => sendCommand({ setStatus: state.plcStatus === 'RUN' ? 'STOP' : 'RUN' })}
                        className={cn(
                            "h-10 px-6 rounded-lg text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 border shadow-lg",
                            state.plcStatus === 'RUN' ? "bg-red-500/10 border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white" : "bg-green-500/10 border-green-500/30 text-green-500 hover:bg-green-500 hover:text-white"
                        )}
                    >
                        {state.plcStatus === 'RUN' ? 'PLC_STOP' : 'PLC_START'}
                    </button>
                </div>
            </header>

            <main className="flex flex-1 overflow-hidden relative z-10">
                {/* Side Nav */}
                <nav className="w-20 border-r border-white/5 bg-[#0a0d14]/60 backdrop-blur-2xl flex flex-col py-8 gap-2">
                    {[
                        { id: 'overview', icon: Activity, label: 'Live' },
                        { id: '3d', icon: Box, label: '3D' },
                        { id: 'cad', icon: FileText, label: 'CAD' },
                        { id: 'io', icon: Binary, label: 'I/O' },
                        { id: 'db', icon: Database, label: 'DBs' },
                        { id: 'network', icon: Network, label: 'PROFI' },
                        { id: 'console', icon: Terminal, label: 'CLI' },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={cn(
                                "group relative flex flex-col items-center justify-center py-4 transition-all duration-300",
                                activeTab === item.id ? "text-cyan-400" : "text-slate-700 hover:text-slate-400"
                            )}
                        >
                            <item.icon className={cn("w-5 h-5 mb-1.5", activeTab === item.id ? "drop-shadow-[0_0_8px_rgba(0,242,255,0.7)]" : "")} />
                            <span className="text-[8px] font-black tracking-widest uppercase">{item.label}</span>
                            {activeTab === item.id && (
                                <div className="absolute right-0 top-1/4 bottom-1/4 w-1 bg-cyan-500 shadow-[0_0_15px_rgba(0,242,255,1)]" />
                            )}
                        </button>
                    ))}
                </nav>

                <div className="flex-1 overflow-hidden">
                    {activeTab === 'cad' ? (
                        <CADViewer />
                    ) : activeTab === '3d' ? (
                        <PlantVisualization3D />
                    ) : activeTab === 'overview' ? (
                        <div className="max-w-7xl mx-auto space-y-6">

                            <div className="grid grid-cols-12 gap-6">
                                {/* Left Column: Telemetry */}
                                <div className="col-span-12 lg:col-span-8 space-y-6">
                                    <div className="grid grid-cols-3 gap-6">
                                        <Card title="Analog Feedback" icon={RefreshCw}>
                                            <div className="flex justify-center py-4">
                                                <AnalogGauge value={state.analogValue} />
                                            </div>
                                        </Card>
                                        <Card title="Digital Outputs" icon={Zap} className="col-span-2">
                                            <BitBoard bits={state.digitalBits} onToggle={handleBitToggle} />
                                        </Card>
                                    </div>

                                    <Card title="HMI Control Center" icon={Sliders}>
                                        <div className="space-y-8 py-2">
                                            <div>
                                                <div className="flex justify-between items-center mb-4">
                                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Analog Process Variable (PV)</span>
                                                    <span className="text-xs font-mono font-bold text-cyan-400">{state.analogValue.toFixed(1)}%</span>
                                                </div>
                                                <input
                                                    type="range"
                                                    min="0"
                                                    max="100"
                                                    step="0.1"
                                                    value={state.analogValue}
                                                    onChange={(e) => handleAnalogChange(parseFloat(e.target.value))}
                                                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                                />
                                            </div>
                                            <div className="grid grid-cols-2 gap-8">
                                                <div className="p-4 rounded-xl bg-black/40 border border-white/5">
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <div className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_10px_rgba(34,211,238,1)]" />
                                                        <span className="text-[9px] font-black text-slate-300 uppercase underline decoration-cyan-500/50 decoration-2 underline-offset-4">HMI Heartbeat</span>
                                                    </div>
                                                    <p className="text-[10px] text-slate-500 leading-relaxed font-bold italic">WebSocket connection active. Packet delay: ~1ms.</p>
                                                </div>
                                                <div className="p-4 rounded-xl bg-cyan-500/5 border border-cyan-500/10">
                                                    <p className="text-[9px] font-black text-cyan-400 uppercase mb-2">Process Counter</p>
                                                    <span className="text-2xl font-black font-mono tracking-tighter text-white">{state.counter}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                </div>

                                {/* Right Column: Core Health */}
                                <div className="col-span-12 lg:col-span-4 space-y-6">
                                    <Card title="CPU Analytics" icon={Cpu}>
                                        <div className="space-y-6">
                                            <Metric label="CPU Temperature" value={state.cpuTemp.toFixed(1)} unit="°C" color="text-orange-400" />
                                            <div className="h-px bg-white/5" />
                                            <Metric label="Memory Usage" value="12.4" unit="MB" color="text-cyan-400" />
                                            <div className="h-px bg-white/5" />
                                            <Metric label="Cyclic Time" value="2" unit="ms" color="text-green-400" />
                                        </div>
                                    </Card>

                                    <Card title="System Log" icon={Terminal}>
                                        <div className="space-y-3 font-mono text-[9px]">
                                            <div className="flex gap-2 text-cyan-500/70">
                                                <span>[15:34:01]</span>
                                                <span className="text-white underline font-bold uppercase tracking-tighter">Connection_Auth_OK</span>
                                            </div>
                                            <div className="flex gap-2 text-slate-600 font-bold uppercase tracking-tighter">
                                                <span>[15:34:02]</span>
                                                <span>Session_Established_V2</span>
                                            </div>
                                            <div className="flex gap-2 text-orange-500/70 font-bold uppercase tracking-tighter">
                                                <span>[15:34:05]</span>
                                                <span>Analog_Buffer_Sync_Complete</span>
                                            </div>
                                            <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-2 group cursor-pointer">
                                                <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-pulse" />
                                                <span className="text-[8px] font-black text-slate-500 uppercase group-hover:text-cyan-400 transition-colors">Monitoring live signals...</span>
                                            </div>
                                        </div>
                                    </Card>
                                </div>
                            </div>
                        </div>
                    ) : activeTab !== '3d' && activeTab !== 'cad' ? (
                        <div className="flex flex-col items-center justify-center min-h-[500px] border border-dashed border-white/10 rounded-3xl bg-black/30 m-8">
                            <Database className="w-12 h-12 text-slate-800 mb-6" />
                            <h2 className="text-xs font-black uppercase tracking-[0.4em] text-slate-700">Engineering Module Offline</h2>
                            <p className="text-[10px] text-slate-800 mt-4 max-w-xs text-center font-bold uppercase leading-relaxed">
                                Please connect actual S7-1200 hardware to enable detailed DB mapping and PROFINET diagnostics.
                            </p>
                        </div>
                    ) : null}
                </div>
            </main>

            {/* Footer */}
            <footer className="h-10 bg-[#0a0d14] border-t border-white/5 flex items-center justify-between px-8 relative z-20">
                <div className="flex items-center gap-10">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full shadow-[0_0_10px_rgba(34,197,94,1)]" />
                        <span className="text-[9px] font-black text-slate-600 uppercase tracking-widest">S7_COMMUNICATION_READY</span>
                    </div>
                </div>
                <div className="flex items-center gap-6 text-[9px] font-mono text-slate-700 font-bold uppercase tracking-tighter">
                    <span>V_DEMO_2026.1</span>
                    <span className="opacity-30">|</span>
                    <span>PACKET_LOSS: 0.00%</span>
                </div>
            </footer>
        </div>
    );
}
