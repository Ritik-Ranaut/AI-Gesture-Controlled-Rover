/**
 * ============================================================================
 * STAIR-CLIMBING ROVER MAIN CONTROLLER
 * Platform: Arduino Nano (ATmega328P)
 * 
 * Hardware Modules:
 * - BTS7960 Motor Drivers (High-current Dual H-bridge for 6 DC Drive Motors)
 * - PCA9685 16-Channel 12-bit PWM I2C Driver (Stair-Climbing Leg Servos)
 * - HC-05 Bluetooth Transceiver (Wireless UART)
 * - FlySky FS-i6 RC Receiver (Optional hardware manual override)
 * 
 * Safety Features:
 * - 500ms Hardware Communication Watchdog (Auto-stops if link drops)
 * - Startup Disarmed state (Prevents accidental motor surge on boot)
 * - Non-blocking State Machine for 360° Turn & Crab Walk sequences
 * ============================================================================
 */

#include <Wire.h>

// --- CONFIGURATION & PIN DEFINITIONS ---

// Use SoftwareSerial if Bluetooth is wired to digital pins 2 & 3
// Set to 0 to use Hardware Serial (Pins 0 & 1)
#define USE_SOFTWARE_SERIAL 0

#if USE_SOFTWARE_SERIAL
  #include <SoftwareSerial.h>
  SoftwareSerial btSerial(2, 3); // RX = Pin 2, TX = Pin 3
  #define SERIAL_PORT btSerial
#else
  #define SERIAL_PORT Serial
#endif

// BTS7960 Left Motor Driver Pins
const int PIN_L_RPWM = 5;  // PWM Forward Left
const int PIN_L_LPWM = 6;  // PWM Reverse Left
const int PIN_L_EN   = 7;  // Enable Left

// BTS7960 Right Motor Driver Pins
const int PIN_R_RPWM = 9;  // PWM Forward Right
const int PIN_R_LPWM = 10; // PWM Reverse Right
const int PIN_R_EN   = 8;  // Enable Right

// Builtin status LED
const int PIN_LED = 13;

// PCA9685 I2C Address & Channels
const uint8_t PCA9685_ADDR = 0x40;
const uint8_t SERVO_FRONT_LEFT  = 0;
const uint8_t SERVO_FRONT_RIGHT = 1;
const uint8_t SERVO_REAR_LEFT   = 2;
const uint8_t SERVO_REAR_RIGHT  = 3;

// Servo Pulse Calibration (50Hz: ~1ms to ~2ms across 4096 steps)
const int SERVO_PULSE_MIN = 150; // ~0 degrees
const int SERVO_PULSE_MID = 375; // ~90 degrees (Neutral driving)
const int SERVO_PULSE_MAX = 600; // ~180 degrees

// Speeds (0 - 255)
const int SPEED_NORMAL = 180;
const int SPEED_TURN   = 160;
const int SPEED_CRAB   = 150;

// Watchdog timeout in milliseconds
const unsigned long COMMAND_TIMEOUT_MS = 500;

// 360 Degree Turn duration in milliseconds (calibrated for rover geometry)
const unsigned long TURN_360_DURATION_MS = 2200;

// Crab Walk step duration
const unsigned long CRAB_STEP_DURATION_MS = 1200;

// --- STATE VARIABLES ---
enum RoverMode { MODE_GESTURE, MODE_MANUAL };
RoverMode currentMode = MODE_GESTURE;

bool isArmed = false;
bool isMoving = false;
char currentCommand = 'S';
unsigned long lastCommandTime = 0;

// Non-blocking action states
enum ActionState { IDLE, EXECUTING_TURN_360, EXECUTING_CRAB_WALK };
ActionState activeAction = IDLE;
unsigned long actionStartTime = 0;
int crabWalkPhase = 0;

// --- PCA9685 DIRECT I2C HELPER FUNCTIONS ---

void initPCA9685() {
  Wire.begin();
  // Reset PCA9685
  Wire.beginTransmission(PCA9685_ADDR);
  Wire.write(0x00); // MODE1 register
  Wire.write(0x00); // Normal mode
  Wire.endTransmission();
  delay(5);

  // Set PWM frequency to 50Hz (prescale = 25MHz / (4096 * 50Hz) - 1 ≈ 121)
  uint8_t prescale = 121;
  Wire.beginTransmission(PCA9685_ADDR);
  Wire.write(0x00);
  Wire.write(0x10); // Sleep mode to set prescale
  Wire.endTransmission();

  Wire.beginTransmission(PCA9685_ADDR);
  Wire.write(0xFE); // PRE_SCALE register
  Wire.write(prescale);
  Wire.endTransmission();

  Wire.beginTransmission(PCA9685_ADDR);
  Wire.write(0x00);
  Wire.write(0xA1); // Auto-increment enabled, restart
  Wire.endTransmission();
  delay(5);
}

