import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useMotionStore } from '../../store/motionStore';
import { LogOut, Wifi, WifiOff, Shield, Clock } from 'lucide-react';
import './Header.css';

export default function Header() {
    const navigate = useNavigate();
    const { user, logout, sessionStart } = useAuthStore();
    const { status } = useMotionStore();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const sessionDuration = sessionStart
        ? Math.floor((Date.now() - new Date(sessionStart).getTime()) / 60000)
        : 0;

    return (
        <header className="header">
            {/* System name */}
            <div className="header-system">
                <span className="header-sys-name">Industrial Motion Control Platform</span>
                <span className="header-sys-sub mono">S7-1200 Gateway · MP2300S · SGD7S</span>
            </div>

            <div className="header-spacer" />

            {/* Comm status */}
            <div className="header-comm">
                {status.commOk ? (
                    <div className="header-badge ok">
                        <Wifi size={13} />
                        <span>PLC ONLINE</span>
                    </div>
                ) : (
                    <div className="header-badge fail">
                        <WifiOff size={13} />
                        <span>PLC OFFLINE</span>
                    </div>
                )}
                <div className="header-badge neutral">
                    <Clock size={13} />
                    <span>{sessionDuration}m</span>
                </div>
            </div>

            {/* User */}
            {user && (
                <div className="header-user">
                    <div className="header-avatar">
                        <Shield size={14} />
                    </div>
                    <div className="header-user-info">
                        <span className="header-user-name">{user.name}</span>
                        <span className={`header-role role-${user.role.toLowerCase()}`}>{user.role}</span>
                    </div>
                    <button className="btn btn-ghost btn-icon" onClick={handleLogout} title="Logout">
                        <LogOut size={15} />
                    </button>
                </div>
            )}
        </header>
    );
}
