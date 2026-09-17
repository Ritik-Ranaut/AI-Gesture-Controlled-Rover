# Bug Report

Testing date: 2026-09-14

## BUG-001

Bug ID: BUG-001  
Description: The Python watchdog stopped `T` and `C` actions after the 500 ms continuous-command timeout, before the Arduino's non-blocking action completed.  
Severity: CRITICAL  
Root Cause: The watchdog treated one-shot timed actions as continuous motion.  
Affected File: `gesture-service/command_controller.py`  
Affected Function: `CommandController._watchdog_loop`  
Fix: Added timed-action deadlines matching the firmware action durations; continuous commands retain the normal watchdog timeout.  
Test Performed: `test_timed_turn_is_not_stopped_by_continuous_watchdog` and full regression suite.  
Result: FIXED. The turn remains active beyond 300 ms and is stopped only after its action deadline.

## BUG-002

Bug ID: BUG-002  
Description: Python disarm and emergency stop sent only `S`, leaving the Arduino arm latch enabled.  
Severity: CRITICAL  
Root Cause: The Arduino protocol requires `D` or `E` to clear `isArmed`; `S` only stops motion.  
Affected File: `gesture-service/command_controller.py`  
Affected Function: `disarm_rover`, `emergency_stop`  
Fix: Disarm sends `D`; emergency stop sends `E`.  
Test Performed: `test_disarm_and_estop_clear_physical_arm_latch` and live `/api/estop` probe.  
Result: FIXED in software/mock testing. Physical latch behavior requires hardware validation.

## BUG-003

Bug ID: BUG-003  
Description: A serial or Bluetooth write exception called `disconnect()` while the transport lock was held, causing a deadlock.  
Severity: HIGH  
Root Cause: Both `send_command` methods re-entered a non-reentrant `threading.Lock`.  
Affected File: `gesture-service/transport/serial_transport.py`, `gesture-service/transport/bluetooth.py`  
Affected Function: `send_command`  
Fix: Close and clear the connection inline while the existing lock is held.  
Test Performed: `test_serial_write_failure_releases_connection` for both transports.  
Result: FIXED. Failed writes return `False` and leave no stale connection.

## BUG-004

Bug ID: BUG-004  
Description: The frontend Backward button sent protocol command `S`, which means Stop.  
Severity: HIGH  
Root Cause: The button handler used `S` despite its displayed backward mapping.  
Affected File: `frontend/src/components/RoverControls.jsx`  
Affected Function: Backward button handler  
Fix: The button now sends `B`.  
Test Performed: Frontend production build and source-path review.  
Result: FIXED. Build succeeds.

## BUG-005

Bug ID: BUG-005  
Description: WebSocket settings updates did not reconnect the transport when the ESP32 IP, port, or Wi-Fi endpoint changed.  
Severity: MEDIUM  
Root Cause: The WebSocket handler only considered transport type, COM port, and baud rate.  
Affected File: `gesture-service/app.py`  
Affected Function: `websocket_telemetry`  
Fix: Added all Wi-Fi endpoint keys to the reconnect condition and passed the updated values to `update_transport`.  
Test Performed: Static path verification and full Python regression suite.  
Result: FIXED in the WebSocket update path.

## Remaining Finding

The ESP32 `/command` response currently confirms that bytes were written to UART, not that the Arduino acknowledged receipt. The ESP32-to-Arduino link therefore remains a **PHYSICAL HARDWARE TEST REQUIRED** item and should be strengthened with an explicit command acknowledgment protocol before production deployment.