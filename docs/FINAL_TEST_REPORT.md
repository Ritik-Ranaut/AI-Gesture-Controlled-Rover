# Final Test Report

Application: STAIROVER Hand-Gesture Controlled Stair-Climbing Rover System  
Testing Date: 2026-09-14  
Environment: Windows, Python 3.12.5, pytest 9.1.1, Node/Vite frontend, mock transport, local webcam available  

Total Tests: 27 automated tests, plus live API/frontend probes  
Passed: 27 automated tests; frontend build; backend startup/import; live safety API probe  
Failed: 0 automated tests  
Fixed: 5 software bugs  
Remaining: 1 medium software integration gap; physical rover path remains unverified  

## Summary

Critical Bugs: 2 found, 2 fixed  
High Bugs: 2 found, 2 fixed  
Medium Bugs: 2 found, 1 fixed, 1 remaining  
Low Bugs: 0 found  

Software Test Status: PASS for automated Python tests, backend startup, frontend build, mock command safety, gesture classifier fixtures, and local API safety transitions.  
Hardware Test Status: NOT EXECUTED. **PHYSICAL HARDWARE TEST REQUIRED** for ESP32, Arduino Nano, UART, motors, servos, HC-05, ESP32-CAM, and Wi-Fi range/reconnection.  

Final Status: SOFTWARE REGRESSION PASS WITH HARDWARE VALIDATION REQUIRED

## Feature Test Table

| Feature | Test Result | Status |
|---|---|---|
| Application startup | Backend imported and started; default telemetry was disarmed with command `S` | PASS |
| Gesture detection | MediaPipe model initialized; classifier tests covered forward, backward, left, right, stop, crab, turn, and empty landmarks | PASS |
| Command system | Mapping, stabilization, invalid-command fallback, cooldown, and watchdog tests passed | PASS |
| ESP32 communication | Mocked Wi-Fi transport tests passed; physical bridge unavailable | PASS (software) / HARDWARE TEST REQUIRED |
| Arduino communication | Protocol inspected; no physical Nano or UART acknowledgment available | HARDWARE TEST REQUIRED |
| Manual control | Controller command mapping tests and frontend build passed; browser interaction automation is not configured | PASS (software) |
| Emergency stop | Unit test and live API probe ended with disarmed, E-stop active, command `S` | PASS (software) |
| Camera | Camera worker initialized and MJPEG endpoint was reachable; gesture accuracy and ESP32-CAM stream were not physically measured | PASS (software) / HARDWARE TEST REQUIRED |
| Error handling | Transport failure tests, unreachable Wi-Fi tests, invalid command probe, and safe fallback paths passed | PASS |

## Tests Performed

- `python -m pytest tests/ -v`: 27 passed.
- `python -m compileall -q gesture-service tests`: passed.
- `npm run build` in `frontend`: passed; Vite transformed 1,874 modules.
- Backend import and direct startup: passed; MediaPipe Tasks initialized.
- Live `GET /api/status`: passed with safe default state.
- Live arm, invalid command, and E-stop sequence: ended safely with `is_armed=false`, `estop_active=true`, `active_command=S`.
- Frontend dev server probe on port 5173: passed.

## Performance and Security

Observed startup included MediaPipe initialization and was approximately several seconds on the local machine; no formal CPU, RAM, FPS, latency, or leak benchmark was run. The service reports FPS and latency telemetry for future hardware benchmarking.

No authentication is implemented, and CORS is configured as `allow_origins=["*"]` with credentials enabled. This is acceptable only for a trusted local network and is a security risk for deployment. The application has no database or authentication integration to test.

FastAPI emitted a deprecation warning for `on_event`; migrating to lifespan handlers is recommended but was outside the safety fixes in this run.