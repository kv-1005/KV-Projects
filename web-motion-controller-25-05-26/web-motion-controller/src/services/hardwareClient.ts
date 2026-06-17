/**
 * Hardware WebSocket client — connects to the Node.js backend (server.js)
 * which in turn talks Modbus TCP to the Siemens S7-1200 PLC.
 *
 * Drop-in replacement for simulator when VITE_USE_REAL_HARDWARE=true
 */

import type { AxisStatus, AlarmEntry, AuditEntry } from '../simulation/S71200Simulator';

const WS_URL = 'ws://localhost:3001';
const RECONNECT_MS = 2000;

type StatusCallback = (status: AxisStatus) => void;
type AckCallback = (command: string, result: string) => void;

export class HardwareClient {
    private ws: WebSocket | null = null;
    private onStatusUpdate: StatusCallback | null = null;
    private onCommandAck: AckCallback | null = null;
    private alarms: AlarmEntry[] = [];
    private auditLog: AuditEntry[] = [];
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    private defaultStatus(): AxisStatus {
        return {
            state: 'SERVO_OFF', actualPosition: 0, actualVelocity: 0,
            targetPosition: 0, servoOn: false, homed: false,
            stoActive: false, faultActive: false, alarmCode: null,
            softLimitMin: 0, softLimitMax: 1000, torquePercent: 0,
            encoderCounts: 0, commOk: false, driveTemp: 0, busVoltage: 0,
        };
    }

    private lastStatus: AxisStatus = this.defaultStatus();

    connect() {
        try {
            this.ws = new WebSocket(WS_URL);
        } catch {
            this.scheduleReconnect();
            return;
        }

        this.ws.onopen = () => {
            console.log('[HardwareClient] Connected to backend');
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'STATUS') {
                    this.lastStatus = msg.payload as AxisStatus;
                    // Generate alarm entry if fault is active
                    if (this.lastStatus.faultActive && this.lastStatus.alarmCode) {
                        const exists = this.alarms.some(a => a.code === this.lastStatus.alarmCode && !a.acknowledged);
                        if (!exists) {
                            this.alarms = [{
                                id: Date.now().toString(),
                                code: this.lastStatus.alarmCode,
                                description: `Hardware alarm: ${this.lastStatus.alarmCode}`,
                                remedy: 'Check drive display and resolve fault, then reset alarms.',
                                severity: 'CRITICAL',
                                timestamp: new Date(),
                                acknowledged: false,
                            }, ...this.alarms];
                        }
                    }
                    this.onStatusUpdate?.(this.lastStatus);
                } else if (msg.type === 'CMD_ACK') {
                    const logEntry: AuditEntry = {
                        id: Date.now().toString(),
                        timestamp: new Date(),
                        user: 'operator',
                        command: msg.command,
                        parameters: '',
                        result: msg.result === 'SUCCESS' ? 'SUCCESS' : msg.result.startsWith('REJECTED') ? 'REJECTED' : 'FAULT',
                    };
                    this.auditLog = [logEntry, ...this.auditLog.slice(0, 499)];
                    this.onCommandAck?.(msg.command, msg.result);
                }
            } catch { /* ignore bad messages */ }
        };

        this.ws.onclose = () => {
            console.warn('[HardwareClient] Disconnected — reconnecting...');
            this.lastStatus = { ...this.defaultStatus(), commOk: false };
            this.onStatusUpdate?.(this.lastStatus);
            this.scheduleReconnect();
        };

        this.ws.onerror = () => {
            this.ws?.close();
        };
    }

    private scheduleReconnect() {
        if (this.reconnectTimer) return;
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, RECONNECT_MS);
    }

    private send(command: string, params: Record<string, unknown> = {}) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...params }));
            return 'SUCCESS';
        }
        return 'REJECTED: Not connected to backend';
    }

    setUpdateCallback(cb: StatusCallback) { this.onStatusUpdate = cb; }
    setAckCallback(cb: AckCallback) { this.onCommandAck = cb; }

    // Motion commands — mirror the S71200Simulator public API
    servoOn() { return this.send('servoOn'); }
    servoOff() { return this.send('servoOff'); }
    startHoming() { return this.send('startHoming'); }
    absoluteMove(targetMm: number) { return this.send('absoluteMove', { target: targetMm, velocity: 500 }); }
    relativeMove(deltaMm: number) {
        const target = this.lastStatus.actualPosition + deltaMm;
        return this.send('absoluteMove', { target, velocity: 500 });
    }
    jogStart(dir: 'FWD' | 'REV') { return this.send('jogStart', { dir }); }
    jogStop() { return this.send('jogStop'); }
    immediateStop() { return this.send('immediateStop'); }
    resetAlarms() {
        this.alarms = this.alarms.map(a => ({ ...a, acknowledged: true }));
        return this.send('resetAlarms');
    }
    injectFault(_code?: string) { return 'REJECTED: Cannot inject faults into real hardware'; }
    setSoftLimits(_min: number, _max: number) { return 'REJECTED: Set soft limits via MPE720'; }

    getStatus(): AxisStatus { return { ...this.lastStatus }; }
    getAlarms(): AlarmEntry[] { return [...this.alarms]; }
    getAuditLog(): AuditEntry[] { return [...this.auditLog]; }
    setUser(_user: string) { /* handled by auth on controller */ }
    startLoop() { this.connect(); }
    stopLoop() { this.ws?.close(); }
}

export const hardwareClient = new HardwareClient();