void setPCA9685PWM(uint8_t channel, uint16_t on, uint16_t off) {
  Wire.beginTransmission(PCA9685_ADDR);
  Wire.write(0x06 + 4 * channel);
  Wire.write(on & 0xFF);
  Wire.write(on >> 8);
  Wire.write(off & 0xFF);
  Wire.write(off >> 8);
  Wire.endTransmission();
}

void setServoAngle(uint8_t channel, int degrees) {
  degrees = constrain(degrees, 0, 180);
  uint16_t pulse = map(degrees, 0, 180, SERVO_PULSE_MIN, SERVO_PULSE_MAX);
  setPCA9685PWM(channel, 0, pulse);
}

void setAllLegServos(int angleFL, int angleFR, int angleRL, int angleRR) {
  setServoAngle(SERVO_FRONT_LEFT, angleFL);
  setServoAngle(SERVO_FRONT_RIGHT, angleFR);
  setServoAngle(SERVO_REAR_LEFT, angleRL);
  setServoAngle(SERVO_REAR_RIGHT, angleRR);
}

// Set all servos to default driving stance
void setNeutralLegPosition() {
  setAllLegServos(90, 90, 90, 90);
}

// --- BTS7960 MOTOR DRIVE PRIMITIVES ---

void setLeftMotors(int speed) {
  if (speed > 0) {
    analogWrite(PIN_L_RPWM, constrain(speed, 0, 255));
    analogWrite(PIN_L_LPWM, 0);
  } else if (speed < 0) {
    analogWrite(PIN_L_RPWM, 0);
    analogWrite(PIN_L_LPWM, constrain(-speed, 0, 255));
  } else {
    analogWrite(PIN_L_RPWM, 0);
    analogWrite(PIN_L_LPWM, 0);
  }
}

void setRightMotors(int speed) {
  if (speed > 0) {
    analogWrite(PIN_R_RPWM, constrain(speed, 0, 255));
    analogWrite(PIN_R_LPWM, 0);
  } else if (speed < 0) {
    analogWrite(PIN_R_RPWM, 0);
    analogWrite(PIN_R_LPWM, constrain(-speed, 0, 255));
  } else {
    analogWrite(PIN_R_RPWM, 0);
    analogWrite(PIN_R_LPWM, 0);
  }
}

// --- ROVER MOTION CONTROLS ---

void stopRover() {
  setLeftMotors(0);
  setRightMotors(0);
  isMoving = false;
  currentCommand = 'S';
  digitalWrite(PIN_LED, LOW);
}

void moveForward(int speed = SPEED_NORMAL) {
  if (!isArmed) return;
  setLeftMotors(speed);
  setRightMotors(speed);
  isMoving = true;
  digitalWrite(PIN_LED, HIGH);
}

void moveBackward(int speed = SPEED_NORMAL) {
  if (!isArmed) return;
  setLeftMotors(-speed);
  setRightMotors(-speed);
  isMoving = true;
  digitalWrite(PIN_LED, HIGH);
}

void turnLeft(int speed = SPEED_TURN) {
  if (!isArmed) return;
  setLeftMotors(-speed);
  setRightMotors(speed);
  isMoving = true;
  digitalWrite(PIN_LED, HIGH);
}

void turnRight(int speed = SPEED_TURN) {
  if (!isArmed) return;
  setLeftMotors(speed);
  setRightMotors(-speed);
  isMoving = true;
  digitalWrite(PIN_LED, HIGH);
}

// Initiate non-blocking 360° Turn sequence
void startTurn360() {
  if (!isArmed) return;
  activeAction = EXECUTING_TURN_360;
  actionStartTime = millis();
  setNeutralLegPosition();
  turnRight(SPEED_TURN);
  SERIAL_PORT.println(F("OK:START_TURN_360"));
}

// Initiate non-blocking Crab Walk sequence
void startCrabWalk() {
  if (!isArmed) return;
  activeAction = EXECUTING_CRAB_WALK;
  actionStartTime = millis();
  crabWalkPhase = 0;
  // Articulate servos for diagonal lateral stride
  setAllLegServos(45, 135, 135, 45);
  setLeftMotors(SPEED_CRAB);
  setRightMotors(-SPEED_CRAB);
  isMoving = true;
  SERIAL_PORT.println(F("OK:START_CRAB_WALK"));
}

