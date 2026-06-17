import { useState, useEffect, useRef } from 'react';
import { useMotionStore } from '../store/motionStore';
import { useAuthStore } from '../store/authStore';
import {
    Power, Home, ArrowRight, RefreshCw, Square,
    ChevronLeft, ChevronRight, AlertTriangle, Settings, Info
} from 'lucide-react';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import { JOG_VELOCITY } from '../simulation/S71200Simulator';
import './AxisControl.css';

function Toast({ msg, ok }: { msg: string; ok: boolean }) {
    return (
        <div className={`ac-toast ${ok ? 'ok' : 'fail'}`}>
            {ok ? '✓' : '✕'} {msg}
        </div>
    );
}

export default function AxisControl() {
    const store = useMotionStore();
    const { status } = store;
    const { user, hasPermission } = useAuthStore();

    const [absTarget, setAbsTarget] = useState('');
    const [relDelta, setRelDelta] = useState('');
    const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
    const [confirmStop, setConfirmStop] = useState(false);
    const [confirmReset, setConfirmReset] = useState(false);
    const [softMinInput, setSoftMinInput] = useState(String(status.softLimitMin));
    const [softMaxInput, setSoftMaxInput] = useState(String(status.softLimitMax));
    const homingStartPosRef = useRef<number | null>(null);

    // Sync soft limit inputs when the live state changes (e.g. after external update)
    useEffect(() => {
        setSoftMinInput(String(status.softLimitMin));
        setSoftMaxInput(String(status.softLimitMax));
    }, [status.softLimitMin, status.softLimitMax]);

    // Track position at homing start for accurate progress
    useEffect(() => {
        if (status.state === 'HOMING' && homingStartPosRef.current === null) {
            homingStartPosRef.current = status.actualPosition;
        } else if (status.state !== 'HOMING') {
            homingStartPosRef.current = null;
        }
    }, [status.state, status.actualPosition]);


    const isEngineerPlus = hasPermission('ENGINEER');
    const isAdmin = hasPermission('ADMIN');

    const showToast = (msg: string, ok = true) => {
        setToast({ msg, ok });
        setTimeout(() => setToast(null), 3000);
    };

    const dispatch = (result: string, command: string) => {
        const ok = result === 'SUCCESS' || result === 'OK';
        showToast(ok ? `${command}: OK` : result.replace('REJECTED: ', ''), ok);
    };

    // ─── Commands ───────────────────────────────────────
    const handleServoToggle = () => {
        if (status.servoOn) {
            dispatch(store.servoOff(), 'Servo OFF');
        } else {
            dispatch(store.servoOn(), 'Servo ON');
        }
    };

    const handleHome = () => {
        dispatch(store.startHoming(), 'Homing');
    };

    const handleAbsMove = () => {
        const val = parseFloat(absTarget);
        if (isNaN(val)) { showToast('Enter a valid position', false); return; }
        dispatch(store.absoluteMove(val), `Abs Move → ${val}mm`);
    };

    const handleRelMove = () => {
        const val = parseFloat(relDelta);
        if (isNaN(val)) { showToast('Enter a valid delta', false); return; }
        dispatch(store.relativeMove(val), `Rel Move +${val}mm`);
    };

    const handleJogStart = (dir: 'FWD' | 'REV') => {
        dispatch(store.jogStart(dir), `Jog ${dir}`);
    };

    const handleJogStop = () => {
        store.jogStop();
    };

    const handleStop = () => {
        dispatch(store.immediateStop(), 'STOP');
        setConfirmStop(false);
    };

    const handleAlarmReset = () => {
        dispatch(store.resetAlarms(), 'Alarm Reset');
        setConfirmReset(false);
    };

    const handleSoftLimits = () => {
        const min = parseFloat(softMinInput);
        const max = parseFloat(softMaxInput);
        if (isNaN(min) || isNaN(max) || min >= max) {
            showToast('Invalid soft limits: min must be < max', false);
            return;
        }
        dispatch(store.setSoftLimits(min, max), 'Soft Limits Updated');
    };

    const handleInjectFault = () => {
        store.injectFault('A.710');
        showToast('Fault injected: A.710 Overload', true);
    };

    const canMove = status.servoOn && status.homed && !status.faultActive && status.state === 'READY';
    const canJog = canMove;

    return (
        <div className="axis-control animate-fade">
            {toast && <Toast msg={toast.msg} ok={toast.ok} />}

            {/* Page header */}
            <div className="section-header">
                <div>
                    <div className="section-title">Axis Control Panel</div>
                    <div className="section-sub">S7-1200 Gateway | MP2300S | {user?.role}</div>
                </div>
                <div className="flex gap-2 items-center">
                    <span className={`badge badge-${status.state.toLowerCase().replace('_', '-')}`}>
                        <span className={`led ${status.state === 'READY' ? 'led-green' : status.state === 'FAULT' ? 'led-red' : status.state === 'MOVING' || status.state === 'JOGGING' ? 'led-cyan' : 'led-amber'}`} />
                        {status.state}
                    </span>
                </div>
            </div>

            {/* Fault banner */}
            {status.faultActive && (
                <div className="ac-fault-banner">
                    <AlertTriangle size={16} />
                    <span>FAULT ACTIVE: {status.alarmCode} — Motion blocked. Reset alarms to resume.</span>
                    <button className="btn btn-danger btn-sm" onClick={() => setConfirmReset(true)}>Reset Alarms</button>
                </div>
            )}

            {/* Not homed warning */}
            {status.servoOn && !status.homed && !status.faultActive && (
                <div className="ac-warn-banner">
                    <Info size={15} />
                    <span>Axis not homed. Perform homing before executing motion commands.</span>
                </div>
            )}

            {/* Getting started banner */}
            {!status.servoOn && !status.faultActive && (
                <div className="ac-warn-banner" style={{ borderColor: 'var(--cyan)', background: 'rgba(0, 210, 255, 0.06)' }}>
                    <Info size={15} style={{ color: 'var(--cyan)' }} />
                    <span style={{ color: 'var(--cyan)' }}>Getting Started: Turn <strong>Servo ON</strong> → then use <strong>Jog Forward / Backward</strong> to test motor rotation.</span>
                </div>
            )}

            <div className="ac-grid">
                {/* ── SERVO & HOMING ── */}
                <div className="card">
                    <div className="card-header"><Power size={15} /><h3>Servo & Init</h3></div>
                    <div className="card-body ac-section">
                        <div className="ac-servo-row">
                            <div className="ac-servo-info">
                                <div className="ac-servo-label">Servo Drive</div>
                                <div className={`ac-servo-state ${status.servoOn ? 'on' : 'off'}`}>
                                    {status.servoOn ? 'ENABLED' : 'DISABLED'}
                                </div>
                            </div>
                            <button
                                className={`btn btn-lg ${status.servoOn ? 'btn-warning' : 'btn-success'}`}
                                onClick={handleServoToggle}
                                disabled={status.state === 'MOVING' || status.state === 'JOGGING'}
                            >
                                <Power size={16} />
                                {status.servoOn ? 'Servo OFF' : 'Servo ON'}
                            </button>
                        </div>

                        <hr className="divider" />

                        <div className="ac-home-row">
                            <div>
                                <div className="ac-servo-label">Homing Status</div>
                                <div className={status.homed ? 'text-green' : 'text-amber'} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600 }}>
                                    {status.homed ? '✓ HOMED' : '⚠ NOT HOMED'}
                                </div>
                                <div className="text-muted" style={{ fontSize: '0.7rem', marginTop: 2 }}>
                                    {status.homed ? `Origin set at 0.000mm` : 'Machine must be homed before motion'}
                                </div>
                            </div>
                            <button
                                className="btn btn-outline"
                                onClick={handleHome}
                                disabled={!status.servoOn || status.faultActive || (status.state !== 'READY' && status.state !== 'SERVO_OFF')}
                            >
                                <Home size={15} />
                                Start Homing
                            </button>
                        </div>

                        {status.state === 'HOMING' && (() => {
                            const startPos = homingStartPosRef.current ?? status.actualPosition;
                            const progress = startPos > 0
                                ? Math.min(100, Math.round(((startPos - status.actualPosition) / startPos) * 100))
                                : 90;
                            return (
                                <div className="ac-homing-progress">
                                    <RefreshCw size={14} className="animate-spin text-amber" />
                                    <span className="text-amber">Homing in progress... {progress}%</span>
                                    <div className="progress-track mt-2" style={{ flex: 1 }}>
                                        <div className="progress-bar progress-amber" style={{ width: `${progress}%`, transition: 'width 0.25s linear' }} />
                                    </div>
                                </div>
                            );
                        })()}
                    </div>
                </div>

                {/* ── ABSOLUTE MOVE ── */}
                <div className="card">
                    <div className="card-header"><ArrowRight size={15} /><h3>Absolute Position Move</h3></div>
                    <div className="card-body ac-section">
                        <div className="ac-kv-row">
                            <div className="ac-kv"><span>Current</span><span className="mono text-cyan">{status.actualPosition.toFixed(3)} mm</span></div>
                            <div className="ac-kv"><span>Target</span><span className="mono text-cyan">{status.targetPosition.toFixed(3)} mm</span></div>
                            <div className="ac-kv"><span>Limits</span><span className="mono text-muted">{status.softLimitMin} – {status.softLimitMax} mm</span></div>
                        </div>
                        <hr className="divider" />
                        <div className="input-group">
                            <label>Target Position (mm)</label>
                            <div className="input-row">
                                <input
                                    className="input"
                                    type="number"
                                    placeholder={`0 – ${status.softLimitMax}`}
                                    value={absTarget}
                                    onChange={e => setAbsTarget(e.target.value)}
                                    min={status.softLimitMin}
                                    max={status.softLimitMax}
                                    step="0.1"
                                />
                                <button className="btn btn-primary" onClick={handleAbsMove} disabled={!canMove}>
                                    <ArrowRight size={14} />
                                    Execute
                                </button>
                            </div>
                        </div>
                        <div className="ac-axis-vis">
                            <div className="ac-axis-label-row">
                                <span className="mono text-muted" style={{ fontSize: '0.68rem' }}>{status.softLimitMin}</span>
                                <span className="mono text-muted" style={{ fontSize: '0.68rem' }}>{status.softLimitMax}</span>
                            </div>
                            <div className="axis-track">
                                <div className="axis-cursor"
                                    style={{ left: `calc(${(status.actualPosition / Math.max(status.softLimitMax, 1)) * 100}% - 7px)` }} />
                                {absTarget && !isNaN(parseFloat(absTarget)) && (
                                    <div className="ac-target-marker"
                                        style={{ left: `${Math.max(0, Math.min(100, parseFloat(absTarget) / Math.max(status.softLimitMax, 1) * 100))}%` }} />
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── RELATIVE MOVE ── */}
                <div className="card">
                    <div className="card-header"><RefreshCw size={15} /><h3>Relative Move</h3></div>
                    <div className="card-body ac-section">
                        <div className="ac-kv-row">
                            <div className="ac-kv"><span>Current</span><span className="mono text-cyan">{status.actualPosition.toFixed(3)} mm</span></div>
                            <div className="ac-kv"><span>Would move to</span>
                                <span className="mono text-cyan">
                                    {relDelta && !isNaN(parseFloat(relDelta))
                                        ? (status.actualPosition + parseFloat(relDelta)).toFixed(3)
                                        : '—'} mm
                                </span>
                            </div>
                        </div>
                        <hr className="divider" />
                        <div className="input-group">
                            <label>Delta Distance (mm) — negative = reverse</label>
                            <div className="input-row">
                                <input
                                    className="input"
                                    type="number"
                                    placeholder="e.g. +50 or -25"
                                    value={relDelta}
                                    onChange={e => setRelDelta(e.target.value)}
                                    step="0.1"
                                />
                                <button className="btn btn-primary" onClick={handleRelMove} disabled={!canMove}>
                                    Execute
                                </button>
                            </div>
                        </div>
                        <div className="ac-quick-deltas">
                            <span className="text-muted" style={{ fontSize: '0.68rem' }}>Quick:</span>
                            {['-100', '-50', '-10', '+10', '+50', '+100'].map(v => (
                                <button key={v} className="btn btn-ghost btn-sm" onClick={() => setRelDelta(v)}>{v}</button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ── JOG CONTROL ── */}
                <div className="card">
                    <div className="card-header"><ChevronLeft size={15} /><h3>Jog Control</h3></div>
                    <div className="card-body ac-section">
                        <div className="ac-jog-info">
                            <span>Jog Velocity:</span>
                            <span className="mono text-cyan">{JOG_VELOCITY} mm/s</span>
                            <span className="text-muted" style={{ fontSize: '0.68rem' }}>Hold button to jog • Release to stop</span>
                        </div>
                        <div className="ac-jog-btns">
                            <button
                                className={`jog-btn ${status.state === 'JOGGING' && (status.actualVelocity < 0) ? 'active' : ''}`}
                                disabled={!canJog && status.state !== 'JOGGING'}
                                onMouseDown={() => handleJogStart('REV')}
                                onMouseUp={handleJogStop}
                                onMouseLeave={handleJogStop}
                                onTouchStart={(e) => { e.preventDefault(); handleJogStart('REV'); }}
                                onTouchEnd={handleJogStop}
                            >
                                <ChevronLeft size={24} />
                                JOG REV
                            </button>
                            <div className="ac-jog-center">
                                <div className="ac-jog-vel mono">
                                    {status.actualVelocity.toFixed(1)} mm/s
                                </div>
                                <div className={`badge ${status.state === 'JOGGING' ? 'badge-moving' : 'badge-servo-off'}`} style={{ fontSize: '0.65rem' }}>
                                    {status.state === 'JOGGING' ? 'JOGGING' : 'IDLE'}
                                </div>
                            </div>
                            <button
                                className={`jog-btn ${status.state === 'JOGGING' && status.actualVelocity > 0 ? 'active' : ''}`}
                                disabled={!canJog && status.state !== 'JOGGING'}
                                onMouseDown={() => handleJogStart('FWD')}
                                onMouseUp={handleJogStop}
                                onMouseLeave={handleJogStop}
                                onTouchStart={(e) => { e.preventDefault(); handleJogStart('FWD'); }}
                                onTouchEnd={handleJogStop}
                            >
                                <ChevronRight size={24} />
                                JOG FWD
                            </button>
                        </div>
                    </div>
                </div>

                {/* ── EMERGENCY STOP ── */}
                <div className="card ac-stop-card">
                    <div className="card-header"><Square size={15} /><h3>Emergency Stop</h3></div>
                    <div className="card-body ac-section">
                        <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: 14 }}>
                            Immediate stop command. Aborts all motion instantly. Always available regardless of system state.
                        </p>
                        <button
                            className="btn btn-danger btn-block btn-lg ac-stop-btn"
                            onClick={() => status.state === 'MOVING' || status.state === 'JOGGING' ? setConfirmStop(true) : handleStop()}
                        >
                            <Square size={20} fill="white" />
                            IMMEDIATE STOP
                        </button>
                    </div>
                </div>

                {/* ── ALARM RESET ── */}
                <div className="card">
                    <div className="card-header"><AlertTriangle size={15} /><h3>Alarm Management</h3></div>
                    <div className="card-body ac-section">
                        <div className="ac-kv-row">
                            <div className="ac-kv"><span>Active Faults</span>
                                <span className={`mono ${status.faultActive ? 'text-red' : 'text-green'}`}>
                                    {status.faultActive ? status.alarmCode : 'NONE'}
                                </span>
                            </div>
                        </div>
                        <div className="flex gap-2 mt-3">
                            <button
                                className="btn btn-warning"
                                onClick={() => setConfirmReset(true)}
                                disabled={!status.faultActive}
                            >
                                <RefreshCw size={14} />
                                Reset Alarms
                            </button>
                            {isAdmin && (
                                <button className="btn btn-ghost btn-sm" onClick={handleInjectFault}>
                                    ⚡ Inject Fault (Demo)
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── SOFT LIMITS (Engineer+) ── */}
                {isEngineerPlus && (
                    <div className="card ac-full-row">
                        <div className="card-header"><Settings size={15} /><h3>Soft Travel Limits — Engineer Access</h3></div>
                        <div className="card-body">
                            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                                <div className="input-group">
                                    <label>Min Limit (mm)</label>
                                    <input className="input" type="number" value={softMinInput} onChange={e => setSoftMinInput(e.target.value)} step="1" style={{ width: 140 }} />
                                </div>
                                <div className="input-group">
                                    <label>Max Limit (mm)</label>
                                    <input className="input" type="number" value={softMaxInput} onChange={e => setSoftMaxInput(e.target.value)} step="1" style={{ width: 140 }} />
                                </div>
                                <button className="btn btn-outline" onClick={handleSoftLimits}>
                                    Apply Limits
                                </button>
                                <div className="text-muted" style={{ fontSize: '0.72rem' }}>
                                    Current: [{status.softLimitMin}, {status.softLimitMax}] mm
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Confirm dialogs */}
            {confirmStop && (
                <ConfirmDialog
                    title="Immediate Stop"
                    message={`Axis is currently ${status.state}. Confirm immediate stop command?`}
                    danger
                    onConfirm={handleStop}
                    onCancel={() => setConfirmStop(false)}
                />
            )}
            {confirmReset && (
                <ConfirmDialog
                    title="Reset Alarms"
                    message={`Reset active alarm ${status.alarmCode}? Ensure the fault condition has been physically resolved before resetting.`}
                    danger
                    onConfirm={handleAlarmReset}
                    onCancel={() => setConfirmReset(false)}
                />
            )}
        </div>
    );
}
