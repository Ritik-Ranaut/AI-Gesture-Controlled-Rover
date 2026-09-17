"""Wi-Fi Transport for Dedicated Normal ESP32 Wireless Communication Controller."""

import time
import threading
from typing import Optional, Dict, Any
import requests


class WiFiTransport:
    """Communicates with the ESP32 HTTP controller over Wi-Fi."""

    def __init__(self, host: str = "192.168.4.1", port: int = 80, timeout: float = 0.3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Persistent HTTP session with keep-alive for sub-5ms low latency
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=0)
        self._session.mount("http://", adapter)
        
        self._connected = False
        self._arduino_connected = False
        self._last_cmd_time = 0.0
        self._last_command = "S"
        self._last_error = ""
        self._last_status_cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Verify reachability of ESP32 and check link to Arduino."""
        with self._lock:
            try:
                print(f"[INFO] Connecting to Normal ESP32 Bridge at {self.base_url}...")
                resp = self._session.get(f"{self.base_url}/status", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self._connected = True
                    self._last_error = ""
                    self._last_status_cache = data
                    print(f"[INFO] ESP32 Connected! Device: {data.get('device')}, Mode: {data.get('wifiMode')}, IP: {data.get('ip')}")
                    
                    return True
                else:
                    self._connected = False
                    self._last_error = f"HTTP {resp.status_code}"
                    return False
            except Exception as e:
                self._connected = False
                self._arduino_connected = False
                self._last_error = str(e)
                print(f"[WARNING] ESP32 Wi-Fi connection failed: {e}")
                return False

    def disconnect(self) -> None:
        """Send STOP command to ESP32 and reset connection flag."""
        with self._lock:
            if self._connected:
                try:
                    self._session.post(
                        f"{self.base_url}/command",
                        json={"command": "S"},
                        timeout=0.2
                    )
                except Exception:
                    pass
            self._connected = False
            self._arduino_connected = False
            print("[INFO] ESP32 Wi-Fi transport disconnected.")

    def send_command(self, command: str) -> bool:
        """Dispatch a compatibility command character to ESP32."""
        if not command or not isinstance(command, str):
            return False
        cmd = command.strip().upper()
        if not cmd:
            return False
        with self._lock:
            try:
                # Fast HTTP POST with persistent keep-alive
                resp = self._session.post(
                    f"{self.base_url}/command",
                    json={"command": cmd},
                    timeout=self.timeout
                )
                # Older ESP32 firmware accepted only the query-string form.
                if resp.status_code == 404:
                    resp = self._session.get(
                        f"{self.base_url}/command",
                        params={"cmd": cmd},
                        timeout=self.timeout
                    )
                if resp.status_code == 200:
                    self._connected = True
                    self._last_cmd_time = time.time()
                    self._last_command = cmd
                    self._last_error = ""
                    return True
                else:
                    self._last_error = f"HTTP {resp.status_code}"
                    return False
            except requests.exceptions.RequestException as e:
                self._connected = False
                self._last_error = str(e)
                return False

    def send_servo_angle(self, angle: int) -> bool:
        """Set the direct-test servo angle on GPIO 18."""
        if not isinstance(angle, int) or not 0 <= angle <= 180:
            return False
        with self._lock:
            try:
                resp = self._session.get(
                    f"{self.base_url}/servo",
                    params={"angle": angle},
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    self._connected = True
                    self._last_error = ""
                    return True
            except requests.exceptions.RequestException as e:
                self._connected = False
                self._last_error = str(e)
        return False

    def read_response(self) -> Optional[str]:
        """Fetch latest status from ESP32."""
        with self._lock:
            if not self._connected:
                return None
            try:
                resp = self._session.get(f"{self.base_url}/status", timeout=0.15)
                if resp.status_code == 200:
                    data = resp.json()
                    self._last_status_cache = data
                    return f"OK:{data.get('lastCommand', 'S')}"
            except Exception:
                pass
            return None

    def test_connection(self) -> Dict[str, Any]:
        """Verify the laptop-to-ESP32 HTTP link using the status endpoint."""
        start_t = time.perf_counter()
        try:
            resp = self._session.get(f"{self.base_url}/status", timeout=1.5)
            rtt_ms = round((time.perf_counter() - start_t) * 1000, 1)

            if resp.status_code == 200:
                data = resp.json()
                laptop_to_esp32 = data.get("laptopToEsp32", "PASS")
                esp32_to_arduino = data.get("esp32ToArduino", "NOT_APPLICABLE")
                
                self._connected = True
                self._arduino_connected = False
                
                return {
                    "success": True,
                    "laptopToEsp32": laptop_to_esp32,
                    "esp32ToArduino": esp32_to_arduino,
                    "latencyMs": rtt_ms,
                    "wifiMode": data.get("wifiMode", "AP"),
                    "lastCommand": data.get("lastCommand", "S"),
                    "uptime": data.get("uptime", 0),
                    "message": "ESP32 HTTP link verified."
                }
            else:
                self._connected = False
                self._arduino_connected = False
                return {
                    "success": False,
                    "laptopToEsp32": "FAIL",
                    "esp32ToArduino": "FAIL",
                    "latencyMs": rtt_ms,
                    "error": f"HTTP {resp.status_code}",
                    "message": f"ESP32 answered with HTTP {resp.status_code} error status."
                }
        except Exception as e:
            rtt_ms = round((time.perf_counter() - start_t) * 1000, 1)
            self._connected = False
            self._arduino_connected = False
            self._last_error = str(e)
            return {
                "success": False,
                "laptopToEsp32": "FAIL",
                "esp32ToArduino": "FAIL",
                "latencyMs": rtt_ms,
                "error": str(e),
                "message": f"Could not reach ESP32 at {self.base_url}. Check the configured IP and Wi-Fi network."
            }

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> Dict[str, Any]:
        """Comprehensive diagnostics dictionary."""
        return {
            "type": "wifi",
            "host": self.host,
            "port": self.port,
            "url": self.base_url,
            "connected": self._connected,
            "arduinoConnected": self._arduino_connected,
            "last_command": self._last_command,
            "last_command_time": self._last_cmd_time,
            "last_error": self._last_error,
            "esp32_cache": self._last_status_cache
        }
