// S7-1200 PLC + SGD7S Servo Drive Motion Simulator
// Calibrated for: SGD7S-120A10A Servo Drive + SGM7G-09AFA6C 900W Motor
// Controlled via: Siemens S7-1200 PLC (Modbus TCP)
// Encoder: 24-bit absolute, 16777216 counts/rev
// Travel: 0 to 1000mm soft limits

export type AxisState =
    | 'INIT'
    | 'SERVO_OFF'
    | 'HOMING'
    | 'READY'
    | 'MOVING'
    | 'JOGGING'
    | 'FAULT';

export type AlarmSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

export interface AlarmEntry {
    id: string;
    code: string;
    description: string;
    remedy: string;
    severity: AlarmSeverity;
    timestamp: Date;
    acknowledged: boolean;
}

export interface AuditEntry {
    id: string;
    timestamp: Date;
    user: string;
    command: string;
    parameters: string;
    result: 'SUCCESS' | 'REJECTED' | 'FAULT';
}

export interface AxisStatus {
    state: AxisState;
    actualPosition: number;     // mm
    actualVelocity: number;     // mm/s
    targetPosition: number;     // mm
    servoOn: boolean;
    homed: boolean;
    stoActive: boolean;         // Safe Torque Off
    faultActive: boolean;
    alarmCode: string | null;
    softLimitMin: number;       // mm
    softLimitMax: number;       // mm
    torquePercent: number;      // %
    encoderCounts: number;
    commOk: boolean;
    driveTemp: number;          // °C simulated
    busVoltage: number;         // V DC bus
}

const ENCODER_COUNTS_PER_MM = 16777216 / 100; // 24-bit encoder, 100mm per rev
export const MAX_VELOCITY = 500;     // mm/s max
const MAX_ACCEL = 800;        // mm/s²
export const JOG_VELOCITY = 50;      // mm/s for jog
const HOME_VELOCITY = 20;     // mm/s for homing

const FAULT_CODES: Record<string, { description: string; remedy: string; severity: AlarmSeverity }> = {
    'A.020': { description: 'Parameter Checksum Error', remedy: 'Reinitialize parameters via SigmaWin+', severity: 'CRITICAL' },
    'A.040': { description: 'Main Circuit Voltage Error (Under Voltage)', remedy: 'Check 200V AC power supply to drive', severity: 'CRITICAL' },
    'A.710': { description: 'Overload (Instantaneous Max Load)', remedy: 'Reduce load or increase deceleration time', severity: 'CRITICAL' },
    'A.720': { description: 'Overload (Continuous Max Load)', remedy: 'Check mechanical load and duty cycle', severity: 'CRITICAL' },
    'A.C10': { description: 'Runaway Detected', remedy: 'Check encoder wiring and motor connection', severity: 'CRITICAL' },
    'A.510': { description: 'Overspeed', remedy: 'Reduce velocity command, check speed loop gain', severity: 'CRITICAL' },
    'A.d00': { description: 'Position Error Overflow', remedy: 'Check for mechanical jam or excessive load', severity: 'CRITICAL' },
    'A.810': { description: 'Encoder Backup Error (Battery)', remedy: 'Replace encoder backup battery', severity: 'WARNING' },
    'A.900': { description: 'Overflow Alarm', remedy: 'Check position command range', severity: 'WARNING' },
    'SW.001': { description: 'Positive Software Limit Exceeded', remedy: 'Move axis in negative direction', severity: 'WARNING' },
    'SW.002': { description: 'Negative Software Limit Exceeded', remedy: 'Move axis in positive direction', severity: 'WARNING' },
};

function generateId(): string {
    return Math.random().toString(36).substr(2, 9);
}

export class S71200Simulator {
    private status: AxisStatus;
    private alarms: AlarmEntry[] = [];
    private auditLog: AuditEntry[] = [];
    private activeJog: 'FWD' | 'REV' | null = null;
    private moveTarget: number = 0;
    private lastUpdateTime: number = Date.now();
    private homingTimer: ReturnType<typeof setTimeout> | null = null;
    private currentUser: string = 'system';
    private onUpdate: (() => void) | null = null;
    private intervalId: ReturnType<typeof setInterval> | null = null;


