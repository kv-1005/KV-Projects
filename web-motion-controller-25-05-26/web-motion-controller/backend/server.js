/**
 * S7-1200 Modbus TCP ↔ WebSocket Bridge  ── CLIENT MODE (Port 502)
 *
 * PORT 502 IS NOW OPEN ON THE S7-1200! 🎉
 * S7-1200 MB_SERVER is live.
 * This server connects TO the S7-1200 PLC as a Modbus TCP master.
 */

'use strict';

const ModbusRTU = require('modbus-serial');
const { WebSocketServer } = require('ws');
const { STATUS, CMD, STATUS_BITS, CMD_BITS } = require('./register-map');

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const CONTROLLER_IP = '192.168.0.1';       // S7-1200 default IP
const MODBUS_PORT = 502;         // ✅ S7-1200 MB_SERVER port
const MODBUS_UNIT_ID = 1;
const POLL_INTERVAL = 250;
const WS_PORT = 3001;
// ─────────────────────────────────────────────────────────────────────────────

const client = new ModbusRTU();
const wss = new WebSocketServer({ port: WS_PORT });

let connected = false;
let lastStatus = buildDefaultStatus();
let pollTimer = null;

// ─── Modbus connection ────────────────────────────────────────────────────────
async function connectModbus() {
    try {
        await client.connectTCP(CONTROLLER_IP, { port: MODBUS_PORT });
        client.setID(MODBUS_UNIT_ID);
        client.setTimeout(5000);
        connected = true;
        console.log(`[Modbus] ✅ Connected to ${CONTROLLER_IP}:${MODBUS_PORT}`);

        // First read immediately
        await pollOnce();
        startPolling();
    } catch (err) {
        console.error(`[Modbus] ❌ Connect failed: ${err.message} — retry in 3s`);
        setTimeout(connectModbus, 3000);
    }
}

client.on('close', () => {
    if (connected) {
        console.warn('[Modbus] Connection lost — reconnecting...');
        connected = false;
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
        setTimeout(connectModbus, 3000);
    }
});

// ─── Polling ─────────────────────────────────────────────────────────────────
async function pollOnce() {
    if (!connected) return;
    try {
        const result = await client.readHoldingRegisters(STATUS.STATUS_WORD, 10);
        const regs = result.data;

        const statusWord = regs[0];
        const posRaw = (regs[1] << 16) | regs[2];
        const actualPos = toSigned32(posRaw) * 0.001;
        const actualVel = toSigned16(regs[3]);
        const torque = regs[4] / 10;

        const bit = (n) => !!(statusWord & (1 << n));
        const state = resolveState(bit);

        lastStatus = {
            state,
            actualPosition: actualPos,
            actualVelocity: actualVel,
            targetPosition: 0,
            servoOn: bit(STATUS_BITS.SERVO_ON),
            homed: bit(STATUS_BITS.HOMED),
            stoActive: bit(STATUS_BITS.STO),
            faultActive: bit(STATUS_BITS.FAULT),
            alarmCode: regs[5] ? `A.${regs[5].toString(16).toUpperCase()}` : null,
            softLimitMin: 0,
            softLimitMax: 1000,
            torquePercent: torque,
            encoderCounts: Math.round(actualPos * 167772.16),
            commOk: true,
            driveTemp: regs[6] / 10,
            busVoltage: regs[7],
        };

        broadcast({ type: 'STATUS', payload: lastStatus });
        console.log(`[Poll] state=${lastStatus.state}  pos=${lastStatus.actualPosition.toFixed(3)}mm`);
    } catch (err) {
        console.warn('[Modbus] Poll error:', err.message);
        lastStatus.commOk = false;
        broadcast({ type: 'STATUS', payload: lastStatus });
    }
}

function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(pollOnce, POLL_INTERVAL);
}

// ─── WebSocket ────────────────────────────────────────────────────────────────
wss.on('listening', () =>
    console.log(`[WS]   Listening  →  ws://localhost:${WS_PORT}`));