// Non-blocking update for sequences
void updateActiveActions() {
  unsigned long now = millis();

  if (activeAction == EXECUTING_TURN_360) {
    if (now - actionStartTime >= TURN_360_DURATION_MS) {
      stopRover();
      activeAction = IDLE;
      SERIAL_PORT.println(F("OK:TURN_360_COMPLETE"));
    }
  } else if (activeAction == EXECUTING_CRAB_WALK) {
    if (crabWalkPhase == 0 && (now - actionStartTime >= CRAB_STEP_DURATION_MS / 2)) {
      // Phase 2: Reverse articulation for fluid gait
      crabWalkPhase = 1;
      setAllLegServos(135, 45, 45, 135);
      setLeftMotors(-SPEED_CRAB);
      setRightMotors(SPEED_CRAB);
    } else if (now - actionStartTime >= CRAB_STEP_DURATION_MS) {
      stopRover();
      setNeutralLegPosition();
      activeAction = IDLE;
      SERIAL_PORT.println(F("OK:CRAB_WALK_COMPLETE"));
    }
  }
}

// --- COMMAND EXECUTION ---

void executeCommand(char cmd) {
  lastCommandTime = millis();
  currentCommand = cmd;

  switch (cmd) {
    case 'F': // Forward
      if (activeAction == IDLE) moveForward();
      break;

    case 'B': // Backward
      if (activeAction == IDLE) moveBackward();
      break;

    case 'L': // Turn Left
      if (activeAction == IDLE) turnLeft();
      break;

    case 'R': // Turn Right
      if (activeAction == IDLE) turnRight();
      break;

    case 'S': // Stop
      activeAction = IDLE;
      stopRover();
      setNeutralLegPosition();
      break;

    case 'T': // 360° Turn (One-shot)
      if (activeAction == IDLE) startTurn360();
      break;

    case 'C': // Crab Walk
      if (activeAction == IDLE) startCrabWalk();
      break;

    case 'A': // Arm Rover
      isArmed = true;
      SERIAL_PORT.println(F("OK:ARMED"));
      break;

    case 'D': // Disarm Rover
      isArmed = false;
      stopRover();
      SERIAL_PORT.println(F("OK:DISARMED"));
      break;

    case 'E': // Emergency Stop
      isArmed = false;
      activeAction = IDLE;
      stopRover();
      SERIAL_PORT.println(F("OK:ESTOP"));
      break;

    case 'M': // Manual Mode
      currentMode = MODE_MANUAL;
      SERIAL_PORT.println(F("OK:MODE_MANUAL"));
      break;

    case 'G': // Gesture Mode
      currentMode = MODE_GESTURE;
      SERIAL_PORT.println(F("OK:MODE_GESTURE"));
      break;

    case 'P': // Ping / Link Handshake from ESP32
      SERIAL_PORT.println(F("OK:P"));
      break;

    default:
      // Unknown command: safely ignore
      break;
  }
}

// --- SETUP & MAIN LOOP ---

void setup() {
  // Initialize Serial
  SERIAL_PORT.begin(9600);

  // Initialize Motor Driver Pins
  pinMode(PIN_L_RPWM, OUTPUT);
  pinMode(PIN_L_LPWM, OUTPUT);
  pinMode(PIN_L_EN,   OUTPUT);

  pinMode(PIN_R_RPWM, OUTPUT);
  pinMode(PIN_R_LPWM, OUTPUT);
  pinMode(PIN_R_EN,   OUTPUT);

  pinMode(PIN_LED, OUTPUT);

  // Enable BTS7960 Drivers
  digitalWrite(PIN_L_EN, HIGH);
  digitalWrite(PIN_R_EN, HIGH);

  // Stop motors initially
  stopRover();

  // Initialize PCA9685 Servo Controller
  initPCA9685();
  setNeutralLegPosition();

  lastCommandTime = millis();
  SERIAL_PORT.println(F("SYSTEM:STAIROVER_NANO_READY"));
}

void loop() {
  // 1. Process incoming Serial commands
  while (SERIAL_PORT.available() > 0) {
    char incoming = (char)SERIAL_PORT.read();
    if (incoming == '\r' || incoming == '\n' || incoming == ' ') {
      continue;
    }
    executeCommand(incoming);
  }

  // 2. Non-blocking sequential action execution
  updateActiveActions();

  // 3. Hardware Watchdog Check
  // If moving and no refresh received within COMMAND_TIMEOUT_MS -> stop immediately!
  if (isMoving && (activeAction == IDLE)) {
    if (millis() - lastCommandTime > COMMAND_TIMEOUT_MS) {
      stopRover();
      SERIAL_PORT.println(F("WATCHDOG:TIMEOUT->STOP"));
    }
  }

  // Brief delay to avoid CPU lockup
  delay(5);
}
