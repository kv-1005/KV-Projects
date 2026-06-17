// Simplified PLC Configuration - DIGITAL OUTPUTS ONLY
export default {
    connection: {
        host: '192.168.0.1',  // PLC IP address - UPDATE THIS
        port: 102,
        rack: 0,
        slot: 1
    },

    // Only testing Digital Outputs (8 bits)
    variables: {
        digitalBits: 'DB2,BYTE0'  // 1 byte at DB2.DBB0 (8 bits)
    },

    pollInterval: 100  // Read every 100ms
};