wss.on('connection', (ws) => {
    console.log('[WS]   Browser connected');
    ws.send(JSON.stringify({ type: 'STATUS', payload: lastStatus }));

    ws.on('message', async (raw) => {
        let msg;
        try { msg = JSON.parse(raw); } catch { return; }
        const result = await handleCommand(msg);
        ws.send(JSON.stringify({ type: 'CMD_ACK', command: msg.command, result }));
    });

    ws.on('close', () => console.log('[WS]   Browser disconnected'));
});

function broadcast(data) {
    const json = JSON.stringify(data);
    for (const ws of wss.clients) if (ws.readyState === 1) ws.send(json);
}

// ─── Commands ─────────────────────────────────────────────────────────────────
async function handleCommand(msg) {
    if (!connected) return 'REJECTED: Not connected';
    try {
        switch (msg.command) {
            case 'servoOn': await pulseCommandBit(CMD_BITS.SERVO_ON); return 'SUCCESS';
            case 'servoOff': await pulseCommandBit(CMD_BITS.SERVO_OFF); return 'SUCCESS';
            case 'startHoming': await pulseCommandBit(CMD_BITS.START_HOME); return 'SUCCESS';
            case 'immediateStop': await pulseCommandBit(CMD_BITS.STOP); return 'SUCCESS';
            case 'resetAlarms': await pulseCommandBit(CMD_BITS.RESET_ALARM); return 'SUCCESS';

            case 'absoluteMove': {
                const posRaw = Math.round((msg.target ?? 0) * 1000);
                await client.writeRegisters(CMD.TARGET_POS_HI, [
                    (posRaw >> 16) & 0xFFFF,
                    posRaw & 0xFFFF,
                ]);
                await client.writeRegister(CMD.TARGET_VEL, msg.velocity ?? 500);
                await pulseCommandBit(CMD_BITS.ABS_MOVE);
                return 'SUCCESS';
            }

            case 'jogStart':
                await pulseCommandBit(
                    msg.dir === 'FWD' ? CMD_BITS.JOG_FWD : CMD_BITS.JOG_REV);
                return 'SUCCESS';

            case 'jogStop':
                await client.writeRegister(CMD.COMMAND_WORD, 0);
                return 'SUCCESS';

            default: return `REJECTED: Unknown "${msg.command}"`;
        }
    } catch (err) {
        return `FAULT: ${err.message}`;
    }
}

async function pulseCommandBit(bit) {
    await client.writeRegister(CMD.COMMAND_WORD, 1 << bit);
    await delay(100);
    await client.writeRegister(CMD.COMMAND_WORD, 0);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function resolveState(bit) {
    if (bit(STATUS_BITS.FAULT)) return 'FAULT';
    if (bit(STATUS_BITS.HOMING)) return 'HOMING';
    if (bit(STATUS_BITS.MOVING)) return 'MOVING';
    if (bit(STATUS_BITS.JOGGING)) return 'JOGGING';
    if (bit(STATUS_BITS.SERVO_ON)) return 'READY';
    return 'SERVO_OFF';
}

function toSigned32(v) { return v > 0x7FFFFFFF ? v - 0x100000000 : v; }
function toSigned16(v) { return v > 0x7FFF ? v - 0x10000 : v; }
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function buildDefaultStatus() {
    return {
        state: 'SERVO_OFF', actualPosition: 0, actualVelocity: 0,
        targetPosition: 0, servoOn: false, homed: false, stoActive: false,
        faultActive: false, alarmCode: null, softLimitMin: 0, softLimitMax: 1000,
        torquePercent: 0, encoderCounts: 0, commOk: false, driveTemp: 0, busVoltage: 0,
    };
}

// ─── Start ────────────────────────────────────────────────────────────────────
console.log('');
console.log('╔══════════════════════════════════════════════════════╗');
console.log('║  S7-1200 Backend  ─  Modbus TCP CLIENT  🎉           ║');
console.log(`║  Connecting to ${CONTROLLER_IP}:${MODBUS_PORT}                ║`);
console.log(`║  WebSocket  →  ws://localhost:${WS_PORT}                 ║`);
console.log('╚══════════════════════════════════════════════════════╝');
console.log('');

connectModbus();
