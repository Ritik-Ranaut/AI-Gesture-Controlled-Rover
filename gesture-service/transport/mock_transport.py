"""Mock Transport for offline development, automated tests, and simulation."""

import time
from typing import Optional, Dict, Any, List


class MockTransport:
    """Simulates rover controller in-memory without physical hardware."""

    def __init__(self, simulate_watchdog: bool = True):
        self._connected = True
        self.last_command = "S"
        self.last_command_time = time.time()
        self.command_history: List[Dict[str, Any]] = []
        self.simulate_watchdog = simulate_watchdog
        self.battery_voltage = 12.4
        self._last_error = ""

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False
        self.last_command = "S"

    def send_command(self, command: str) -> bool:
        if not self._connected:
            return False

        cmd = command.strip().upper()
        now = time.time()
        self.last_command = cmd
        self.last_command_time = now
        self.command_history.append({
            "command": cmd,
            "timestamp": now
        })
        if len(self.command_history) > 100:
            self.command_history.pop(0)
        return True

    def read_response(self) -> Optional[str]:
        if not self._connected:
            return None

        # Simulate watchdog stop if idle for > 500ms
        if self.simulate_watchdog and self.last_command != "S":
            if time.time() - self.last_command_time > 0.5:
                self.last_command = "S"
                return "WATCHDOG:TIMEOUT->STOP"

        return f"OK:{self.last_command}"

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> Dict[str, Any]:
        return {
            "type": "mock",
            "connected": self._connected,
            "last_command": self.last_command,
            "last_command_time": self.last_command_time,
            "battery_voltage": self.battery_voltage,
            "total_commands": len(self.command_history),
            "last_error": self._last_error
        }
