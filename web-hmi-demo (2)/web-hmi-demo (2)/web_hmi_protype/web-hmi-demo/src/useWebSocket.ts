import { useEffect, useCallback } from 'react';
import { usePLCStore } from './store';

export const useWebSocket = () => {
    const { setData, setConnected } = usePLCStore();

    // Singleton socket reference
    let socket: WebSocket | null = null;

    const sendCommand = useCallback((cmd: any) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(cmd));
        }
    }, []);

    useEffect(() => {
        let reconnectTimeout: number;
        let simulationInterval: number;
        let simulationActive = false;

        const startSimulation = () => {
            console.log('🎮 HMI: Starting DEMO MODE (simulated PLC data)');
            simulationActive = true;

            // Initial state
            const simState = {
                analogValue: 45,
                digitalBits: [0, 0, 0, 0, 0, 0, 0, 0],
                plcStatus: 'RUN',
                counter: 0,
                cpuTemp: 45.0,
                uptime: 0,
                timestamp: Date.now(),
                isConnected: true // Show as connected in demo mode
            };

            // Update simulation every 100ms
            simulationInterval = window.setInterval(() => {
                // Slowly change analog value (tank level)
                simState.analogValue += (Math.random() - 0.5) * 2;
                simState.analogValue = Math.max(0, Math.min(100, simState.analogValue));

                // Randomly toggle digital bits (equipment on/off)
                if (Math.random() > 0.98) { // 2% chance each cycle
                    const bitIndex = Math.floor(Math.random() * 5); // Toggle bits 0-4
                    simState.digitalBits[bitIndex] = simState.digitalBits[bitIndex] ? 0 : 1;
                }

                // Increment counter
                simState.counter++;

                // Vary temperature slightly
                simState.cpuTemp = 45 + Math.sin(Date.now() / 5000) * 5 + Math.random() * 2;

                // Update uptime
                simState.uptime = Math.floor((Date.now() - simState.timestamp) / 1000);

                // Send to store
                setData({ ...simState });
            }, 100);

            // Set initial state
            setData(simState);
            setConnected(true);
        };

        const connect = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log('✅ HMI: Connected to real PLC Gateway');
                setConnected(true);

                // Stop simulation if it was running
                if (simulationActive) {
                    simulationActive = false;
                    clearInterval(simulationInterval);
                }
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setData(data);
                } catch (e) {
                    console.error('HMI: Protocol Error', e);
                }
            };

            socket.onclose = () => {
                console.warn('⚠️ HMI: Gateway disconnected. Starting DEMO MODE...');
                setConnected(false);

                // Start simulation after connection fails
                if (!simulationActive) {
                    setTimeout(startSimulation, 1000);
                }

                // Still try to reconnect in background
                reconnectTimeout = window.setTimeout(connect, 5000);
            };

            socket.onerror = (err) => {
                console.error('❌ HMI: Socket Error - will use DEMO MODE');
                if (socket) socket.close();
            };
        };

        // Try to connect first
        connect();

        // If connection doesn't succeed in 2 seconds, start simulation
        const startupTimeout = window.setTimeout(() => {
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                console.log('🎮 No PLC Gateway detected - starting DEMO MODE immediately');
                if (!simulationActive) {
                    startSimulation();
                }
            }
        }, 2000);

        return () => {
            if (socket) socket.close();
            clearTimeout(reconnectTimeout);
            clearTimeout(startupTimeout);
            clearInterval(simulationInterval);
        };
    }, [setData, setConnected]);

    return { sendCommand };
};
