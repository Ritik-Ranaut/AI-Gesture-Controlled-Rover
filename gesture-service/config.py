"""Configuration settings for the Stair-Climbing Rover Gesture Control System."""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RoverConfig:
    # Camera settings
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30
    video_encode_every_n_frames: int = 2
    actual_camera_width: int = 0
    actual_camera_height: int = 0
    actual_camera_fps: float = 0.0

    # Gesture recognition parameters
    confidence_threshold: float = 0.80
    confirmation_frames: int = 3
    turn_cooldown_sec: float = 2.0
    crab_cooldown_sec: float = 1.0

    # Safety and Watchdog
    command_timeout_ms: int = 500
    command_refresh_interval_ms: int = 120
    watchdog_interval_ms: int = 100
    rover_armed: bool = False  # Safe default: starts disarmed

    # Communication / Transport
    transport_type: str = field(default_factory=lambda: os.environ.get("ROVER_TRANSPORT", "wifi"))  # "bluetooth", "serial", "wifi", "mock"
    com_port: str = "COM7"
    baud_rate: int = 9600
    # Normal ESP32 Wireless Communication Controller (Dedicated Bridge)
    esp32_ip: str = field(default_factory=lambda: os.environ.get("ESP32_IP", "192.168.4.1"))
    esp32_port: int = field(default_factory=lambda: int(os.environ.get("ESP32_PORT", "80")))
    esp32_wifi_mode: str = field(default_factory=lambda: os.environ.get("ESP32_WIFI_MODE", "AP"))
    wifi_host: str = field(default_factory=lambda: os.environ.get("ESP32_IP", "192.168.4.1"))
    wifi_port: int = field(default_factory=lambda: int(os.environ.get("ESP32_PORT", "80")))

    # ESP32-CAM video stream (Independent subsystem)
    esp32_cam_url: str = field(default_factory=lambda: os.environ.get("ESP32_CAM_URL", ""))

    # Web & WebSocket Server
    server_host: str = "0.0.0.0"
    server_port: int = int(os.environ.get("ROVER_PORT", 8001))

    # Gesture-to-Command Mapping dictionary
    # Can be updated at runtime without altering core classification logic
    gesture_mappings: Dict[str, str] = field(default_factory=lambda: {
        "FORWARD": "F",
        "BACKWARD": "B",
        "LEFT": "L",
        "RIGHT": "R",
        "STOP": "S",
        "CRAB_WALK": "C",
        "TURN_360": "T",
        "NONE": "S"
    })

    def update(self, new_settings: Dict[str, Any]) -> None:
        """Dynamically update settings from dictionary."""
        for key, val in new_settings.items():
            if hasattr(self, key):
                target_type = type(getattr(self, key))
                try:
                    setattr(self, key, target_type(val))
                except (ValueError, TypeError):
                    setattr(self, key, val)


# Global singleton instance
config = RoverConfig()
