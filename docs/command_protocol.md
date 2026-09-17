# Command & Communication Protocol Specification

This document details the serial ASCII protocol and WebSocket telemetry exchange between the Python Gesture Service, Arduino Nano, and React Mission Control Dashboard.

---

## 1. Physical / Wireless UART Layer

- **Baud Rate:** `9600` (HC-05 default) or `115200` (USB Serial)
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Line Termination:** `\n` (Newline ASCII 0x0A)

---

## 2. Command Set: Laptop $\rightarrow$ Arduino Nano

Each movement command consists of a single uppercase ASCII character followed by a newline:

| Character | Command Name | Motion Executed by Rover | Execution Mode |
| :---: | :--- | :--- | :--- |
| `F` | **FORWARD** | Left & Right motor banks drive forward at calibrated drive speed. | Continuous (Watchdog guarded) |
| `B` | **BACKWARD** | Left & Right motor banks drive reverse. | Continuous (Watchdog guarded) |
| `L` | **LEFT** | Skid-steer left: Left reverse, Right forward. | Continuous (Watchdog guarded) |
| `R` | **RIGHT** | Skid-steer right: Left forward, Right reverse. | Continuous (Watchdog guarded) |
| `S` | **STOP** | All motor PWM set to 0; all leg servos returned to neutral 90°. | Instantaneous |
| `C` | **CRAB WALK** | Coordinated sequence: articulated leg servos angle 45°, differential counter-drive lateral stride. | Non-blocking timed sequence (1.2s) |
| `T` | **360° TURN** | Non-blocking skid-steer in-place pivot spin for 2.2s, auto-stopping upon completion. | One-shot with 2.0s cooldown |
| `A` | **ARM ROVER** | Enables motion commands; clears safety lock. | State Toggle |
| `D` | **DISARM ROVER**| Disables motion commands; forces immediate motor stop. | State Toggle |
| `E` | **E-STOP** | Immediate Emergency Stop override latch. | Safety Critical |
| `M` | **MANUAL MODE**| Sets Arduino internal mode to manual control. | State Toggle |
| `G` | **GESTURE MODE**| Sets Arduino internal mode to gesture control. | State Toggle |

---

## 3. Acknowledgments & Telemetry: Arduino $\rightarrow$ Laptop

The Arduino echoes received commands and telemetry:

| Packet | Description |
| :--- | :--- |
| `SYSTEM:STAIROVER_NANO_READY` | Sent by Arduino on initial boot. |
| `OK:<CMD>` | Acknowledgment of received command (e.g. `OK:F`, `OK:S`). |
| `OK:START_TURN_360` | Notification that 360° turn sequence started. |
| `OK:TURN_360_COMPLETE` | Notification that 360° turn finished and rover stopped. |
| `OK:START_CRAB_WALK` | Notification that crab walk sequence started. |
| `OK:CRAB_WALK_COMPLETE` | Notification that crab walk finished. |
| `WATCHDOG:TIMEOUT->STOP` | Watchdog tripped because no command was received for >500ms. |

---

## 4. WebSocket Telemetry Packet (Python $\rightarrow$ React Frontend)

Streamed over `/ws/telemetry` at 25-30 Hz:

```json
{
  "mode": "GESTURE",
  "is_armed": true,
  "estop_active": false,
  "active_command": "F",
  "confirmed_gesture": "FORWARD",
  "confidence": 0.94,
  "hand_detected": true,
  "handedness": "Right",
  "orientation": "UP",
  "fps": 31.4,
  "latency_ms": 13.8,
  "finger_states": {
    "thumb": true,
    "index": true,
    "middle": false,
    "ring": false,
    "pinky": false
  },
  "transport": {
    "type": "bluetooth",
    "port": "COM7",
    "baudrate": 9600,
    "connected": true,
    "last_error": ""
  },
  "recent_logs": [
    {
      "command": "F",
      "source": "gesture",
      "confidence": 0.94,
      "timestamp": 1726300456.12,
      "time_str": "11:45:20"
    }
  ]
}
```

---

## 5. Safety Watchdog Timing Constraints

```
Last Command Received
        │
        │ < 500 ms  ──▶ Motor PWM maintained
        ▼
   500 ms Elapsed   ──▶ WATCHDOG TRIPPED!
        │
        ▼
  stopRover()
  (Left PWM = 0, Right PWM = 0, Builtin LED = OFF)
```

1. **Host Python Watchdog:** Sends `S` (STOP) if hand detection is lost for $>150\text{ ms}$ or if command stream pauses for $>500\text{ ms}$.
2. **Arduino Nano Hardware Watchdog:** Independently monitors `millis() - lastCommandTime`. If $>500\text{ ms}$ elapses without a valid character, the Arduino Nano independently halts all motor driver PWM pins to guarantee fail-safe operation even if the laptop crashes, powers off, or goes out of Bluetooth range.
