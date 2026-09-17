# Hardware Wiring Guide: Stair-Climbing Rover

This document provides complete, step-by-step wiring diagrams and pin connections for the Arduino Nano main controller, PCA9685 servo driver, BTS7960 high-power DC motor drivers, HC-05 Bluetooth module, power distribution, and ESP32-CAM.

---

## 1. System Power Architecture

```
                    ┌────────────────────────────┐
                    │ 3S LiPo Battery (11.1-12V) │
                    └──────────────┬─────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                   │
         ▼                                                   ▼
┌──────────────────┐                              ┌───────────────────┐
│ High-Current Bus │                              │ Buck Converter    │
│ (12V DC Motors)  │                              │ (Step-down to 5V) │
└────────┬─────────┘                              └─────────┬─────────┘
         │                                                  │
         ├──────────────────────┐             ┌─────────────┴─────────────┐
         ▼                      ▼             ▼             ▼             ▼
   BTS7960 Left          BTS7960 Right   Arduino Nano    PCA9685 (V+)  ESP32-CAM
   (B+ / B- pins)        (B+ / B- pins)  (VIN pin)      (Servo Power)  (5V pin)
```

> [!CAUTION]
> **Ground Loop & Common Ground:** All components (Arduino Nano, BTS7960 drivers, PCA9685 driver, HC-05, and Buck converter) **must share a common GND**.
> Never power high-torque leg servos directly from the Arduino 5V pin! Power servos via the PCA9685 external screw terminal connected to the buck converter.

---

## 2. Arduino Nano Pin Assignments

| Arduino Nano Pin | Connected Component | Function / Signal |
| :--- | :--- | :--- |
| **D0 (RX)** | HC-05 Bluetooth TX | Serial Receive (Hardware UART) |
| **D1 (TX)** | HC-05 Bluetooth RX | Serial Transmit (via 2:3 voltage divider) |
| **D5 (PWM)** | BTS7960 Left RPWM | Left Motors Forward PWM |
| **D6 (PWM)** | BTS7960 Left LPWM | Left Motors Reverse PWM |
| **D7 (DO)** | BTS7960 Left R_EN & L_EN | Left Driver Enable |
| **D8 (DO)** | BTS7960 Right R_EN & L_EN | Right Driver Enable |
| **D9 (PWM)** | BTS7960 Right RPWM | Right Motors Forward PWM |
| **D10 (PWM)**| BTS7960 Right LPWM | Right Motors Reverse PWM |
| **A4 (SDA)** | PCA9685 SDA | I2C Data Line |
| **A5 (SCL)** | PCA9685 SCL | I2C Clock Line |
| **D13** | Built-in LED | Motion / Command Activity Status |
| **5V** | Logic Power Bus | Logic Power for PCA9685 (VCC) & HC-05 (VCC) |
| **GND** | Common Ground Bus | System Common Ground |

---

## 3. BTS7960 Motor Driver Wiring

Two BTS7960 43A H-bridge drivers control the 6 DC drive motors (3 motors wired in parallel on the left side, 3 on the right side).

### Left Driver (BTS7960 #1):
- **VCC** $\rightarrow$ Arduino 5V
- **GND** $\rightarrow$ System Common GND
- **R_EN** $\rightarrow$ Arduino D7 (tied with L_EN)
- **L_EN** $\rightarrow$ Arduino D7 (tied with R_EN)
- **RPWM** $\rightarrow$ Arduino D5 (PWM)
- **LPWM** $\rightarrow$ Arduino D6 (PWM)
- **B+** $\rightarrow$ +12V Battery terminal
- **B-** $\rightarrow$ - Battery Ground
- **M+ / M-** $\rightarrow$ Left 3 DC Motors in parallel

