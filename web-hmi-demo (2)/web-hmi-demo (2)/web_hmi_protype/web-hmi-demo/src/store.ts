import { create } from 'zustand';

interface PLCState {
    // PLC Data (Simulated or Real)
    analogValue: number;      // 0.0 - 100.0
    digitalBits: number[];    // [Bit 0, Bit 1, ... Bit 7]
    plcStatus: string;        // "RUN", "STOP", "ERROR"
    counter: number;          // Rapidly incrementing test counter
    cpuTemp: number;          // CPU Temperature
    uptime: number;           // Seconds since system start

    // System Meta
    timestamp: number;
    isConnected: boolean;
    serverIp: string;

    // Actions
    setData: (data: Partial<PLCState>) => void;
    setConnected: (status: boolean) => void;
}

export const usePLCStore = create<PLCState>((set) => ({
    analogValue: 0,
    digitalBits: [0, 0, 0, 0, 0, 0, 0, 0],
    plcStatus: 'OFFLINE',
    counter: 0,
    cpuTemp: 35.0,
    uptime: 0,

    timestamp: Date.now(),
    isConnected: false,
    serverIp: '0.0.0.0',

    setData: (data) => set((state) => ({ ...state, ...data })),
    setConnected: (status) => set({ isConnected: status }),
}));