    constructor() {
        this.status = {
            state: 'INIT',
            actualPosition: 0,
            actualVelocity: 0,
            targetPosition: 0,
            servoOn: false,
            homed: false,
            stoActive: false,
            faultActive: false,
            alarmCode: null,
            softLimitMin: 0,
            softLimitMax: 1000,
            torquePercent: 0,
            encoderCounts: 0,
            commOk: true,
            driveTemp: 28,
            busVoltage: 310,
        };

        // Transition INIT → SERVO_OFF after boot
        setTimeout(() => {
            this.status.state = 'SERVO_OFF';
            this.onUpdate?.();
        }, 1500);
    }

    setUser(user: string) {
        this.currentUser = user;
    }

    setUpdateCallback(cb: () => void) {
        this.onUpdate = cb;
    }

    startLoop() {
        this.intervalId = setInterval(() => this.tick(), 250);
    }

    stopLoop() {
        if (this.intervalId) clearInterval(this.intervalId);
    }

    private tick() {
        const now = Date.now();
        const dt = (now - this.lastUpdateTime) / 1000; // seconds
        this.lastUpdateTime = now;

        // Drive temp simulation
        if (this.status.servoOn) {
            this.status.driveTemp = Math.min(65, this.status.driveTemp + 0.01);
        } else {
            this.status.driveTemp = Math.max(28, this.status.driveTemp - 0.005);
        }

        // Bus voltage slight variation
        this.status.busVoltage = 310 + (Math.random() - 0.5) * 4;

        if (this.status.state === 'MOVING') {
            this.simulateMove(dt);
        } else if (this.status.state === 'JOGGING') {
            this.simulateJog(dt);
        } else if (this.status.state === 'HOMING') {
            // Homing is timer-based
        } else {
            this.status.actualVelocity = 0;
            this.status.torquePercent = 0;
        }

        this.status.encoderCounts = Math.round(this.status.actualPosition * ENCODER_COUNTS_PER_MM);
        this.onUpdate?.();
    }

    private simulateMove(dt: number) {
        const error = this.moveTarget - this.status.actualPosition;
        if (Math.abs(error) < 0.01) {
            this.status.actualPosition = this.moveTarget;
            this.status.actualVelocity = 0;
            this.status.torquePercent = 0;
            this.status.state = 'READY';
            this.onUpdate?.();
            return;
        }
        const dir = error > 0 ? 1 : -1;
        const distLeft = Math.abs(error);
        const brakeDist = (this.status.actualVelocity ** 2) / (2 * MAX_ACCEL);
        let velocity = this.status.actualVelocity;

        if (brakeDist >= distLeft) {
            velocity -= MAX_ACCEL * dt;
            if (velocity < 5) velocity = 5;
        } else {
            velocity += MAX_ACCEL * dt;
            if (velocity > MAX_VELOCITY) velocity = MAX_VELOCITY;
        }

        const step = dir * velocity * dt;
        this.status.actualPosition += step;
        this.status.actualVelocity = velocity;
        this.status.torquePercent = Math.min(80, (velocity / MAX_VELOCITY) * 60 + Math.random() * 5);

        // Check soft limits
        if (this.status.actualPosition >= this.status.softLimitMax) {
            this.status.actualPosition = this.status.softLimitMax;
            this.triggerAlarm('SW.001', 'Positive soft limit reached');
        }
        if (this.status.actualPosition <= this.status.softLimitMin) {
            this.status.actualPosition = this.status.softLimitMin;
            this.triggerAlarm('SW.002', 'Negative soft limit reached');
        }
    }

    private simulateJog(dt: number) {
        if (!this.activeJog) {
            this.status.actualVelocity = 0;
            this.status.torquePercent = 0;
            this.status.state = 'READY';
            return;
        }
        const dir = this.activeJog === 'FWD' ? 1 : -1;
        this.status.actualVelocity = dir * JOG_VELOCITY;
        const newPos = this.status.actualPosition + dir * JOG_VELOCITY * dt;

        if (newPos >= this.status.softLimitMax) {
            this.status.actualPosition = this.status.softLimitMax;
            this.status.actualVelocity = 0;
            this.activeJog = null;
            this.status.state = 'READY';
            this.triggerAlarm('SW.001', 'Positive soft limit reached during jog');
            return;
        }
        if (newPos <= this.status.softLimitMin) {
            this.status.actualPosition = this.status.softLimitMin;
            this.status.actualVelocity = 0;
            this.activeJog = null;
            this.status.state = 'READY';
            this.triggerAlarm('SW.002', 'Negative soft limit reached during jog');
            return;
        }
        this.status.actualPosition = newPos;
        this.status.torquePercent = 25 + Math.random() * 5;
    }

