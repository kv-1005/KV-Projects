import { create } from 'zustand';
import type { AxisStatus, AlarmEntry, AuditEntry } from '../simulation/S71200Simulator';

// ─── Mode switch ──────────────────────────────────────────────────────────────
// To use REAL hardware:  add VITE_USE_REAL_HARDWARE=true to .env.local
// To use simulator:      remove that line (or set to false)
const USE_REAL_HARDWARE = import.meta.env.VITE_USE_REAL_HARDWARE === 'true';

// Dynamically pick the backend
let backend: {
    getStatus(): AxisStatus;
    getAlarms(): AlarmEntry[];
    getAuditLog(): AuditEntry[];
    setUpdateCallback(cb: () => void): void;
    setUser(user: string): void;
    startLoop(): void;
    servoOn(): string;
    servoOff(): string;
    startHoming(): string;
    absoluteMove(t: number): string;
    relativeMove(d: number): string;
    jogStart(dir: 'FWD' | 'REV'): string;
    jogStop(): string;
    immediateStop(): string;
    resetAlarms(): string;
    injectFault(code?: string): string;
    setSoftLimits(min: number, max: number): string;
};

if (USE_REAL_HARDWARE) {
    // Import real hardware client
    const { hardwareClient } = await import('../services/hardwareClient');
    backend = hardwareClient;
    console.log('%c[motionStore] 🔌 REAL HARDWARE MODE', 'color:lime;font-weight:bold');
} else {
    const { simulator } = await import('../simulation/S71200Simulator');
    backend = simulator;
    console.log('%c[motionStore] 🖥️  SIMULATOR MODE', 'color:cyan;font-weight:bold');
}

interface MotionState {
    status: AxisStatus;
    alarms: AlarmEntry[];
    auditLog: AuditEntry[];
    positionHistory: { time: number; position: number; velocity: number }[];
    usingRealHardware: boolean;

    servoOn: () => string;
    servoOff: () => string;
    startHoming: () => string;
    absoluteMove: (target: number) => string;
    relativeMove: (delta: number) => string;
    jogStart: (dir: 'FWD' | 'REV') => string;
    jogStop: () => string;
    immediateStop: () => string;
    resetAlarms: () => string;
    injectFault: (code?: string) => string;
    setSoftLimits: (min: number, max: number) => string;
    refresh: () => void;
}

export const useMotionStore = create<MotionState>((set, get) => {
    const refresh = () => {
        const status = backend.getStatus();
        const alarms = backend.getAlarms();
        const auditLog = backend.getAuditLog();
        const prev = get().positionHistory;
        const now = Date.now();
        const history = [...prev, { time: now, position: status.actualPosition, velocity: status.actualVelocity }].slice(-120);
        set({ status, alarms, auditLog, positionHistory: history });
    };

    backend.setUpdateCallback(refresh);
    backend.startLoop();

    return {
        status: backend.getStatus(),
        alarms: [],
        auditLog: [],
        positionHistory: [],
        usingRealHardware: USE_REAL_HARDWARE,
        refresh,

        servoOn: () => { const r = backend.servoOn(); refresh(); return r; },
        servoOff: () => { const r = backend.servoOff(); refresh(); return r; },
        startHoming: () => { const r = backend.startHoming(); refresh(); return r; },
        absoluteMove: (t) => { const r = backend.absoluteMove(t); refresh(); return r; },
        relativeMove: (d) => { const r = backend.relativeMove(d); refresh(); return r; },
        jogStart: (dir) => { const r = backend.jogStart(dir); refresh(); return r; },
        jogStop: () => { const r = backend.jogStop(); refresh(); return r; },
        immediateStop: () => { const r = backend.immediateStop(); refresh(); return r; },
        resetAlarms: () => { const r = backend.resetAlarms(); refresh(); return r; },
        injectFault: (c) => { const r = backend.injectFault(c); refresh(); return r; },
        setSoftLimits: (min, max) => { const r = backend.setSoftLimits(min, max); refresh(); return r; },
    };
});
