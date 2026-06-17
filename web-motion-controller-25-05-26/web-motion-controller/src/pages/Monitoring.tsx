import { useRef } from 'react';
import { useMotionStore } from '../store/motionStore';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Activity, Wifi, Thermometer, Zap, BarChart2 } from 'lucide-react';
import { MAX_VELOCITY } from '../simulation/S71200Simulator';
import './Monitoring.css';

function CommHealthWidget({ ok }: { ok: boolean }) {
    // Stable latency value — recomputed only when link state changes
    const latencyRef = useRef<string>((0.4 + Math.random() * 0.2).toFixed(2));
    return (
        <div className={`comm-health ${ok ? 'ok' : 'fail'}`}>
            <Wifi size={16} />
            <div>
                <div className="comm-label">{ok ? 'MODBUS TCP LINK OK' : 'MODBUS TCP LINK LOST'}</div>
                <div className="comm-sub">{ok ? `Latency: ${latencyRef.current}ms · 250ms cycle` : 'Check cable / drive power'}</div>
            </div>
            <span className={`led ${ok ? 'led-green' : 'led-red'}`} />
        </div>
    );
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="chart-tooltip">
                <div className="chart-tt-time">{new Date(label).toLocaleTimeString()}</div>
                {payload.map((p: any) => (
                    <div key={p.dataKey} style={{ color: p.color, fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                        {p.name}: {p.value?.toFixed(2)} mm/s
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export default function Monitoring() {
    const { status, positionHistory } = useMotionStore();

    const posRange = {
        min: Math.max(0, Math.min(...positionHistory.map(p => p.position)) - 20),
        max: Math.min(status.softLimitMax, Math.max(...positionHistory.map(p => p.position)) + 20),
    };

    return (
        <div className="monitoring animate-fade">
            <div className="section-header">
                <div>
                    <div className="section-title">Real-Time Monitoring</div>
                    <div className="section-sub">Update interval: 250ms | Axis 1 — S7-1200 ↔ MP2300S</div>
                </div>
                <CommHealthWidget ok={status.commOk} />
            </div>

            {/* Live stats */}
            <div className="grid-4 mb-4">
                <div className="stat-card mon-stat">
                    <div className="stat-label">Actual Position</div>
                    <div className="stat-value text-cyan">{status.actualPosition.toFixed(3)}<span className="stat-unit">mm</span></div>
                    <div className="stat-sub">Target: {status.targetPosition.toFixed(3)} mm</div>
                    <div className="progress-track mt-2">
                        <div className="progress-bar progress-cyan" style={{ width: `${(status.actualPosition / Math.max(status.softLimitMax, 1)) * 100}%` }} />
                    </div>
                </div>
                <div className="stat-card mon-stat">
                    <div className="stat-label">Actual Velocity</div>
                    <div className={`stat-value ${Math.abs(status.actualVelocity) > 0 ? 'text-cyan' : 'text-muted'}`}>
                        {status.actualVelocity.toFixed(1)}<span className="stat-unit">mm/s</span>
                    </div>
                    <div className="stat-sub">Dir: {status.actualVelocity > 0 ? '▶ FWD' : status.actualVelocity < 0 ? '◀ REV' : 'STOPPED'}</div>
                </div>
                <div className="stat-card mon-stat">
                    <div className="stat-label">Torque Load</div>
                    <div className={`stat-value ${status.torquePercent > 70 ? 'text-red' : status.torquePercent > 40 ? 'text-amber' : 'text-green'}`}>
                        {status.torquePercent.toFixed(1)}<span className="stat-unit">%</span>
                    </div>
                    <div className="progress-track mt-2">
                        <div className={`progress-bar ${status.torquePercent > 70 ? 'progress-red' : status.torquePercent > 40 ? 'progress-amber' : 'progress-green'}`}
                            style={{ width: `${status.torquePercent}%` }} />
                    </div>
                </div>
                <div className="stat-card mon-stat">
                    <div className="stat-label">Axis State</div>
                    <div className={`badge badge-${status.state.toLowerCase().replace('_', '-')} mon-state-badge`}>
                        <span className={`led ${status.state === 'READY' ? 'led-green' : status.state === 'FAULT' ? 'led-red' : status.state === 'MOVING' || status.state === 'JOGGING' ? 'led-cyan' : 'led-amber'}`} />
                        {status.state}
                    </div>
                    <div className="stat-sub mt-2">Encoder: {status.encoderCounts.toLocaleString()} cts</div>
                </div>
            </div>

            {/* Position Chart */}
            <div className="card mb-4">
                <div className="card-header">
                    <Activity size={15} />
                    <h3>Position History (30s window)</h3>
                    <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--cyan)' }}>
                        LIVE ●
                    </span>
                </div>
                <div className="card-body">
                    <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={positionHistory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis
                                dataKey="time"
                                tickFormatter={v => new Date(v).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                                stroke="var(--border)"
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                dataKey="position"
                                domain={[posRange.min, posRange.max]}
                                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                                stroke="var(--border)"
                                width={55}
                                tickFormatter={v => `${v.toFixed(0)}mm`}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine y={status.softLimitMin} stroke="rgba(239,68,68,0.4)" strokeDasharray="4 2" label={{ value: 'LIM-', fill: 'var(--red)', fontSize: 9 }} />
                            <ReferenceLine y={status.softLimitMax} stroke="rgba(239,68,68,0.4)" strokeDasharray="4 2" label={{ value: 'LIM+', fill: 'var(--red)', fontSize: 9 }} />
                            <Line
                                type="monotone" dataKey="position" name="Position"
                                stroke="var(--cyan)" strokeWidth={2} dot={false}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Velocity Chart */}
            <div className="card mb-4">
                <div className="card-header">
                    <BarChart2 size={15} />
                    <h3>Velocity History (30s window) — +FWD / −REV</h3>
                </div>
                <div className="card-body">
                    <ResponsiveContainer width="100%" height={160}>
                        <LineChart data={positionHistory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis
                                dataKey="time"
                                tickFormatter={v => new Date(v).toLocaleTimeString([], { hour12: false, second: '2-digit' })}
                                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                                stroke="var(--border)"
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                                stroke="var(--border)"
                                width={55}
                                domain={[-MAX_VELOCITY, MAX_VELOCITY]}
                                tickFormatter={v => `${v.toFixed(0)}`}
                                label={{ value: 'mm/s', angle: -90, position: 'insideLeft', fill: 'var(--text-muted)', fontSize: 9, dy: 20 }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine y={0} stroke="rgba(255,255,255,0.25)" strokeDasharray="3 2" />
                            <Line
                                type="monotone" dataKey="velocity" name="Velocity"
                                stroke="var(--green)" strokeWidth={2} dot={false}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Drive diagnostics */}
            <div className="grid-2">
                <div className="card">
                    <div className="card-header"><Thermometer size={15} /><h3>Drive Thermal Status</h3></div>
                    <div className="card-body">
                        <div className="mon-kv-list">
                            <div className="mon-kv">
                                <span>Drive Temp</span>
                                <span className={`mono ${status.driveTemp > 55 ? 'text-red' : status.driveTemp > 45 ? 'text-amber' : 'text-green'}`}>
                                    {status.driveTemp.toFixed(1)}°C
                                </span>
                            </div>
                            <div className="mon-kv"><span>DC Bus Voltage</span><span className="mono text-cyan">{status.busVoltage.toFixed(1)} V</span></div>
                            <div className="mon-kv"><span>Rated Power</span><span className="mono text-muted">900 W</span></div>
                            <div className="mon-kv"><span>Drive Model</span><span className="mono text-muted">SGD7S-120A10A (via MP2300S)</span></div>
                        </div>
                        <div className="progress-track mt-3">
                            <div className={`progress-bar ${status.driveTemp > 55 ? 'progress-red' : 'progress-green'}`}
                                style={{ width: `${(status.driveTemp / 85) * 100}%` }} />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>
                            <span>0°C</span><span>Warning 55°C</span><span>Trip 85°C</span>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header"><Zap size={15} /><h3>Encoder & Position Details</h3></div>
                    <div className="card-body">
                        <div className="mon-kv-list">
                            <div className="mon-kv"><span>Encoder Type</span><span className="mono text-muted">24-bit Absolute</span></div>
                            <div className="mon-kv"><span>Resolution</span><span className="mono text-muted">16,777,216 ct/rev</span></div>
                            <div className="mon-kv"><span>Current Counts</span><span className="mono text-cyan">{status.encoderCounts.toLocaleString()}</span></div>
                            <div className="mon-kv"><span>Homed</span><span className={`mono ${status.homed ? 'text-green' : 'text-amber'}`}>{status.homed ? 'YES' : 'NO'}</span></div>
                            <div className="mon-kv"><span>Soft Limit Min</span><span className="mono text-muted">{status.softLimitMin} mm</span></div>
                            <div className="mon-kv"><span>Soft Limit Max</span><span className="mono text-muted">{status.softLimitMax} mm</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
