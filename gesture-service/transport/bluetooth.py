"""Bluetooth (HC-05 SPP) Transport implementation using PySerial."""

import time
import threading
from typing import Optional, Dict, Any
import serial
import serial.tools.list_ports


class BluetoothTransport:
    """Communicates with HC-05 Bluetooth transceiver via Windows virtual serial COM port."""

    def __init__(self, port: str = "COM7", baudrate: int = 9600, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._last_cmd_time = 0.0
        self._last_error = ""

    def connect(self) -> bool:
        """Open the Bluetooth serial connection."""
        with self._lock:
            if self.serial_conn and self.serial_conn.is_open:
                return True

            try:
                print(f"[INFO] Connecting to HC-05 on {self.port} at {self.baudrate} baud...")
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=0.2
                )
                time.sleep(0.1)  # Allow port settling
                self._last_error = ""
                print(f"[INFO] Bluetooth connected successfully on {self.port}")
                return True
            except Exception as e:
                self._last_error = str(e)
                print(f"[ERROR] Bluetooth connection to {self.port} failed: {e}")
                self.serial_conn = None
                return False

    def disconnect(self) -> None:
        """Close the serial connection cleanly."""
        with self._lock:
            if self.serial_conn:
                try:
                    # Send safe stop command before closing
                    self.serial_conn.write(b"S\n")
                    self.serial_conn.flush()
                except Exception:
                    pass
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
                self.serial_conn = None
                print(f"[INFO] Bluetooth disconnected from {self.port}")

    def send_command(self, command: str) -> bool:
        """Transmit a single command character terminated by newline."""
        with self._lock:
            if not self.serial_conn or not self.serial_conn.is_open:
                return False

            try:
                payload = f"{command.strip().upper()}\n".encode("ascii")
                self.serial_conn.write(payload)
                self.serial_conn.flush()
                self._last_cmd_time = time.time()
                return True
            except Exception as e:
                self._last_error = str(e)
                print(f"[WARNING] Bluetooth write error: {e}")
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
                self.serial_conn = None
                return False

    def read_response(self) -> Optional[str]:
        """Read any incoming response line from the Arduino."""
        with self._lock:
            if not self.serial_conn or not self.serial_conn.is_open:
                return None

            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode("ascii", errors="replace").strip()
                    if line:
                        return line
            except Exception as e:
                self._last_error = str(e)
            return None

    def is_connected(self) -> bool:
        """Check if serial connection is open."""
        with self._lock:
            return bool(self.serial_conn and self.serial_conn.is_open)

    def get_status(self) -> Dict[str, Any]:
        """Diagnostics and status summary."""
        return {
            "type": "bluetooth",
            "port": self.port,
            "baudrate": self.baudrate,
            "connected": self.is_connected(),
            "last_error": self._last_error,
            "last_command_time": self._last_cmd_time
        }
