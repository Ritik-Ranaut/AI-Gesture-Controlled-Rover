<<<<<<< HEAD
# 🤖 AI Hand Gesture Controlled RC Car

Control an RC car **without touching a remote!** 🚗💨
This project uses **AI-based hand gesture recognition** with a webcam to detect hand movements and wirelessly control an RC car through an **ESP32**.

## ✨ Features

* 🖐️ Real-time hand gesture detection
* 🚗 Forward, Backward, Left & Right control
* 🛑 Gesture-based emergency stop
* 📡 Wireless ESP32 communication
* ⚡ Low-latency gesture-to-motor control
* 💻 Interactive React dashboard

## 🛠️ Tech Stack

**React.js • AI/Computer Vision • ESP32 • L298N • DC Motors • Wi-Fi**

## 🎮 Controls

| Gesture     | Action     |
| ----------- | ---------- |
| 👆 UP       | Forward    |
| 👇 DOWN     | Backward   |
| 👈 LEFT     | Turn Left  |
| 👉 RIGHT    | Turn Right |
| ✋ OPEN PALM | Stop       |

## 🚀 How It Works

```text
Webcam
  ↓
Hand Gesture Recognition
  ↓
React Dashboard
  ↓ Wi-Fi
ESP32
  ↓
L298N Motor Driver
  ↓
🚗 RC Car
```

## 🎯 Goal

To create a **fast, intuitive, and contactless robotic control system** using computer vision and IoT technology.

---

