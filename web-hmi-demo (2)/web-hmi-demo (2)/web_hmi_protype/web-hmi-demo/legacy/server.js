const express = require("express");
const WebSocket = require("ws");

const app = express();
app.use(express.static("public"));

const server = app.listen(3000, () =>
  console.log("Server running at http://localhost:3000")
);

const wss = new WebSocket.Server({ server });

// ---- Crane PLC Simulation DATA ----
let plcData = {
  load: 5.2,          // tons
  maxLoad: 25.0,      // tons
  hookHeight: 12.5,   // meters
  trolleyRadius: 18.0, // meters
  slewAngle: 45,      // degrees
  windSpeed: 12.4,    // km/h
  engineTemp: 65,     // celsius
  hydraulicPressure: 180, // bar
  alarms: [],
  status: "Safe",     // Safe, Warning, Overload
  timestamp: Date.now()
};

// Movement targets (set via commands)
let targets = {
  hookHeight: 12.5,
  trolleyRadius: 18.0,
  slewAngle: 45
};

// Simulation Loop (10Hz)
setInterval(() => {
  // Simulate Hook Movement
  if (Math.abs(plcData.hookHeight - targets.hookHeight) > 0.1) {
    plcData.hookHeight += (targets.hookHeight > plcData.hookHeight ? 0.1 : -0.1);
  }

  // Simulate Trolley Movement
  if (Math.abs(plcData.trolleyRadius - targets.trolleyRadius) > 0.1) {
    plcData.trolleyRadius += (targets.trolleyRadius > plcData.trolleyRadius ? 0.1 : -0.1);
  }

  // Simulate Slew Movement
  if (Math.abs(plcData.slewAngle - targets.slewAngle) > 0.5) {
    plcData.slewAngle += (targets.slewAngle > plcData.slewAngle ? 1 : -1);
  }

  // Randomize wind and load slightly
  plcData.windSpeed = Math.max(0, plcData.windSpeed + (Math.random() * 0.4 - 0.2));
  plcData.load = Math.max(0, 5.2 + (Math.random() * 0.1 - 0.05));
  plcData.engineTemp = 60 + Math.sin(Date.now() / 10000) * 10;
  
  // Logic for status
  if (plcData.load > plcData.maxLoad * 0.9) {
    plcData.status = "Warning";
  } else if (plcData.load > plcData.maxLoad) {
    plcData.status = "Overload";
  } else {
    plcData.status = "Safe";
  }

  plcData.timestamp = Date.now();
}, 100);

// WebSocket connection
wss.on("connection", ws => {
  console.log("Client connected");

  // Send data every 200ms
  const interval = setInterval(() => {
    ws.send(JSON.stringify(plcData));
  }, 200);

  // Receive commands from UI
  ws.on("message", msg => {
    try {
      const command = JSON.parse(msg);
      if (command.targetHookHeight !== undefined) targets.hookHeight = command.targetHookHeight;
      if (command.targetTrolleyRadius !== undefined) targets.trolleyRadius = command.targetTrolleyRadius;
      if (command.targetSlewAngle !== undefined) targets.slewAngle = command.targetSlewAngle;
      
      // Toggle Alarms for testing
      if (command.toggleAlarm) {
        if (plcData.alarms.length > 0) plcData.alarms = [];
        else plcData.alarms.push({ id: 1, type: "Warning", msg: "Wind speed high" });
      }
    } catch (e) {
      console.error("Failed to parse command", e);
    }
  });

  ws.on("close", () => clearInterval(interval));
});
