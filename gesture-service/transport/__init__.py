"""Transport package exporting all transport implementations and a factory."""

from .base import CommandTransport
from .bluetooth import BluetoothTransport
from .serial_transport import SerialTransport
from .wifi_transport import WiFiTransport
from .mock_transport import MockTransport


def create_transport(transport_type: str, **kwargs) -> CommandTransport:
    """Factory function for creating rover communication transports."""
    t_type = transport_type.lower()
    if t_type == "bluetooth":
        port = kwargs.get("com_port", "COM7")
        baud = kwargs.get("baud_rate", 9600)
        return BluetoothTransport(port=port, baudrate=baud)
    elif t_type == "serial":
        port = kwargs.get("com_port", "COM3")
        baud = kwargs.get("baud_rate", 115200)
        return SerialTransport(port=port, baudrate=baud)
    elif t_type == "wifi":
        host = kwargs.get("esp32_ip") or kwargs.get("wifi_host", "192.168.4.1")
        port = int(kwargs.get("esp32_port") or kwargs.get("wifi_port", 80))
        return WiFiTransport(host=host, port=port)
    elif t_type == "mock":
        return MockTransport()
    else:
        print(f"[WARNING] Unknown transport '{transport_type}', falling back to MockTransport.")
        return MockTransport()


__all__ = [
    "CommandTransport",
    "BluetoothTransport",
    "SerialTransport",
    "WiFiTransport",
    "MockTransport",
    "create_transport"
]
