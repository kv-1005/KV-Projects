import { useState } from 'react';
import { useMotionStore } from '../store/motionStore';
import { useAuthStore } from '../store/authStore';
import { AlertTriangle, CheckCircle, X, RefreshCw, Search } from 'lucide-react';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import './Alarms.css';

const FAULT_DESCRIPTIONS: Record<string, { description: string; remedy: string }> = {
    'A.020': { description: 'Parameter Checksum Error', remedy: 'Reinitialize parameters via TIA Portal / Drive commissioning software' },
    'A.040': { description: 'Main Circuit Voltage Error (Under Voltage)', remedy: 'Check 200V AC power supply to drive' },
    'A.710': { description: 'Overload (Instantaneous Max Load)', remedy: 'Reduce load or increase deceleration time' },
    'A.720': { description: 'Overload (Continuous Max Load)', remedy: 'Check mechanical load and duty cycle' },
    'A.C10': { description: 'Runaway Detected', remedy: 'Check encoder wiring and motor connection' },
    'A.510': { description: 'Overspeed', remedy: 'Reduce velocity command, check speed loop gain' },
    'A.d00': { description: 'Position Error Overflow', remedy: 'Check for mechanical jam or excessive load' },
    'A.810': { description: 'Encoder Backup Error (Battery)', remedy: 'Replace encoder backup battery' },
    'SW.001': { description: 'Positive Software Limit Exceeded', remedy: 'Move axis in negative direction' },
    'SW.002': { description: 'Negative Software Limit Exceeded', remedy: 'Move axis in positive direction' },
};

export default function Alarms() {
    const { alarms, status, resetAlarms, injectFault } = useMotionStore();
    const { hasPermission } = useAuthStore();
    const [confirmReset, setConfirmReset] = useState(false);
    const [search, setSearch] = useState('');
    const [lookup, setLookup] = useState('');

    const active = alarms.filter(a => !a.acknowledged);
    const history = alarms.filter(a => a.acknowledged);
    const filtered = history.filter(a =>
        a.code.toLowerCase().includes(search.toLowerCase()) ||
        a.description.toLowerCase().includes(search.toLowerCase())
    );

    const lookupResult = lookup ? FAULT_DESCRIPTIONS[lookup.toUpperCase()] : null;

    const handleReset = () => {
        resetAlarms();
        setConfirmReset(false);
    };

    return (
        <div className="alarms animate-fade">
            <div className="section-header">
                <div>
                    <div className="section-title">Alarm & Diagnostics Center</div>
                    <div className="section-sub">S7-1200 + SGD7S Fault Management</div>
                </div>
                <div className="flex gap-2">
                    {hasPermission('ADMIN') && (
                        <button className="btn btn-ghost btn-sm" onClick={() => injectFault('A.710')}>
                            ⚡ Inject Fault
                        </button>
                    )}
                    <button
                        className="btn btn-warning btn-sm"
                        onClick={() => setConfirmReset(true)}
                        disabled={!status.faultActive}
                    >
                        <RefreshCw size={14} /> Reset Alarms
                    </button>
                </div>
            </div>

            {/* Active alarms */}
            <div className="card mb-4">
                <div className="card-header">
                    <AlertTriangle size={15} className={active.length > 0 ? 'text-red' : 'text-green'} />
                    <h3>Active Alarms</h3>
                    <span className={`badge ml-auto ${active.length > 0 ? 'badge-fault' : 'badge-ready'}`} style={{ marginLeft: 'auto' }}>
                        {active.length}
                    </span>
                </div>
                {active.length === 0 ? (
                    <div className="alarms-empty">
                        <CheckCircle size={28} className="text-green" />
                        <span>No active alarms — System normal</span>
                    </div>
                ) : (
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Code</th>
                                    <th>Severity</th>
                                    <th>Description</th>
                                    <th>Remedy</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                {active.map(a => (
                                    <tr key={a.id} className={`alarm-row-${a.severity}`}>
                                        <td className={`mono severity-${a.severity}`}>{a.code}</td>
                                        <td>
                                            <span className={`badge ${a.severity === 'CRITICAL' ? 'badge-fault' : a.severity === 'WARNING' ? 'badge-homing' : 'badge-moving'}`}>
                                                {a.severity}
                                            </span>
                                        </td>
                                        <td>{a.description}</td>
                                        <td className="text-muted">{a.remedy}</td>
                                        <td className="mono text-muted">{(a.timestamp instanceof Date ? a.timestamp : new Date(a.timestamp)).toLocaleTimeString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Fault code lookup */}
            <div className="card mb-4">
                <div className="card-header"><Search size={15} /><h3>Fault Code Lookup</h3></div>
                <div className="card-body">
                    <div className="input-row">
                        <input className="input" type="text" placeholder="Enter code e.g. A.710, SW.001..." value={lookup} onChange={e => setLookup(e.target.value)} style={{ maxWidth: 300 }} />
                    </div>
                    {lookupResult ? (
                        <div className="lookup-result">
                            <div className="lookup-code mono text-amber">{lookup.toUpperCase()}</div>
                            <div className="lookup-desc">{lookupResult.description}</div>
                            <div className="lookup-remedy"><span>Remedy:</span> {lookupResult.remedy}</div>
                        </div>
                    ) : lookup ? (
                        <div className="lookup-result text-muted">No code found for "{lookup}"</div>
                    ) : null}
                    <div className="fault-chips">
                        {Object.keys(FAULT_DESCRIPTIONS).map(code => (
                            <button key={code} className="btn btn-ghost btn-sm mono" onClick={() => setLookup(code)}>{code}</button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Alarm history */}
            <div className="card">
                <div className="card-header">
                    <X size={15} />
                    <h3>Alarm History</h3>
                    <div className="ml-auto flex gap-2 items-center" style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
                        <input className="input" style={{ width: 200, padding: '5px 10px', fontSize: '0.75rem' }}
                            type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />
                        <span className="text-muted" style={{ fontSize: '0.72rem' }}>{filtered.length} events</span>
                    </div>
                </div>
                {filtered.length === 0 ? (
                    <div className="alarms-empty"><span className="text-muted">No alarm history yet</span></div>
                ) : (
                    <div className="table-container" style={{ maxHeight: 280, overflowY: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Code</th>
                                    <th>Severity</th>
                                    <th>Description</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(a => (
                                    <tr key={a.id}>
                                        <td className="mono text-muted">{(a.timestamp instanceof Date ? a.timestamp : new Date(a.timestamp)).toLocaleString()}</td>
                                        <td className={`mono severity-${a.severity}`}>{a.code}</td>
                                        <td>
                                            <span className={`badge ${a.severity === 'CRITICAL' ? 'badge-fault' : a.severity === 'WARNING' ? 'badge-homing' : 'badge-moving'}`} style={{ opacity: 0.7 }}>
                                                {a.severity}
                                            </span>
                                        </td>
                                        <td>{a.description}</td>
                                        <td><span className="badge badge-ready" style={{ opacity: 0.7 }}>CLEARED</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {confirmReset && (
                <ConfirmDialog
                    title="Reset Alarms"
                    message="Ensure the physical fault condition is resolved. Resetting without resolving may cause repeated faults. Confirm alarm reset?"
                    danger
                    onConfirm={handleReset}
                    onCancel={() => setConfirmReset(false)}
                />
            )}
        </div>
    );
}