    private triggerAlarm(code: string, extraDesc?: string) {
        const def = FAULT_CODES[code] ?? {
            description: extraDesc ?? 'Unknown Alarm',
            remedy: 'Check system and contact support',
            severity: 'WARNING' as AlarmSeverity,
        };
        const alarm: AlarmEntry = {
            id: generateId(),
            code,
            description: def.description,
            remedy: def.remedy,
            severity: def.severity,
            timestamp: new Date(),
            acknowledged: false,
        };
        this.alarms = [alarm, ...this.alarms];
        if (def.severity === 'CRITICAL') {
            this.status.faultActive = true;
            this.status.alarmCode = code;
            this.status.actualVelocity = 0;
            this.status.torquePercent = 0;
            this.status.state = 'FAULT';
            this.activeJog = null;
        }
        this.onUpdate?.();
    }

    // ─── PUBLIC COMMANDS ───────────────────────────────────────────────

    servoOn(): string {
        if (this.status.faultActive) return this.reject('ServoOn', 'FAULT active — clear alarms first');
        if (this.status.stoActive) return this.reject('ServoOn', 'STO active — check safety circuit');
        if (this.status.state !== 'SERVO_OFF') return this.reject('ServoOn', `Cannot enable servo in state ${this.status.state}`);
        this.status.servoOn = true;
        this.status.state = 'READY';
        // If not homed, force to a homing-required sub-state visible via homed flag
        return this.audit('ServoOn', '', 'SUCCESS');
    }

    servoOff(): string {
        if (this.status.state === 'MOVING' || this.status.state === 'JOGGING') {
            this.immediateStop();
        }
        this.status.servoOn = false;
        this.status.state = 'SERVO_OFF';
        this.status.actualVelocity = 0;
        this.status.torquePercent = 0;
        return this.audit('ServoOff', '', 'SUCCESS');
    }

    startHoming(): string {
        if (!this.status.servoOn) return this.reject('Homing', 'Servo must be ON to home');
        if (this.status.faultActive) return this.reject('Homing', 'Clear faults before homing');
        if (this.status.state !== 'READY' && this.status.state !== 'SERVO_OFF') {
            return this.reject('Homing', `Cannot home in state ${this.status.state}`);
        }
        this.status.state = 'HOMING';
        this.status.actualVelocity = HOME_VELOCITY;

        // Simulate homing: move to 0 over ~3s, then set homed
        const startPos = this.status.actualPosition;
        const homingDuration = 3000 + Math.random() * 1000;
        const steps = 20;
        const interval = homingDuration / steps;
        let step = 0;
        const homingInterval = setInterval(() => {
            step++;
            this.status.actualPosition = startPos * (1 - step / steps);
            this.status.actualVelocity = HOME_VELOCITY * (1 - step / steps);
            if (step >= steps) {
                clearInterval(homingInterval);
                this.status.actualPosition = 0;
                this.status.actualVelocity = 0;
                this.status.homed = true;
                this.status.state = 'READY';
                this.audit('Homing', 'completed', 'SUCCESS');
                this.onUpdate?.();
            }
        }, interval);

        return this.audit('Homing', 'started', 'SUCCESS');
    }

    absoluteMove(targetMm: number): string {
        if (!this.canMove()) return this.reject('AbsMove', this.moveBlockReason());
        const clamped = Math.max(this.status.softLimitMin, Math.min(this.status.softLimitMax, targetMm));
        if (clamped !== targetMm) {
            return this.reject('AbsMove', `Target ${targetMm}mm out of soft limits [${this.status.softLimitMin}, ${this.status.softLimitMax}]`);
        }
        this.moveTarget = clamped;
        this.status.targetPosition = clamped;
        this.status.state = 'MOVING';
        return this.audit('AbsMove', `target=${targetMm}mm`, 'SUCCESS');
    }

