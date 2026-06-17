import express from "express";
import { WebSocketServer } from "ws";
import path from "path";
import { fileURLToPath } from "url";
import NodeS7 from "nodes7";
import plcConfig from "./plc-config.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001; // PLC Gateway Port

app.use(express.static(path.join(__dirname, "dist")));

const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`[PLC_GATEWAY]: Core online at 0.0.0.0:${PORT}`);
});

const wss = new WebSocketServer({ server });

// --- S7 PLC Connection ---
const plc = new NodeS7();
let plcConnected = false;

// PLC Data Structure
let plcData = {
    analogValue: 0,
    digitalBits: [0, 0, 0, 0, 0, 0, 0, 0],
    plcStatus: "STOP",
    counter: 0,
    cpuTemp: 0,
    uptime: 0,
    timestamp: Date.now(),
    isConnected: false
};

// Initialize PLC Connection
function connectPLC() {
    console.log(`[S7_COMM]: Attempting connection to ${plcConfig.connection.host}...`);

    plc.initiateConnection(
        {
            port: plcConfig.connection.port,
            host: plcConfig.connection.host,
            rack: plcConfig.connection.rack,
            slot: plcConfig.connection.slot
        },
        (err) => {
            if (err) {
                console.error(`[S7_COMM]: Connection failed:`, err.message);
                plcConnected = false;
                plcData.isConnected = false;

                // Retry connection after 5 seconds
                setTimeout(connectPLC, 5000);
                return;
            }

            console.log(`[S7_COMM]: ✓ Connected to PLC at ${plcConfig.connection.host}`);
            plcConnected = true;
            plcData.isConnected = true;

            // Set up variable addresses
            plc.addItems([
                'analogValue',
                'digitalBits',
                'counter',
                'cpuTemp',
                'plcStatus'
            ]);

            plc.setTranslationCB((tag) => plcConfig.variables[tag]);

            // Start reading PLC data
            startPLCPolling();
        }
    );
}

// PLC Read Cycle
const startTime = Date.now();
let pollTimer = null;

function startPLCPolling() {
    if (pollTimer) clearInterval(pollTimer);

    pollTimer = setInterval(() => {
        if (!plcConnected) return;

        plc.readAllItems((err, values) => {
            if (err) {
                console.error(`[S7_COMM]: Read error:`, err.message);
                plcConnected = false;
                plcData.isConnected = false;

                // Attempt reconnection
                setTimeout(connectPLC, 2000);
                return;
            }

            // Update PLC data from read values
            if (values.analogValue !== undefined) {
                // Scale REAL value (0-100) to percentage
                plcData.analogValue = Math.max(0, Math.min(100, values.analogValue));
            }

            if (values.digitalBits !== undefined) {
                // Convert byte to bit array
                const byte = values.digitalBits;
                plcData.digitalBits = Array.from({ length: 8 }, (_, i) => (byte >> i) & 1);
            }

            if (values.counter !== undefined) {
                plcData.counter = values.counter;
            }

            if (values.cpuTemp !== undefined) {
                plcData.cpuTemp = values.cpuTemp;
            }

            if (values.plcStatus !== undefined) {
                plcData.plcStatus = values.plcStatus ? "RUN" : "STOP";
            }

            // Update metadata
            plcData.uptime = Math.floor((Date.now() - startTime) / 1000);
            plcData.timestamp = Date.now();

            // Broadcast to all WebSocket clients
            broadcast(JSON.stringify(plcData));
        });
    }, plcConfig.pollInterval);
}

function broadcast(msg) {
    wss.clients.forEach(client => {
        if (client.readyState === 1) {
            client.send(msg);
        }
    });
}

// WebSocket Connection Handler
wss.on("connection", (ws, req) => {
    const ip = req.socket.remoteAddress;
    console.log(`[COMM_LINK]: New HMI Client authorized from ${ip}`);

    // Send current state immediately
    ws.send(JSON.stringify(plcData));

    ws.on("message", (msg) => {
        try {
            const cmd = JSON.parse(msg);

            if (!plcConnected) {
                console.warn(`[PLC_WRITE]: Cannot write - PLC disconnected`);
                return;
            }

            // Handle Bit Toggles
            if (cmd.bitToggle !== undefined) {
                const idx = cmd.bitToggle;
                const currentByte = plcData.digitalBits.reduce((acc, bit, i) => acc | (bit << i), 0);
                const newByte = currentByte ^ (1 << idx); // Toggle bit

                plc.writeItems(plcConfig.variables.digitalBits, newByte, (err) => {
                    if (err) {
                        console.error(`[PLC_WRITE]: Bit toggle failed:`, err.message);
                    } else {
                        console.log(`[PLC_WRITE]: Bit ${idx} toggled`);
                    }
                });
            }

            // Handle Analog Set
            if (cmd.setAnalog !== undefined) {
                const value = parseFloat(cmd.setAnalog);

                plc.writeItems(plcConfig.variables.analogValue, value, (err) => {
                    if (err) {
                        console.error(`[PLC_WRITE]: Analog write failed:`, err.message);
                    } else {
                        console.log(`[PLC_WRITE]: Analog set to ${value}`);
                    }
                });
            }

            // Handle PLC Status Change
            if (cmd.setStatus !== undefined) {
                const status = cmd.setStatus === "RUN" ? 1 : 0;

                plc.writeItems(plcConfig.variables.plcStatus, status, (err) => {
                    if (err) {
                        console.error(`[PLC_WRITE]: Status write failed:`, err.message);
                    } else {
                        console.log(`[PLC_WRITE]: PLC Status set to ${cmd.setStatus}`);
                    }
                });
            }

        } catch (e) {
            console.error("[PROTOCOL_ERROR]: Malformed command", e);
        }
    });

    ws.on("close", () => console.log(`[COMM_LINK]: Client disconnected`));
});

// Start PLC connection
connectPLC();

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n[SHUTDOWN]: Closing PLC connection...');
    if (pollTimer) clearInterval(pollTimer);
    plc.dropConnection();
    process.exit(0);
});