⭐ If you find this project interesting, consider giving it a star!
=======
# STAIROVER: Hand-Gesture Controlled Stair-Climbing Rover System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/react-19-cyan.svg)](https://react.dev/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-1.0-orange.svg)](https://developers.google.com/mediapipe)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-emerald.svg)](https://fastapi.tiangolo.com/)
[![Arduino](https://img.shields.io/badge/Arduino-Nano-teal.svg)](https://www.arduino.cc/)

A complete, production-grade robotics application for controlling a 6-wheel stair-climbing rover using computer-vision hand gestures captured from a laptop webcam. The system integrates real-time geometric landmark classification, multi-frame stabilization, dual safety watchdogs, wireless HC-05 Bluetooth communication, Arduino Nano hardware motor/servo control, an ESP32-CAM live Wi-Fi video stream, and a modern React mission-control dashboard.

---

## 1. System Architecture

```text
                  ┌────────────────────────┐
                  │       USER HAND        │
                  └───────────┬────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  Laptop Webcam  │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ OpenCV 4 +      │
                     │ MediaPipe Tasks │
                     └────────┬────────┘
                              │ 21 3D Landmarks
                              ▼
                     ┌─────────────────┐
                     │ Gesture         │
                     │ Classifier      │ (Forward, Backward, Left, Right,
                     └────────┬────────┘  Stop, Crab Walk, 360° Turn)
                              │
                              ▼
                     ┌─────────────────┐
                     │ Safety Command  │ (3-Frame Confirmation, Turn Cooldown,
                     │ Controller      │  Startup Safe Arming, 500ms Watchdog)
                     └────────┬────────┘
                              │ ASCII Commands (F, B, L, R, C, T, S)
               ┌──────────────┴──────────────┐
               │                             │ WebSocket Telemetry & Video
               ▼                             ▼
       ┌───────────────┐           ┌─────────────────────────────┐
       │ HC-05 BT /    │           │ React Mission Control Deck  │
       │ USB Serial    │           │                             │
       └───────┬───────┘           │  • Dual Camera View         │
               │                   │  • Real-time Confidence     │
               ▼                   │  • Tactile 8-Way Controls   │
       ┌───────────────┐           │  • Manual Keyboard Overrides│
       │ Arduino Nano  │           │  • Diagnostics & Logs       │
       │ Controller    │           │  • Big Emergency Stop       │
       └───────┬───────┘           └──────────────▲──────────────┘
               │                                  │
       ┌───────┴───────┐                          │ Wi-Fi MJPEG Stream
       ▼               ▼                          │
 ┌───────────┐   ┌───────────┐           ┌────────┴─────────┐
 │  BTS7960  │   │  PCA9685  │           │    ESP32-CAM     │
 │  Motors   │   │  Servos   │           │   Rover Camera   │
 └─────┬─────┘   └─────┬─────┘           └──────────────────┘
       └───────┬───────┘
               ▼
     STAIR-CLIMBING ROVER
```

---

## 2. Default Gesture Mapping

| Gesture | Icon | Command Character | Action on Rover | Cooldown / Timing |
| :--- | :---: | :---: | :--- | :--- |
| **Index Finger UP** | ☝️ | `F` | Drive Forward | Continuous (watchdog guarded) |
| **Index Finger DOWN** | 👇 | `B` | Drive Backward | Continuous (watchdog guarded) |
| **Index Pointing LEFT** | 👈 | `L` | Skid-steer Left | Continuous (watchdog guarded) |
| **Index Pointing RIGHT**| 👉 | `R` | Skid-steer Right | Continuous (watchdog guarded) |
| **Open Palm** | ✋ | `S` | Instant Full Stop | Immediate |
| **Rock-on / I-Love-You**| 🤟 | `C` | Coordinated Crab Walk | 1.0s cooldown |
| **Closed Fist** | ✊ | `T` | 360° Pivot Turn Sequence | 2.0s cooldown (one-shot) |

> **Customization Note:** All gesture mappings are defined centrally in `gesture-service/config.py` and can be adjusted dynamically from the UI settings panel.

---

## 3. Hardware Requirements & Wiring

### Hardware Checklist:
- **Arduino Nano** (ATmega328P 16MHz) — Main rover controller
- **Normal ESP32 Development Board** (ESP-WROOM-32 / NodeMCU-32S) — Dedicated wireless communication bridge
- **2x BTS7960 43A Motor Drivers** — Controls 6 high-torque DC drive motors
- **PCA9685 16-Channel 12-bit PWM Driver** — Controls stair-climbing articulated leg servos
- **4x Metal-Gear Servos** (MG996R or DS3218) — Leg lifting & stair ascension
- **HC-05 Bluetooth Module** — Wireless UART fallback link (or USB tether)
- **ESP32-CAM (AI-Thinker)** — Dedicated Wi-Fi live video streamer
- **Step-down Buck Converter (5V / 6V 5A)** — Supplies stable power to servos & logic
- **3S LiPo Battery (11.1V - 12.6V, 2200mAh+)** — High-drain motor power

### Wiring Summary:
- **Normal ESP32 $\leftrightarrow$ Arduino Nano:** ESP32 GPIO 17 (TX2) $\rightarrow$ Nano D0 (RX); Nano D1 (TX) $\rightarrow$ 1k/2k voltage divider $\rightarrow$ ESP32 GPIO 16 (RX2); Common GND.
- **Arduino $\leftrightarrow$ HC-05 (Optional):** D0 (RX) $\leftarrow$ HC-05 TX; D1 (TX) $\rightarrow$ 1k/2k voltage divider $\rightarrow$ HC-05 RX; VCC $\rightarrow$ 5V, GND $\rightarrow$ GND.
- **Arduino $\leftrightarrow$ PCA9685:** A4 $\rightarrow$ SDA; A5 $\rightarrow$ SCL; VCC $\rightarrow$ 5V, GND $\rightarrow$ GND; External V+ $\rightarrow$ Buck 6V.
- **Arduino $\leftrightarrow$ BTS7960 Left:** D5 $\rightarrow$ RPWM; D6 $\rightarrow$ LPWM; D7 $\rightarrow$ R_EN & L_EN; B+/B- $\rightarrow$ 12V LiPo.
- **Arduino $\leftrightarrow$ BTS7960 Right:** D9 $\rightarrow$ RPWM; D10 $\rightarrow$ LPWM; D8 $\rightarrow$ R_EN & L_EN; B+/B- $\rightarrow$ 12V LiPo.

*Detailed schematics and pin connection tables are located in [docs/wiring_guide.md](file:///r:/StairClimbingRoverControler/docs/wiring_guide.md).*

---

## 4. Software Requirements

- **Operating System:** Windows 10/11
- **Python:** 3.10 to 3.12 (Tested on Python 3.12)
- **Node.js:** v18+ (Tested on v22.12.0)
- **Arduino IDE:** 1.8.x or 2.x
- **VS Code** with Python and ESLint extensions

---

## 5. Installation & Setup (Windows / VS Code)

### Step 1: Open Project in VS Code
Open VS Code in this directory:
```powershell
code r:\StairClimbingRoverControler
```

### Step 2: Python Gesture Service Setup
Open a PowerShell terminal in VS Code:
```powershell
cd r:\StairClimbingRoverControler\gesture-service
python -m pip install -r requirements.txt
```

Verify the installation and test suite:
```powershell
cd r:\StairClimbingRoverControler
python -m pytest tests/ -v
```
*(All 23 automated tests should pass with 100% success).*

### Step 3: React Dashboard Setup
Open a second PowerShell terminal in VS Code:
```powershell
cd r:\StairClimbingRoverControler\frontend
npm install
npm run build
```

### Step 4A: Flash Arduino Nano Firmware
1. Open the Arduino IDE.
2. Open `r:\StairClimbingRoverControler\arduino\stair_rover\stair_rover.ino`.
3. Select **Tools $\rightarrow$ Board $\rightarrow$ Arduino Nano**.
4. Select **Tools $\rightarrow$ Processor $\rightarrow$ ATmega328P (or Old Bootloader)**.
5. Select your Arduino COM Port.
6. *(Important)* If ESP32/HC-05 is connected to pins 0/1, unplug RX/TX jumper wires during uploading, then reconnect them after upload completes.
7. Click **Upload**.

### Step 4B: Flash Normal ESP32 Wireless Controller
1. Open `r:\StairClimbingRoverControler\esp32\rover_communication\rover_communication.ino` in Arduino IDE.
2. Select **Tools $\rightarrow$ Board $\rightarrow$ ESP32 Dev Module** (or your exact ESP32 model).
3. Select the ESP32 COM Port.
4. The default is direct AP mode: the ESP32 creates `ESP32-Rover` with password `rover12345` at `192.168.4.1`. No router credentials are required.
5. For router mode instead, set `WIFI_MODE_AP` to `false`, enter `WIFI_SSID` and `WIFI_PASSWORD`, and leave `USE_STATIC_IP` as `false` for DHCP.
6. Connect the servo signal to GPIO 18 and share ground between the servo power supply and ESP32. Power the servo from an appropriate external 5V supply; do not draw servo current from the ESP32 3.3V pin.
7. Click **Upload**.
8. Open Serial Monitor at 115200 baud. In router mode, use the printed DHCP address; in AP mode, use `192.168.4.1`.
   ```text
  Wi-Fi Mode: STA
  ESP32 IP: 192.168.x.x
  Gateway: 192.168.x.1
  HTTP Server Started on port 80
   ```

### Direct ESP32 test
1. Connect the laptop to `ESP32-Rover` using password `rover12345`.
2. Open `http://192.168.4.1/` in a browser.
3. Test `/status`, `/wifi`, and the 0, 45, 90, 135, and 180 degree buttons before opening React.

### React ESP32 configuration
The dashboard stores the target in browser `localStorage` under `esp32_ip`. Enter the address printed by the ESP32 in **ESP32 Wi-Fi Link**, save it, and press **Test Connection**. The direct request has a four-second timeout and reports the actual error.

Optional frontend environment defaults can be placed in `frontend/.env`:
```text
VITE_ESP32_IP=192.168.4.1
VITE_ESP32_PORT=80
VITE_ESP32_CAM_URL=http://camera-address:81/stream
```

Do not use the laptop IP in the ESP32 field. In router mode, the laptop and ESP32 normally share the router subnet; in AP mode, the laptop receives a `192.168.4.x` address and the ESP32 is `192.168.4.1`.

### Step 5: Flash ESP32-CAM Video Streamer
1. Open `r:\StairClimbingRoverControler\esp32-cam\camera_stream\camera_stream.ino`.
2. Enter your local Wi-Fi network SSID and Password:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Select Board: **AI Thinker ESP32-CAM**.
4. Connect GPIO 0 to GND, plug in FTDI programmer, press Reset, and click **Upload**.
5. Disconnect GPIO 0 from GND, open Serial Monitor at 115200 baud, and press Reset.
6. Note the printed IP address (e.g. `http://192.168.1.100:81/stream`).

---

## 6. Running the System

### 1. Launch the Python Gesture & Telemetry Service
In Terminal 1:
```powershell
cd r:\StairClimbingRoverControler\gesture-service
python app.py
```
*The service will start on `http://localhost:8001`. You will see:*
- `[INFO] MediaPipe Tasks HandLandmarker initialized.`
- `[INFO] Connecting to HC-05 / Mock Transport...`
- `[INFO] Camera started at 640x480.`

### 2. Launch the React Mission Control Dashboard
In Terminal 2:
```powershell
cd r:\StairClimbingRoverControler\frontend
npm run dev
```
*Open `http://localhost:5173` in your browser (Chrome or Edge recommended).*

---

## 7. Operational Workflow

1. **Safe Startup (Disarmed):** On startup, the rover is automatically **DISARMED**. You can test gestures in front of the camera and inspect recognition on screen without driving the physical motors.
2. **Arm the Rover:** Click the green **ENABLE ROVER** button on the dashboard. The status badge will switch to **ROVER ARMED**.
3. **Control via Hand Gestures:**
   - Show **☝️ One finger up**: Rover moves **FORWARD** (`F`).
   - Show **👇 Finger down**: Rover moves **BACKWARD** (`B`).
   - Point **👉 Right**: Rover turns **RIGHT** (`R`).
   - Point **👈 Left**: Rover turns **LEFT** (`L`).
   - Open **✋ Palm**: Rover immediately **STOPS** (`S`).
   - Form **🤟 Rock-on**: Rover triggers **CRAB WALK** (`C`).
   - Clench **✊ Fist**: Rover triggers a single **360° TURN** (`T`) with automatic stop and 2-second cooldown.
4. **Remove Hand:** If you remove your hand from the webcam view, the rover automatically halts within 150ms.
5. **Emergency Stop:** Hit the large red **EMERGENCY STOP** button or press **ESC** at any time to instantly lock the motors.
6. **Manual Keyboard Override:** Toggle to **MANUAL MODE** and control using **W / A / S / D / C / T / SPACE**.

---

## 8. Systematic Testing Checklist (ESP32 Wireless Order)

Follow this structured testing procedure:

- [x] **Test 1 (ESP32 Boot & Wi-Fi Start):**
  Power on the Normal ESP32. In Serial Monitor or Wi-Fi settings, verify AP SSID `STAIROVER` appears with IP `192.168.4.1` (or local station IP).
- [x] **Test 2 (Laptop Connects to ESP32):**
  Connect laptop Wi-Fi to `STAIROVER`. Open dashboard and verify **Laptop $\rightarrow$ ESP32: PASS**.
- [x] **Test 3 (ESP32 Direct Test Buttons & Arduino Link):**
  Click **TEST CONNECTION** and verify **ESP32 $\rightarrow$ Arduino: PASS**. Use the Direct Test Deck buttons (`F`, `B`, `L`, `R`, `C`, `T`, `S`) to verify UART transmission.
- [x] **Test 4 (Motor & Servo Movements on Bench Stand):**
  Elevate the rover with wheels off the ground. Arm the rover and verify `F` drives forward, `B` reverse, `L` left, `R` right, `C` crab articulation, `T` 360° pivot, and `S` stop.
- [x] **Test 5 (Full Hand Gesture Pipeline):**
  Enable Gesture Mode. Show ☝️ (Forward), 👇 (Backward), 👉 (Right), 👈 (Left), ✋ (Stop), 🤟 (Crab), and ✊ (360° Turn). Verify the command flows: `Gesture → Command → ESP32 → Arduino Nano`.
- [x] **Test 6 (Wi-Fi Disconnection Watchdog):**
  While rover is moving, disconnect Wi-Fi or turn off laptop Wi-Fi $\rightarrow$ ESP32 watchdog trips within 500ms and immediately sends `S` to Arduino.
- [x] **Test 7 (Gesture Application Shutdown):**
  Close the Python gesture application $\rightarrow$ ESP32 command timeout trips and halts the rover immediately.
- [x] **Test 8 (Hand Removal Safe Stop):**
  Remove your hand from the webcam field of view $\rightarrow$ Gesture controller detects hand loss and issues `STOP` within 150ms.

---

## 9. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"Webcam Feed Offline"** | Camera occupied or wrong index | Change `camera_index` (0, 1, or 2) in Settings modal. Ensure no other app (Zoom, Teams) is locking the webcam. |
| **"Bluetooth connection failed"** | HC-05 not paired in Windows | Open Windows Bluetooth settings, pair `HC-05` (PIN `1234`), check Device Manager for assigned Outgoing COM port (e.g. `COM7`), and select it in Settings. |
| **ESP32-CAM stream offline** | IP address mismatch | Check Arduino Serial Monitor for the ESP32-CAM IP and update the URL in Settings (`http://<IP>:81/stream`). |
| **Low Gesture Confidence** | Poor lighting or cluttered background | Ensure good lighting on the hand. Adjust Confidence Threshold slider in Settings from 80% to 75%. |
| **Motors do not move** | Rover is Disarmed | Click **ENABLE ROVER** in the top banner or Emergency Stop panel. |

---

## 10. Safety Instructions

1. **Bench Testing First:** Always test the rover on an elevated stand with wheels off the ground before placing it on stairs or floors.
2. **Watchdog Verification:** Verify the built-in LED on the Arduino turns OFF when the laptop is paused.
3. **Emergency Stop Proximity:** Keep one hand near the physical power switch or dashboard E-Stop button during initial stair-climbing trials.
>>>>>>> a68c7a2 (updations)
