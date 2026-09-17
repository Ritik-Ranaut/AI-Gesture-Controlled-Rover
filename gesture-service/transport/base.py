"""Abstract base class for Rover Command Transports."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class CommandTransport(ABC):
    """Interface defining communication with the rover controller."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the rover hardware."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the rover hardware."""
        pass

    @abstractmethod
    def send_command(self, command: str) -> bool:
        """Send a single ASCII command character to the rover."""
        pass

    @abstractmethod
    def read_response(self) -> Optional[str]:
        """Read any telemetry or acknowledgment string from the rover."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is currently connected and healthy."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status dictionary."""
        pass
