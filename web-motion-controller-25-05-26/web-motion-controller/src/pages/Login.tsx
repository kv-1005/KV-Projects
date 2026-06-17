import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Activity, Lock, User, ChevronRight, Shield } from 'lucide-react';
import './Login.css';

const DEMO_CREDS = [
    { username: 'operator', password: 'op123', role: 'OPERATOR', color: 'var(--green)' },
    { username: 'engineer', password: 'eng456', role: 'ENGINEER', color: 'var(--cyan)' },
    { username: 'admin', password: 'admin789', role: 'ADMIN', color: 'var(--purple)' },
];

export default function Login() {
    const navigate = useNavigate();
    const { login, loginError } = useAuthStore();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        await new Promise(r => setTimeout(r, 600)); // sim auth delay
        const ok = login(username, password);
        setLoading(false);
        if (ok) navigate('/dashboard');
    };

    const quickLogin = (u: string, p: string) => {
        setUsername(u);
        setPassword(p);
    };

    return (
        <div className="login-bg">
            {/* Animated grid */}
            <div className="login-grid" />
            {/* Glow orbs */}
            <div className="orb orb-1" />
            <div className="orb orb-2" />

            <div className="login-container">
                {/* Brand */}
                <div className="login-brand">
                    <div className="login-logo">
                        <Activity size={28} color="var(--cyan)" />
                    </div>
                    <div>
                        <h1 className="login-title">MotionOS</h1>
                        <p className="login-subtitle">S7-1200 ↔ MP2300S Gateway</p>
                    </div>
                </div>

                {/* System badge */}
                <div className="login-sys-badge">
                    <div className="led led-green" />
                    <span>S7-1200 Gateway | MP2300S | SGD7S</span>
                </div>

                {/* Form Card */}
                <div className="login-card">
                    <div className="login-card-header">
                        <Shield size={16} color="var(--cyan)" />
                        <span>Secure Login — TLS 1.3</span>
                    </div>

                    <form onSubmit={handleLogin} className="login-form">
                        <div className="input-group">
                            <label>Username</label>
                            <div className="input-icon-wrap">
                                <User size={15} className="input-icon" />
                                <input
                                    className="input"
                                    type="text"
                                    placeholder="Enter username"
                                    value={username}
                                    onChange={e => setUsername(e.target.value)}
                                    autoComplete="username"
                                    required
                                />
                            </div>
                        </div>
                        <div className="input-group">
                            <label>Password</label>
                            <div className="input-icon-wrap">
                                <Lock size={15} className="input-icon" />
                                <input
                                    className="input"
                                    type="password"
                                    placeholder="Enter password"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    autoComplete="current-password"
                                    required
                                />
                            </div>
                        </div>

                        {loginError && (
                            <div className="login-error">
                                <span>⚠</span> {loginError}
                            </div>
                        )}

                        <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={loading}>
                            {loading ? <span className="animate-spin">⟳</span> : <ChevronRight size={16} />}
                            {loading ? 'Authenticating...' : 'Login'}
                        </button>
                    </form>

                    {/* Quick access */}
                    <div className="quick-login">
                        <p className="quick-login-label">Demo Quick Access</p>
                        <div className="quick-login-btns">
                            {DEMO_CREDS.map(c => (
                                <button
                                    key={c.username}
                                    className="quick-btn"
                                    style={{ borderColor: c.color + '44', color: c.color }}
                                    onClick={() => quickLogin(c.username, c.password)}
                                    type="button"
                                >
                                    {c.role}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <p className="login-footer">
                    Siemens S7-1200 | SGD7S-120A10A + SGM7G-09AFA6C | Modbus TCP
                </p>
            </div>
        </div>
    );
}
