"""Safety-First Rover Command Controller and Watchdog Manager."""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import deque

from config import RoverConfig, config
from transport import CommandTransport, create_transport
from transport.wifi_transport import WiFiTransport
from gesture_classifier import GestureClassificationResult


class CommandController:
    """Manages rover state, command confirmation filtering, cooldowns, and safety watchdogs."""

    def __init__(self, cfg: Optional[RoverConfig] = None):
        self.config = cfg or config
        self.transport: CommandTransport = create_transport(
            self.config.transport_type,
            com_port=self.config.com_port,
            baud_rate=self.config.baud_rate,
            wifi_host=self.config.wifi_host,
            wifi_port=self.config.wifi_port
        )

        self.mode: str = "GESTURE"  # "GESTURE" or "MANUAL"
        self.is_armed: bool = self.config.rover_armed
        self.estop_active: bool = False

        # Multi-frame gesture stabilization buffer
        self._gesture_history: deque = deque(maxlen=self.config.confirmation_frames)
        self.confirmed_gesture: str = "STOP"
        self.active_command: str = "S"
        self.current_confidence: float = 0.0
        self.last_command_latency_ms: float = 0.0
        self.gesture_to_command_latency_ms: float = 0.0
        self._gesture_change_started_at: Optional[float] = None
        self._last_dispatch_time: float = 0.0

        # Timing and safety timestamps
        self.last_command_time: float = time.time()
        self.last_turn_time: float = 0.0
        self.last_crab_time: float = 0.0
        self.last_hand_detected_time: float = 0.0

        self._turn_latched: bool = False
        self._crab_latched: bool = False
        self._timed_action_deadline: float = 0.0

        # Command logging
        self.command_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._dispatch_event = threading.Event()
        self._pending_motion: Optional[str] = None
        self._pending_safety: Optional[str] = None
        self._dispatch_thread: Optional[threading.Thread] = None
        self._running = True

        # Connect transport
        self.transport.connect()

        self._start_dispatcher_if_needed()

        # Start watchdog background thread
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def update_transport(self, transport_type: str, **kwargs) -> bool:
        """Switch or reconnect transport dynamically."""
        with self._lock:
            try:
                self.transport.disconnect()
            except Exception:
                pass
            if "com_port" in kwargs:
                self.config.com_port = kwargs["com_port"]
            if "baud_rate" in kwargs:
                self.config.baud_rate = kwargs["baud_rate"]
            if "esp32_ip" in kwargs:
                self.config.esp32_ip = kwargs["esp32_ip"]
                self.config.wifi_host = kwargs["esp32_ip"]
            if "esp32_port" in kwargs:
                self.config.esp32_port = kwargs["esp32_port"]
                self.config.wifi_port = kwargs["esp32_port"]

            transport_kwargs = {
                "com_port": self.config.com_port,
                "baud_rate": self.config.baud_rate,
                "esp32_ip": self.config.esp32_ip,
                "esp32_port": self.config.esp32_port,
                "wifi_host": self.config.wifi_host,
                "wifi_port": self.config.wifi_port,
                **kwargs
            }
            self.transport = create_transport(transport_type, **transport_kwargs)
            connected = self.transport.connect()
            self._start_dispatcher_if_needed()
            return connected

    def _start_dispatcher_if_needed(self) -> None:
        if (isinstance(self.transport, WiFiTransport) and
                (self._dispatch_thread is None or not self._dispatch_thread.is_alive())):
            self._dispatch_thread = threading.Thread(
                target=self._command_dispatch_loop,
                name="rover-command-dispatch",
                daemon=True
            )
            self._dispatch_thread.start()

    def set_mode(self, new_mode: str) -> None:
        """Switch between GESTURE and MANUAL modes."""
        with self._lock:
            if new_mode.upper() in ("GESTURE", "MANUAL"):
                self.mode = new_mode.upper()
                print(f"[INFO] Rover mode changed to {self.mode}")
                self._dispatch_command("S", source="mode_change")

    def arm_rover(self) -> None:
        """Arm the rover to allow physical movement."""
        with self._lock:
            self.is_armed = True
            self.estop_active = False
            self.config.rover_armed = True
            print("[INFO] Rover ARMED: Movement commands enabled.")
            self._dispatch_command("A", source="arm")

    def disarm_rover(self) -> None:
        """Disarm the rover for safety."""
        with self._lock:
            self.is_armed = False
            self.config.rover_armed = False
            print("[INFO] Rover DISARMED: Movements locked.")
            # D clears the arm latch in the Arduino as well as stopping motion.
            self._dispatch_command("D", source="disarm")

    def emergency_stop(self) -> None:
        """Immediate Emergency Stop override."""
        with self._lock:
            self.estop_active = True
            self.is_armed = False
            self.config.rover_armed = False
            self.active_command = "S"
            self.confirmed_gesture = "STOP"
            self._gesture_history.clear()
            self._turn_latched = False
            self._crab_latched = False
            print("[EMERGENCY STOP] Triggered! Halting rover immediately.")
            # E clears the physical arm latch; the firmware also stops motors.
            try:
                self.transport.send_command("E")
            except Exception as e:
                print(f"[ERROR] E-Stop send failed: {e}")
            self._log_command("E", "EMERGENCY_STOP", 1.0)

    def process_gesture_frame(self, hand_detected: bool, classification: GestureClassificationResult) -> Dict[str, Any]:
        """Process classified hand gesture through stabilization queue, cooldowns, and safety gates."""
        now = time.time()

        with self._lock:
            if self.estop_active:
                return self._get_telemetry_unlocked()

            if self.mode != "GESTURE":
                return self._get_telemetry_unlocked()

            if not hand_detected or classification.gesture == "NONE":
                self._gesture_history.clear()
                self._turn_latched = False
                self._crab_latched = False
                # Hand lost -> automatically issue STOP immediately if not already stopped
                if self.active_command != "S":
                    self._dispatch_command("S", source="hand_lost")
                return self._get_telemetry_unlocked()

            self.last_hand_detected_time = now
            self.current_confidence = classification.confidence

            # Confidence gate: drop predictions below threshold
            if classification.confidence < self.config.confidence_threshold:
                return self._get_telemetry_unlocked()

            # Append gesture to multi-frame stabilization window
            self._gesture_history.append(classification.gesture)

            # Check if gesture is stable across required frame count
            if len(self._gesture_history) == self.config.confirmation_frames:
                first_g = self._gesture_history[0]
                if all(g == first_g for g in self._gesture_history):
                    stable_gesture = first_g
                    target_cmd = self.config.gesture_mappings.get(stable_gesture, "S")

                    # Handle one-shot 360° Turn with latch and cooldown
                    if target_cmd == "T":
                        if not self._turn_latched and (now - self.last_turn_time >= self.config.turn_cooldown_sec):
                            self._turn_latched = True
                            self.last_turn_time = now
                            self.confirmed_gesture = stable_gesture
                            self._dispatch_command("T", source="gesture")
                            print("[INFO] One-shot 360° TURN dispatched.")
                    else:
                        self._turn_latched = False

                    # Handle Crab Walk with latch and cooldown
                    if target_cmd == "C":
                        if not self._crab_latched and (now - self.last_crab_time >= self.config.crab_cooldown_sec):
                            self._crab_latched = True
                            self.last_crab_time = now
                            self.confirmed_gesture = stable_gesture
                            self._dispatch_command("C", source="gesture")
                    else:
                        self._crab_latched = False

                    # Continuous directional gestures (F, B, L, R, S)
                    if target_cmd not in ("T", "C"):
                        self.confirmed_gesture = stable_gesture
                        self._dispatch_command(target_cmd, source="gesture")

            return self._get_telemetry_unlocked()

    def process_manual_command(self, key_or_cmd: str) -> None:
        """Execute manual keyboard or button command."""
        if not key_or_cmd or not isinstance(key_or_cmd, str):
            return

        if self.estop_active:
            return

        # S is protocol STOP; B is BACKWARD; W/KEY_S/A/D support keyboard mapping
        cmd_map = {
            "W": "F", "F": "F", "FORWARD": "F",
            "B": "B", "BACKWARD": "B", "KEY_S": "B",
            "A": "L", "L": "L", "LEFT": "L",
            "D": "R", "R": "R", "RIGHT": "R",
            "C": "C", "CRAB": "C", "CRAB_WALK": "C",
            "T": "T", "TURN": "T", "TURN_360": "T",
            "S": "S", "STOP": "S", "SPACE": "S"
        }

        target = cmd_map.get(key_or_cmd.strip().upper(), "S")
        with self._lock:
            self._dispatch_command(target, source="manual")

    def _dispatch_command(self, cmd: str, source: str = "unknown") -> None:
        """Send command to physical rover if armed or if command is STOP."""
        if cmd not in {"F", "B", "L", "R", "C", "T", "S", "A", "D", "E"}:
            cmd = "S"

        now = time.time()

        # Refresh movement often enough for the hardware watchdog, but never
        # send the same frame's command repeatedly over HTTP.
        refresh_sec = max(0.02, self.config.command_refresh_interval_ms / 1000.0)
        if (cmd == self.active_command and
                now - self._last_dispatch_time < refresh_sec and
                cmd not in ("A", "D", "E")):
            return

        # Safety gate: if disarmed and command is not STOP or ARM, log and suppress physical motion
        if not self.is_armed and cmd not in ("S", "A", "D", "E"):
            self._log_command(cmd, f"{source}_disarmed", self.current_confidence)
            return

        if isinstance(self.transport, WiFiTransport):
            if source == "gesture" and cmd != self.active_command:
                self._gesture_change_started_at = time.perf_counter()
            self.active_command = cmd
            self.last_command_time = now
            self._last_dispatch_time = now
            if cmd == "T":
                self._timed_action_deadline = now + 2.5
            elif cmd == "C":
                self._timed_action_deadline = now + 1.5
            else:
                self._timed_action_deadline = 0.0
            self._log_command(cmd, source, self.current_confidence)

            # Keep only the newest movement command. Safety commands are kept
            # separately so ARM/DISARM/ESTOP/STOP cannot be overwritten by it.
            if cmd in ("A", "D", "E", "S"):
                self._pending_safety = cmd
            else:
                self._pending_motion = cmd
            self._dispatch_event.set()
            return

        # Transmit via hardware transport
        try:
            send_started = time.perf_counter()
            sent = self.transport.send_command(cmd)
            self.last_command_latency_ms = round((time.perf_counter() - send_started) * 1000.0, 1)
        except Exception as exc:
            print(f"[ERROR] Command dispatch failed: {exc}")
            sent = False

        if not sent:
            self.active_command = "S"
            self.confirmed_gesture = "STOP"
            self._timed_action_deadline = 0.0
            self._log_command("S", f"{source}_transport_failure", 1.0)
            return

        self.active_command = cmd
        self.last_command_time = now
        self._last_dispatch_time = now
        if cmd == "T":
            self._timed_action_deadline = now + 2.5
        elif cmd == "C":
            self._timed_action_deadline = now + 1.5
        else:
            self._timed_action_deadline = 0.0
        self._log_command(cmd, source, self.current_confidence)

    def _command_dispatch_loop(self) -> None:
        """Send Wi-Fi commands off the camera thread with latest-motion priority."""
        while self._running:
            self._dispatch_event.wait(0.05)
            self._dispatch_event.clear()

            while self._running:
                with self._lock:
                    command = self._pending_safety or self._pending_motion
                    if self._pending_safety:
                        self._pending_safety = None
                    else:
                        self._pending_motion = None

                if not command:
                    break

                started = time.perf_counter()
                try:
                    sent = self.transport.send_command(command)
                except Exception as exc:
                    print(f"[ERROR] Async command dispatch failed: {exc}")
                    sent = False
                latency_ms = round((time.perf_counter() - started) * 1000.0, 1)

                with self._lock:
                    self.last_command_latency_ms = latency_ms
                    if self._gesture_change_started_at is not None:
                        self.gesture_to_command_latency_ms = round(
                            (time.perf_counter() - self._gesture_change_started_at) * 1000.0,
                            1
                        )
                        self._gesture_change_started_at = None
                    if not sent:
                        self.active_command = "S"
                        self.confirmed_gesture = "STOP"
                        self._timed_action_deadline = 0.0
                        self._log_command("S", "transport_failure", 1.0)

    def _log_command(self, cmd: str, source: str, confidence: float) -> None:
        """Keep a rolling timestamped log of sent commands."""
        self.command_log.append({
            "command": cmd,
            "source": source,
            "confidence": round(confidence, 2),
            "timestamp": round(time.time(), 3),
            "time_str": time.strftime("%H:%M:%S")
        })
        if len(self.command_log) > 50:
            self.command_log.pop(0)

    def _watchdog_loop(self) -> None:
        """Communication safety watchdog: enforces STOP if no active command refresh within timeout."""
        timeout_sec = self.config.command_timeout_ms / 1000.0

        while self._running:
            time.sleep(self.config.watchdog_interval_ms / 1000.0)

            with self._lock:
                now = time.time()
                # If rover is armed and in a motion state (not STOP)
                if self.is_armed and self.active_command not in ("S", "A"):
                    if self._timed_action_deadline and now < self._timed_action_deadline:
                        continue
                    # Check if command timeout exceeded
                    if (not self._timed_action_deadline and
                            now - self.last_command_time > timeout_sec) or (
                            self._timed_action_deadline and now >= self._timed_action_deadline):
                        print("[WATCHDOG] Command timeout expired! Issuing automatic STOP.")
                        self.active_command = "S"
                        self._timed_action_deadline = 0.0
                        self.confirmed_gesture = "STOP"
                        self._gesture_history.clear()
                        self._turn_latched = False
                        self._crab_latched = False
                        try:
                            self.transport.send_command("S")
                        except Exception:
                            pass
                        self._log_command("S", "watchdog_timeout", 1.0)

    def _get_telemetry_unlocked(self) -> Dict[str, Any]:
        """Internal telemetry packet generator without re-acquiring lock."""
        return {
            "mode": self.mode,
            "is_armed": self.is_armed,
            "estop_active": self.estop_active,
            "active_command": self.active_command,
            "confirmed_gesture": self.confirmed_gesture,
            "confidence": self.current_confidence,
            "command_latency_ms": self.last_command_latency_ms,
            "gesture_to_command_latency_ms": self.gesture_to_command_latency_ms,
            "command_refresh_interval_ms": self.config.command_refresh_interval_ms,
            "camera_fps": 0.0,
            "detection_fps": 0.0,
            "camera_width": 0,
            "camera_height": 0,
            "camera_configured_fps": 0.0,
            "frame_interval_ms": 0.0,
            "latency_ms": 0.0,
            "classification_latency_ms": 0.0,
            "transport": self.transport.get_status(),
            "last_command_time": self.last_command_time,
            "recent_logs": list(self.command_log[-10:]) if self.command_log else []
        }

    def get_telemetry(self) -> Dict[str, Any]:
        """Thread-safe telemetry packet for WebSocket clients."""
        with self._lock:
            return self._get_telemetry_unlocked()

    def close(self) -> None:
        """Clean shutdown."""
        self._running = False
        self._dispatch_event.set()
        if self._dispatch_thread and self._dispatch_thread.is_alive():
            self._dispatch_thread.join(timeout=1.0)
        try:
            self.emergency_stop()
            self.transport.disconnect()
        except Exception:
            pass
