import express from "express";
import { WebSocketServer } from "ws";
import path from "path";
import { fileURLToPath } from "url";
import NodeS7 from "nodes7";
import plcConfig from "./plc-config-simple.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

app.use(express.static(path.join(__dirname, "dist")));

const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`[SERVER]: v2 (Tag Name Fix) - Running at http://localhost:${PORT}`);
});

const wss = new WebSocketServer({ server });

// --- S7 PLC Connection ---
const plc = new NodeS7();
let plcConnected = false;

// Digital Outputs Only
let digitalBits = [0, 0, 0, 0, 0, 0, 0, 0];

// Connect to PLC
function connectPLC() {
    console.log(`[PLC]: Connecting to ${plcConfig.connection.host}...`);

    plc.initiateConnection(
        {
            port: plcConfig.connection.port,
            host: plcConfig.connection.host,
            rack: plcConfig.connection.rack,
            slot: plcConfig.connection.slot
        },
        (err) => {
            if (err) {
                console.error(`[PLC]: ❌ Connection failed:`, err.message);
                plcConnected = false;
                setTimeout(connectPLC, 5000);
                return;
            }

            console.log(`[PLC]: ✅ Connected!`);
            plcConnected = true;

            plc.addItems(['digitalBits']);
            plc.setTranslationCB((tag) => plcConfig.variables[tag]);

            startPolling();
        }
    );
}

// Read PLC every 100ms
let pollTimer = null;

function startPolling() {
    if (pollTimer) clearInterval(pollTimer);

    pollTimer = setInterval(() => {
        if (!plcConnected) return;

        plc.readAllItems((err, values) => {
            if (err) {
                console.error(`[PLC]: Read error:`, err.message);
                plcConnected = false;
                setTimeout(connectPLC, 2000);
                return;
            }

            // Convert byte to bit array
            if (values.digitalBits !== undefined) {
                const byte = values.digitalBits;
                digitalBits = Array.from({ length: 8 }, (_, i) => (byte >> i) & 1);

                // Broadcast to HMI
                broadcast(JSON.stringify({
                    digitalBits: digitalBits,
                    isConnected: plcConnected
                }));
            }
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

// WebSocket Handler
wss.on("connection", (ws) => {
    console.log(`[CLIENT]: Connected`);

    // Send current state
    ws.send(JSON.stringify({
        digitalBits: digitalBits,
        isConnected: plcConnected
    }));

    ws.on("message", (msg) => {
        try {
            const cmd = JSON.parse(msg);

            if (!plcConnected) {
                console.warn(`[PLC]: Cannot write - disconnected`);
                return;
            }

            // Toggle bit
            if (cmd.bitToggle !== undefined) {
                const idx = cmd.bitToggle;
                const currentByte = digitalBits.reduce((acc, bit, i) => acc | (bit << i), 0);
                const newByte = currentByte ^ (1 << idx); // Toggle

                // Write to 'digitalBits' tag (which resolves to DB2,BYTE0 via translation CB)
                plc.writeItems('digitalBits', newByte, (err) => {
                    if (err) {
                        console.error(`[PLC]: Write failed:`, err.message);
                    } else {
                        console.log(`[PLC]: ✓ Bit ${idx} toggled to ${(newByte >> idx) & 1}`);
                    }
                });
            }

        } catch (e) {
            console.error("[ERROR]:", e);
        }
    });

    ws.on("close", () => console.log(`[CLIENT]: Disconnected`));
});

// Start
connectPLC();

process.on('SIGINT', () => {
    console.log('\n[SHUTDOWN]');
    if (pollTimer) clearInterval(pollTimer);
    plc.dropConnection();
    process.exit(0);
});