    relativeMove(deltaMm: number): string {
        if (!this.canMove()) return this.reject('RelMove', this.moveBlockReason());
        const target = this.status.actualPosition + deltaMm;
        const clamped = Math.max(this.status.softLimitMin, Math.min(this.status.softLimitMax, target));
        if (clamped !== target) {
            return this.reject('RelMove', `Result ${target}mm would exceed soft limits`);
        }
        this.moveTarget = clamped;
        this.status.targetPosition = clamped;
        this.status.state = 'MOVING';
        return this.audit('RelMove', `delta=${deltaMm}mm → target=${clamped}mm`, 'SUCCESS');
    }

    jogStart(dir: 'FWD' | 'REV'): string {
        if (!this.canMove()) return this.reject('Jog' + dir, this.moveBlockReason());
        this.activeJog = dir;
        this.status.state = 'JOGGING';
        return this.audit('Jog' + dir, 'started', 'SUCCESS');
    }

    jogStop(): string {
        if (this.status.state !== 'JOGGING') return 'OK';
        this.activeJog = null;
        this.status.state = 'READY';
        this.status.actualVelocity = 0;
        return this.audit('JogStop', '', 'SUCCESS');
    }

    immediateStop(): string {
        const prevState = this.status.state;
        this.activeJog = null;
        if (this.homingTimer) clearTimeout(this.homingTimer);
        this.status.state = this.status.servoOn ? 'READY' : 'SERVO_OFF';
        this.status.actualVelocity = 0;
        this.status.torquePercent = 0;
        this.moveTarget = this.status.actualPosition;
        this.status.targetPosition = this.status.actualPosition;
        return this.audit('ImmediateStop', `from ${prevState}`, 'SUCCESS');
    }

    resetAlarms(): string {
        if (this.status.state === 'MOVING' || this.status.state === 'JOGGING') {
            return this.reject('AlarmReset', 'Stop axis before resetting alarms');
        }
        this.alarms = this.alarms.map(a => ({ ...a, acknowledged: true }));
        this.status.faultActive = false;
        this.status.alarmCode = null;
        this.status.state = this.status.servoOn ? 'READY' : 'SERVO_OFF';
        return this.audit('AlarmReset', '', 'SUCCESS');
    }

    injectFault(code: string = 'A.710'): string {
        this.triggerAlarm(code);
        return this.audit('InjectFault', `code=${code}`, 'SUCCESS');
    }

    setSoftLimits(minMm: number, maxMm: number): string {
        this.status.softLimitMin = minMm;
        this.status.softLimitMax = maxMm;
        return this.audit('SetSoftLimits', `min=${minMm}mm, max=${maxMm}mm`, 'SUCCESS');
    }

    // ─── HELPERS ───────────────────────────────────────────────────────

    private canMove(): boolean {
        return (
            this.status.servoOn &&
            this.status.homed &&
            !this.status.faultActive &&
            !this.status.stoActive &&
            (this.status.state === 'READY')
        );
    }

    private moveBlockReason(): string {
        if (!this.status.servoOn) return 'Servo is OFF';
        if (!this.status.homed) return 'Axis not homed — perform homing first';
        if (this.status.faultActive) return 'Fault active — reset alarms first';
        if (this.status.stoActive) return 'STO active — check safety circuit';
        return `Invalid state: ${this.status.state}`;
    }

    private reject(command: string, reason: string): string {
        this.audit(command, reason, 'REJECTED');
        return `REJECTED: ${reason}`;
    }

    private audit(command: string, parameters: string, result: 'SUCCESS' | 'REJECTED' | 'FAULT'): string {
        const entry: AuditEntry = {
            id: generateId(),
            timestamp: new Date(),
            user: this.currentUser,
            command,
            parameters,
            result,
        };
        this.auditLog = [entry, ...this.auditLog.slice(0, 499)]; // keep max 500
        return result;
    }

    getStatus(): AxisStatus {
        return { ...this.status };
    }

    getAlarms(): AlarmEntry[] {
        return [...this.alarms];
    }

    getAuditLog(): AuditEntry[] {
        return [...this.auditLog];
    }

    getFaultCodes() {
        return FAULT_CODES;
    }
}

export const simulator = new S71200Simulator();
