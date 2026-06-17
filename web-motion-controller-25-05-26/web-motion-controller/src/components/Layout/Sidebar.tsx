import { NavLink } from 'react-router-dom';
import { useMotionStore } from '../../store/motionStore';
import {
    Activity, Cpu, BarChart2, AlertTriangle, ClipboardList, Zap
} from 'lucide-react';
import './Sidebar.css';

const NAV = [
    { to: '/dashboard', icon: Activity, label: 'Dashboard' },
    { to: '/axis-control', icon: Cpu, label: 'Axis Control' },
    { to: '/monitoring', icon: BarChart2, label: 'Monitoring' },
    { to: '/alarms', icon: AlertTriangle, label: 'Alarms' },
    { to: '/audit-log', icon: ClipboardList, label: 'Audit Log' },
];

export default function Sidebar() {
    const { status, alarms } = useMotionStore();
    const activeAlarmCount = alarms.filter(a => !a.acknowledged).length;

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-brand">
                <div className="sidebar-logo">
                    <Zap size={20} color="var(--cyan)" />
                </div>
                <div>
                    <div className="sidebar-brand-name">MotionOS</div>
                    <div className="sidebar-brand-sub">S7-1200 ↔ MP2300S</div>
                </div>
            </div>

            {/* Axis quick status */}
            <div className="sidebar-axis-status">
                <div className="sidebar-axis-label">AXIS-1 STATUS</div>
                <div className={`sidebar-state badge badge-${status.state.toLowerCase().replace('_', '-')}`}>
                    <span className={`led ${status.state === 'READY' ? 'led-green' :
                        status.state === 'FAULT' ? 'led-red' :
                            status.state === 'MOVING' || status.state === 'JOGGING' ? 'led-cyan' :
                                status.state === 'HOMING' ? 'led-amber' : 'led-gray'
                        }`} />
                    {status.state}
                </div>
                <div className="sidebar-pos">
                    <span className="sidebar-pos-val mono">{status.actualPosition.toFixed(3)}</span>
                    <span className="sidebar-pos-unit">mm</span>
                </div>
            </div>

            {/* Nav */}
            <nav className="sidebar-nav">
                {NAV.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                    >
                        <Icon size={17} />
                        <span>{label}</span>
                        {label === 'Alarms' && activeAlarmCount > 0 && (
                            <span className="sidebar-alarm-badge">{activeAlarmCount}</span>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div className="sidebar-footer">
                <div className="sidebar-footer-line">
                    <span className={`led ${status.commOk ? 'led-green' : 'led-red'}`} />
                    <span>MECHATROLINK-II</span>
                </div>
                <div className="sidebar-footer-line">
                    <span className={`led ${status.commOk ? 'led-cyan' : 'led-red'}`} />
                    <span>Modbus TCP</span>
                </div>
                <div className="sidebar-footer-line">
                    <span className={`led ${status.stoActive ? 'led-red' : 'led-gray'}`} />
                    <span>STO {status.stoActive ? 'ACTIVE' : 'OK'}</span>
                </div>
            </div>
        </aside>
    );
}
