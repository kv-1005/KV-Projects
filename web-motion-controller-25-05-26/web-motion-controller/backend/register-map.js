/**
 * Siemens S7-1200 Modbus TCP Register Map (via MB_SERVER)
 *
 * The S7-1200 MB_SERVER maps Modbus Holding Registers to a Data Block (DB).
 * Modbus Holding Register offset corresponds to DB Word offsets as follows:
 *   Modbus Holding Register N  ===  DB Word Offset (N * 2)
 *
 * Example mapping:
 *   Modbus HR 100 (STATUS_WORD)  === DBW200 (Word at byte offset 200)
 *   Modbus HR 101/102 (POS_HI/LO) === DBD202 (Double Word at byte offset 202)
 *   Modbus HR 200 (COMMAND_WORD) === DBW400 (Word at byte offset 400)
 *
 * STATUS REGISTERS (Read from S7-1200 → Web Dashboard)
 * Map these variables in SCL to write to your MB_SERVER DB (offset 200+).
 */
const STATUS = {
    STATUS_WORD: 100,   // MW00100 — bit field: b0=servoOn, b1=homed, b2=moving, b3=fault, b4=jogging, b5=homing
    POSITION_HI: 101,   // MW00101 — actual position HIGH word (×0.001mm, 32-bit split)
    POSITION_LO: 102,   // MW00102 — actual position LOW word
    VELOCITY: 103,   // MW00103 — actual velocity (mm/s, signed int16)
    TORQUE: 104,   // MW00104 — torque % ×10 (e.g., 456 = 45.6%)
    ALARM_CODE: 105,   // MW00105 — active alarm code (0 = none)
    DRIVE_TEMP: 106,   // MW00106 — drive temperature ×10 (°C)
    BUS_VOLTAGE: 107,   // MW00107 — DC bus voltage (V)
    TARGET_POS_HI: 108,   // MW00108 — target position HIGH (echo back)
    TARGET_POS_LO: 109,   // MW00109 — target position LOW (echo back)
};

/**
 * COMMAND REGISTERS (Write from Web Dashboard → S7-1200)
 * Read these in your SCL program to trigger MC_Power, MC_MoveAbsolute, or MC_Jog.
 */
const CMD = {
    COMMAND_WORD: 200,   // MW00200 — bit field: b0=servoOn, b1=servoOff, b2=startHome, b3=move, b4=jogFwd, b5=jogRev, b6=stop, b7=resetAlarm
    TARGET_POS_HI: 201,   // MW00201 — move target HIGH word (×0.001mm)
    TARGET_POS_LO: 202,   // MW00202 — move target LOW word
    TARGET_VEL: 203,   // MW00203 — move velocity (mm/s)
};

// Bit positions for STATUS_WORD (MW00100)
const STATUS_BITS = {
    SERVO_ON: 0,
    HOMED: 1,
    MOVING: 2,
    FAULT: 3,
    JOGGING: 4,
    HOMING: 5,
    STO: 6,
    COMM_OK: 7,
};

// Bit positions for COMMAND_WORD (MW00200)
const CMD_BITS = {
    SERVO_ON: 0,
    SERVO_OFF: 1,
    START_HOME: 2,
    ABS_MOVE: 3,
    JOG_FWD: 4,
    JOG_REV: 5,
    STOP: 6,
    RESET_ALARM: 7,
};

module.exports = { STATUS, CMD, STATUS_BITS, CMD_BITS };
