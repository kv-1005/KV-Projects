const ws = new WebSocket(`ws://${window.location.host}`);

// State management
let currentState = {
    load: 0,
    maxLoad: 25,
    hookHeight: 0,
    trolleyRadius: 0,
    slewAngle: 0,
    windSpeed: 0,
    engineTemp: 0,
    hydraulicPressure: 0,
    alarms: [],
    status: "Safe"
};

// UI Elements
const elements = {
    load: document.getElementById('val-load'),
    height: document.getElementById('val-height'),
    radius: document.getElementById('val-radius'),
    angle: document.getElementById('val-angle'),
    wind: document.getElementById('val-wind'),
    temp: document.getElementById('val-temp'),
    pressure: document.getElementById('val-pressure'),
    status: document.getElementById('system-status-indicator'),
    statusText: document.getElementById('status-text'),
    alarmList: document.getElementById('alarm-list')
};

// Navigation
const navItems = document.querySelectorAll('.nav-item');
const screens = document.querySelectorAll('.screen');

navItems.forEach(item => {
    item.addEventListener('click', () => {
        const screenId = item.getAttribute('data-screen');

        // Update Nav
        navItems.forEach(ni => ni.classList.remove('active'));
        item.classList.add('active');

        // Update Screen
        screens.forEach(s => s.classList.remove('active'));
        document.getElementById(`screen-${screenId}`).classList.add('active');
    });
});

// WebSocket Handling
ws.onopen = () => console.log("Connected to PLC Simulator");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    currentState = data;
    updateUI();
};

function updateUI() {
    if (elements.load) elements.load.innerText = currentState.load.toFixed(1);
    if (elements.height) elements.height.innerText = currentState.hookHeight.toFixed(1);
    if (elements.radius) elements.radius.innerText = currentState.trolleyRadius.toFixed(1);
    if (elements.angle) elements.angle.innerText = currentState.slewAngle.toFixed(0);
    if (elements.wind) elements.wind.innerText = currentState.windSpeed.toFixed(1);
    if (elements.temp) elements.temp.innerText = currentState.engineTemp.toFixed(1);
    if (elements.pressure) elements.pressure.innerText = currentState.hydraulicPressure.toFixed(0);

    // Status Indicator
    if (elements.status) {
        elements.status.className = `status-indicator status-${currentState.status.toLowerCase()}`;
        elements.statusText.innerText = currentState.status;
    }

    // Alarms
    if (elements.alarmList) {
        if (currentState.alarms.length === 0) {
            elements.alarmList.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 20px;">No Active Alarms</div>';
        } else {
            elements.alarmList.innerHTML = currentState.alarms.map(alarm => `
        <div class="alarm-item">
          <div class="alarm-msg">${alarm.msg}</div>
          <div class="alarm-time">${new Date(currentState.timestamp).toLocaleTimeString()}</div>
        </div>
      `).join('');
        }
    }

    // Update Visualizations (if any)
    drawCraneViz();
}

// Simple Canvas Visualization
function drawCraneViz() {
    const canvas = document.getElementById('crane-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Design constants
    const groundY = h - 20;
    const towerX = 60;
    const towerWidth = 20;
    const jibHeight = 80;
    const jibWidth = w - 100;

    // Draw Ground
    ctx.strokeStyle = '#333';
    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(w, groundY);
    ctx.stroke();

    // Draw Tower
    ctx.fillStyle = '#444';
    ctx.fillRect(towerX - towerWidth / 2, jibHeight, towerWidth, groundY - jibHeight);

    // Draw Jib
    ctx.fillStyle = '#666';
    ctx.fillRect(towerX - 10, jibHeight - 10, jibWidth, 10);

    // Draw Trolley
    const trolleyX = towerX + (currentState.trolleyRadius / 50) * jibWidth; // Scale radius to width
    ctx.fillStyle = '#00e0ff';
    ctx.fillRect(trolleyX - 5, jibHeight, 10, 5);

    // Draw Hook & Line
    const hookY = jibHeight + (currentState.hookHeight / 50) * (groundY - jibHeight); // Scale height
    ctx.strokeStyle = '#00e0ff';
    ctx.beginPath();
    ctx.moveTo(trolleyX, jibHeight + 5);
    ctx.lineTo(trolleyX, hookY);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(trolleyX, hookY, 4, 0, Math.PI * 2);
    ctx.fill();
}

// Commands
window.sendCommand = (type, val) => {
    const cmd = {};
    if (type === 'height') cmd.targetHookHeight = parseFloat(val);
    if (type === 'radius') cmd.targetTrolleyRadius = parseFloat(val);
    if (type === 'angle') cmd.targetSlewAngle = parseFloat(val);
    if (type === 'alarm') cmd.toggleAlarm = true;
    ws.send(JSON.stringify(cmd));
};

// Initial draw resize
window.addEventListener('resize', () => {
    const canvas = document.getElementById('crane-canvas');
    if (canvas) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
    }
});

// Set initial canvas size
setTimeout(() => {
    const canvas = document.getElementById('crane-canvas');
    if (canvas) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
    }
}, 100);
