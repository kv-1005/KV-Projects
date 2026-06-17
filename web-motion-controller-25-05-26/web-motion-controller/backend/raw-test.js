/**
 * Raw Modbus TCP diagnostic — sends raw bytes to S7-1200
 * to confirm whether the S7-1200 MB_SERVER responds to Modbus TCP protocol.
 * Run: node raw-test.js
 */

'use strict';

const net = require('net');

const HOST = '192.168.0.1';  // S7-1200 default IP
const PORT = 502;  // S7-1200 MB_SERVER port

// Modbus TCP Read Holding Registers (FC3)
// Transaction: 0x0001, Protocol: 0x0000, Length: 0x0006
// Unit: 0xFF (255), FC: 0x03, Start: 0x0000, Qty: 0x0001
const REQUEST = Buffer.from([
    0x00, 0x01,   // Transaction ID
    0x00, 0x00,   // Protocol ID (Modbus TCP = 0)
    0x00, 0x06,   // Length (6 bytes follow)
    0xFF,         // Unit ID (255 = broadcast)
    0x03,         // Function Code: Read Holding Registers
    0x00, 0x00,   // Starting Address: 0 (MW00000)
    0x00, 0x01    // Quantity: 1 register
]);

console.log(`\nConnecting to ${HOST}:${PORT}...`);

const socket = new net.Socket();
let responseReceived = false;

socket.setTimeout(5000);

socket.connect(PORT, HOST, () => {
    console.log('✅ TCP Connected!');
    console.log('Sending raw Modbus read request...');
    console.log('Request bytes:', REQUEST.toString('hex'));
    socket.write(REQUEST);
});

socket.on('data', (data) => {
    responseReceived = true;
    console.log('\n🎉 RESPONSE RECEIVED from controller!');
    console.log('Response bytes:', data.toString('hex'));
    console.log('Response length:', data.length, 'bytes');

    if (data.length >= 9) {
        const fnCode = data[7];
        const byteCount = data[8];
        console.log('\nParsed:');
        console.log('  Function Code:', fnCode === 0x03 ? '03 (Read Holding Registers)' : `0x${fnCode.toString(16)}`);
        console.log('  Byte count:', byteCount);
        if (byteCount >= 2) {
            const value = (data[9] << 8) | data[10];
            console.log('  Register[0] value:', value);
        }
    }
    socket.destroy();
});

socket.on('timeout', () => {
    console.log('\n⏰ Timeout — no response in 5 seconds');
    if (!responseReceived) {
        console.log('   This port may not be Modbus TCP, or the 218IFA is rejecting requests.');
    }
    socket.destroy();
});

socket.on('error', (err) => {
    console.error('\n❌ Error:', err.message);
});

socket.on('close', () => {
    console.log('\nConnection closed.');
    if (!responseReceived) {
        console.log('\n──────────────────────────────────────────────');
        console.log('No Modbus response from port 10001.');
        console.log('Possible causes:');
        console.log('  1. MB_SERVER may not be configured in TIA Portal');
        console.log('  2. S7-1200 CPU must be in RUN mode to process requests');
        console.log('  3. Unit ID or register address issue');
        console.log('──────────────────────────────────────────────');
    }
});
