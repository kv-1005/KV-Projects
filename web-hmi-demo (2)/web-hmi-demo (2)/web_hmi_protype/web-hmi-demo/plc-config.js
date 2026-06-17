// PLC Connection Configuration
export default {
    connection: {
        host: '192.168.0.1',  // PLC IP address (verified from TIA Portal)
        port: 102,             // S7 protocol port (default)
        rack: 0,               // CPU rack number (usually 0 for S7-1200)
        slot: 1                // CPU slot number (usually 1 for S7-1200)
    },

    // Variable mapping: PLC address -> HMI data
    // Format: 'DB<number>,<type><offset>'
    // Types: REAL (4 bytes), DINT (4 bytes), INT (2 bytes), BYTE (1 byte), X (bit)
    variables: {
        analogValue: 'DB1,REAL0',      // 4 bytes starting at DB1.DBD0
        digitalBits: 'DB1,BYTE4',      // 1 byte at DB1.DBB4 (8 bits)
        counter: 'DB1,DINT8',          // 4 bytes at DB1.DBD8
        cpuTemp: 'DB1,REAL12',         // 4 bytes at DB1.DBD12
        plcStatus: 'DB1,X16.0'         // 1 bit at DB1.DBX16.0 (RUN/STOP)
    },

    pollInterval: 50  // Read cycle in milliseconds (50ms = 20Hz)
};
