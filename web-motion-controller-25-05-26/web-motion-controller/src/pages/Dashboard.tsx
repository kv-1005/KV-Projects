import { useMotionStore } from '../store/motionStore';
import { useAuthStore } from '../store/authStore';
import { MAX_VELOCITY } from '../simulation/S71200Simulator';
import {
    Activity, Thermometer, Zap, Clock, TrendingUp,
    AlertTriangle, CheckCircle, Server, Cpu
} from 'lucide-react';
import './Dashboard.css';

function StateCard() {
    const { status } = useMotionStore();
    const stateClass = `badge-${status.state.toLowerCase().replace('_', '-')}`;
    return (
        <div className="card dashboard-state-card">
            <div className="card-header">
                <Cpu size={15} />
                <h3>Axis 1 — S7-1200 ↔ MP2300S</h3>
            </div>
            <div className="card-body">
                <div className="ds-state-row">
                    <span className={`badge ${stateClass} badge-xl`}>
                        <span className={`led ${status.state === 'READY' ? 'led-green' :
                            status.state === 'FAULT' ? 'led-red' :
                                status.state === 'MOVING' || status.state === 'JOGGING' ? 'led-cyan' :
                                    status.state === 'HOMING' ? 'led-amber' : 'led-gray'
                            }`} />
                        {status.state.replace('_', ' ')}
                    </span>
                    <div>
                        <div className="ds-kv">
                            <span>Servo</span>
                            <span className={status.servoOn ? 'text-green' : 'text-muted'}>{status.servoOn ? 'ON' : 'OFF'}</span>
                        </div>
                        <div className="ds-kv">
                            <span>Homed</span>
                            <span className={status.homed ? 'text-green' : 'text-amber'}>{status.homed ? 'YES' : 'NO'}</span>
                        </div>
                        <div className="ds-kv">
                            <span>STO</span>
                            <span className={status.stoActive ? 'text-red' : 'text-green'}>{status.stoActive ? 'ACTIVE' : 'OK'}</span>
                        </div>
                    </div>
                </div>

                {/* Axis visualizer */}
                <div className="ds-axis-section">
                    <div className="ds-axis-labels">
                        <span className="mono text-muted" style={{ fontSize: '0.7rem' }}>{status.softLimitMin}mm</span>
                        <span className="mono text-muted" style={{ fontSize: '0.7rem' }}>{status.softLimitMax}mm</span>
                    </div>
                    <div className="axis-track">
                        <div
                            className="axis-cursor"
                            style={{ left: `calc(${Math.min(100, Math.max(0, (status.actualPosition / Math.max(status.softLimitMax, 1)) * 100))}% - 7px)` }}
                        />
                    </div>
                    <div className="ds-axis-pos mono text-cyan" style={{ fontSize: '1.4rem', fontWeight: 600 }}>
                        {status.actualPosition.toFixed(3)} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>mm</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function Dashboard() {
    const { status, alarms, auditLog } = useMotionStore();
    const { user } = useAuthStore();
    const activeAlarms = alarms.filter(a => !a.acknowledged);

    return (
        <div className="dashboard animate-fade">
            {/* Welcome */}
            <div className="section-header">
                <div>
                    <div className="section-title">System Overview</div>
                    <div className="section-sub">Welcome back, {user?.name} · {new Date().toLocaleString()}</div>
                </div>
            </div>

            {/* Stats row */}
            <div className="grid-4 mb-4">
                <div className="stat-card">
                    <div className="stat-label"><Activity size={12} style={{ verticalAlign: 'middle' }} /> Position</div>
                    <div className="stat-value text-cyan">{status.actualPosition.toFixed(2)}<span className="stat-unit">mm</span></div>
                    <div className="stat-sub">Target: {status.targetPosition.toFixed(2)}mm</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label"><TrendingUp size={12} style={{ verticalAlign: 'middle' }} /> Velocity</div>
                    <div className={`stat-value ${Math.abs(status.actualVelocity) > 0 ? 'text-cyan' : 'text-muted'}`}>
                        {Math.abs(status.actualVelocity).toFixed(1)}<span className="stat-unit">mm/s</span>
                    </div>
                    <div className="stat-sub">Max: {MAX_VELOCITY} mm/s</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label"><Zap size={12} style={{ verticalAlign: 'middle' }} /> Torque</div>
                    <div className={`stat-value ${status.torquePercent > 70 ? 'text-amber' : 'text-green'}`}>
                        {status.torquePercent.toFixed(1)}<span className="stat-unit">%</span>
                    </div>
                    <div className="progress-track mt-2">
                        <div className={`progress-bar ${status.torquePercent > 70 ? 'progress-amber' : 'progress-green'}`}
                            style={{ width: `${status.torquePercent}%` }} />
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-label"><AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> Alarms</div>
                    <div className={`stat-value ${activeAlarms.length > 0 ? 'text-red' : 'text-green'}`}>
                        {activeAlarms.length}
                    </div>
                    <div className="stat-sub">{alarms.length} total events</div>
                </div>
            </div>

            <div className="grid-2 mb-4">
                {/* State card */}
                <StateCard />

                {/* Drive health */}
                <div className="card">
                    <div className="card-header">
                        <Server size={15} />
                        <h3>Drive Health — SGD7S via S7-1200</h3>
                    </div>
                    <div className="card-body">
                        <div className="ds-health-grid">
                            <div className="ds-health-item">
                                <Thermometer size={15} className="text-amber" />
                                <div>
                                    <div className="ds-health-label">Drive Temp</div>
                                    <div className={`ds-health-val mono ${status.driveTemp > 55 ? 'text-red' : status.driveTemp > 45 ? 'text-amber' : 'text-green'}`}>
                                        {status.driveTemp.toFixed(1)}°C
                                    </div>
                                    <div className="progress-track mt-2" style={{ width: 100 }}>
                                        <div className={`progress-bar ${status.driveTemp > 55 ? 'progress-red' : status.driveTemp > 45 ? 'progress-amber' : 'progress-green'}`}
                                            style={{ width: `${(status.driveTemp / 85) * 100}%` }} />
                                    </div>
                                </div>
                            </div>
                            <div className="ds-health-item">
                                <Zap size={15} className="text-cyan" />
                                <div>
                                    <div className="ds-health-label">DC Bus Voltage</div>
                                    <div className="ds-health-val mono text-cyan">{status.busVoltage.toFixed(1)} V</div>
                                    <div className="stat-sub">Nominal: 310V</div>
                                </div>
                            </div>
                            <div className="ds-health-item">
                                <Cpu size={15} className="text-purple" />
                                <div>
                                    <div className="ds-health-label">Encoder Counts</div>
                                    <div className="ds-health-val mono text-purple">{status.encoderCounts.toLocaleString()}</div>
                                    <div className="stat-sub">24-bit absolute</div>
                                </div>
                            </div>
                            <div className="ds-health-item">
                                <Clock size={15} className="text-muted" />
                                <div>
                                    <div className="ds-health-label">Fault Code</div>
                                    <div className={`ds-health-val mono ${status.alarmCode ? 'text-red' : 'text-green'}`}>
                                        {status.alarmCode ?? 'NONE'}
                                    </div>
                                    <div className="stat-sub">{status.faultActive ? 'FAULT ACTIVE' : 'Normal'}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent audit log */}
            <div className="card">
                <div className="card-header">
                    <CheckCircle size={15} />
                    <h3>Recent Commands</h3>
                    <span className="ml-auto text-muted" style={{ fontSize: '0.7rem', marginLeft: 'auto' }}>Last 5 events</span>
                </div>
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>User</th>
                                <th>Command</th>
                                <th>Parameters</th>
                                <th>Result</th>
                            </tr>
                        </thead>
                        <tbody>
                            {auditLog.slice(0, 5).map(e => (
                                <tr key={e.id}>
                                    <td>{e.timestamp instanceof Date ? e.timestamp.toLocaleTimeString() : new Date(e.timestamp).toLocaleTimeString()}</td>
                                    <td>{e.user}</td>
                                    <td className="text-cyan">{e.command}</td>
                                    <td className="text-muted">{e.parameters || '—'}</td>
                                    <td>
                                        <span className={`badge ${e.result === 'SUCCESS' ? 'badge-ready' : e.result === 'REJECTED' ? 'badge-servo-off' : 'badge-fault'}`}>
                                            {e.result}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {auditLog.length === 0 && (
                                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>No commands yet</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
