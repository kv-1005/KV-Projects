import { useState } from 'react';
import { useMotionStore } from '../store/motionStore';
import { ClipboardList, Download, Filter } from 'lucide-react';
import './AuditLog.css';

const COMMANDS = ['ALL', 'ServoOn', 'ServoOff', 'Homing', 'AbsMove', 'RelMove', 'JogFWD', 'JogREV', 'JogStop', 'ImmediateStop', 'AlarmReset', 'SetSoftLimits', 'InjectFault'];

export default function AuditLog() {
    const { auditLog } = useMotionStore();
    const [filter, setFilter] = useState('ALL');
    const [resultFilter, setResultFilter] = useState('ALL');

    const filtered = auditLog.filter(e => {
        const cmdMatch = filter === 'ALL' || e.command === filter;
        const resMatch = resultFilter === 'ALL' || e.result === resultFilter;
        return cmdMatch && resMatch;
    });

    const handleExport = () => {
        const header = 'Timestamp,User,Command,Parameters,Result\n';
        const rows = filtered.map(e =>
            `"${(e.timestamp instanceof Date ? e.timestamp : new Date(e.timestamp)).toISOString()}","${e.user}","${e.command}","${e.parameters}","${e.result}"`
        ).join('\n');
        const blob = new Blob([header + rows], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const successCount = auditLog.filter(e => e.result === 'SUCCESS').length;
    const rejectedCount = auditLog.filter(e => e.result === 'REJECTED').length;
    const faultCount = auditLog.filter(e => e.result === 'FAULT').length;

    return (
        <div className="audit-log animate-fade">
            <div className="section-header">
                <div>
                    <div className="section-title">Audit Log</div>
                    <div className="section-sub">Immutable command trace — {auditLog.length} total events</div>
                </div>
                <button className="btn btn-outline btn-sm" onClick={handleExport} disabled={filtered.length === 0}>
                    <Download size={14} /> Export CSV
                </button>
            </div>

            {/* Stats */}
            <div className="grid-3 mb-4">
                <div className="stat-card">
                    <div className="stat-label">Total Commands</div>
                    <div className="stat-value text-cyan">{auditLog.length}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Successful</div>
                    <div className="stat-value text-green">{successCount}</div>
                    <div className="stat-sub">{auditLog.length ? ((successCount / auditLog.length) * 100).toFixed(0) : 0}% success rate</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Rejected / Faults</div>
                    <div className={`stat-value ${rejectedCount + faultCount > 0 ? 'text-amber' : 'text-muted'}`}>
                        {rejectedCount + faultCount}
                    </div>
                    <div className="stat-sub">{rejectedCount} rejected · {faultCount} faults</div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="card-header"><Filter size={15} /><h3>Filters</h3></div>
                <div className="card-body">
                    <div className="audit-filters">
                        <div className="input-group">
                            <label>Command</label>
                            <select className="input" value={filter} onChange={e => setFilter(e.target.value)}
                                style={{ cursor: 'pointer' }}>
                                {COMMANDS.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Result</label>
                            <select className="input" value={resultFilter} onChange={e => setResultFilter(e.target.value)}
                                style={{ cursor: 'pointer' }}>
                                <option value="ALL">ALL</option>
                                <option value="SUCCESS">SUCCESS</option>
                                <option value="REJECTED">REJECTED</option>
                                <option value="FAULT">FAULT</option>
                            </select>
                        </div>
                        <div className="audit-filter-info">
                            <span className="text-muted" style={{ fontSize: '0.72rem' }}>{filtered.length} results</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Log table */}
            <div className="card">
                <div className="card-header">
                    <ClipboardList size={15} />
                    <h3>Command Log</h3>
                    <span className="text-muted" style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>Latest first · Max 500 entries</span>
                </div>
                {filtered.length === 0 ? (
                    <div className="audit-empty">
                        <ClipboardList size={28} className="text-muted" />
                        <span className="text-muted">No commands logged yet — interact with the Axis Control panel</span>
                    </div>
                ) : (
                    <div className="table-container" style={{ maxHeight: 420, overflowY: 'auto' }}>
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
                                {filtered.map(e => (
                                    <tr key={e.id}>
                                        <td className="mono text-muted" style={{ fontSize: '0.75rem' }}>
                                            {(e.timestamp instanceof Date ? e.timestamp : new Date(e.timestamp)).toLocaleString()}
                                        </td>
                                        <td>{e.user}</td>
                                        <td className="mono text-cyan">{e.command}</td>
                                        <td className="text-muted" style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {e.parameters || '—'}
                                        </td>
                                        <td>
                                            <span className={`badge ${e.result === 'SUCCESS' ? 'badge-ready' :
                                                    e.result === 'REJECTED' ? 'badge-servo-off' : 'badge-fault'
                                                }`}>
                                                {e.result}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