### Right Driver (BTS7960 #2):
- **VCC** $\rightarrow$ Arduino 5V
- **GND** $\rightarrow$ System Common GND
- **R_EN** $\rightarrow$ Arduino D8 (tied with L_EN)
- **L_EN** $\rightarrow$ Arduino D8 (tied with R_EN)
- **RPWM** $\rightarrow$ Arduino D9 (PWM)
- **LPWM** $\rightarrow$ Arduino D10 (PWM)
- **B+** $\rightarrow$ +12V Battery terminal
- **B-** $\rightarrow$ - Battery Ground
- **M+ / M-** $\rightarrow$ Right 3 DC Motors in parallel

---

## 4. PCA9685 16-Channel Servo Driver Wiring

The PCA9685 articulates the 4 stair-climbing rocker-bogie leg servos.

### Control Signals:
- **VCC (Logic)** $\rightarrow$ Arduino 5V
- **GND** $\rightarrow$ Arduino GND
- **SDA** $\rightarrow$ Arduino A4
- **SCL** $\rightarrow$ Arduino A5
- **OE** $\rightarrow$ Left open (active low, pulled down on board)

### Servo Power:
- **V+ (Screw Terminal)** $\rightarrow$ Buck Converter Output (+5.5V or +6.0V, 5A rated)
- **GND (Screw Terminal)** $\rightarrow$ Buck Converter Output GND

### Servo Channels:
- **Channel 0** $\rightarrow$ Front-Left Climbing Leg Servo
- **Channel 1** $\rightarrow$ Front-Right Climbing Leg Servo
- **Channel 2** $\rightarrow$ Rear-Left Climbing Leg Servo
- **Channel 3** $\rightarrow$ Rear-Right Climbing Leg Servo

---

## 5. HC-05 Bluetooth Module Wiring

The HC-05 Bluetooth module acts as the wireless serial bridge between the Python gesture service and the Arduino Nano.

| HC-05 Pin | Arduino Nano Pin | Notes |
| :--- | :--- | :--- |
| **VCC** | 5V | Powers the HC-05 onboard 3.3V LDO |
| **GND** | GND | Common Ground |
| **TXD** | D0 (RX) | 3.3V logic is directly recognized by Nano 5V TTL |
| **RXD** | D1 (TX) | **Voltage Divider Required:** 1kΩ from Nano TX to HC-05 RX, and 2kΩ from HC-05 RX to GND |
| **STATE** | Not connected | Optional connection status indicator |
| **EN / KEY**| Not connected | Leave floating for normal data mode |

---

## 6. ESP32-CAM Wiring (Standalone Live Video)

The ESP32-CAM operates independently on Wi-Fi for live video streaming.

- **5V Pin** $\rightarrow$ Buck Converter +5V (Needs min 2A peak during Wi-Fi transmission)
- **GND Pin** $\rightarrow$ System Common GND
- **GPIO 0** $\rightarrow$ Connected to GND during firmware upload; disconnected during normal boot
- **U0R / U0T** $\rightarrow$ Connected to USB-to-UART FTDI programmer during flashing only

---

## 7. Normal ESP32 Wireless Controller Wiring (Direct Servo Test)

The normal ESP32 development board (e.g., ESP32 Dev Module, NodeMCU-32S, ESP-WROOM-32) serves the HTTP controller and drives the first test servo directly.

### Pin Connections:

| ESP32 Pin | Servo / Supply | Notes / Description |
| :--- | :--- | :--- |
| **GPIO 18** | Servo signal | PWM signal for the one-servo test |
| **GND** | Servo ground and supply ground | All grounds must be common |
| **5V external supply** | Servo V+ | Use a supply sized for the servo; do not use ESP32 3.3V for servo power |

### Dual ESP Subsystem Summary:
- **Normal ESP32:** Handles router DHCP/static IP or AP mode, HTTP diagnostics, and direct GPIO 18 servo testing. The current sketch does not drive rover motors or use the Nano UART.
- **ESP32-CAM:** Completely dedicated to streaming live rover video over Wi-Fi to the dashboard. Does not touch motor or servo lines.
