"""Unit tests for the Rover Transports."""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gesture-service")))

from transport import create_transport, MockTransport
from transport.serial_transport import SerialTransport
from transport.bluetooth import BluetoothTransport


def test_mock_transport_connect_and_send():
    t = create_transport("mock")
    assert t.connect() is True
    assert t.is_connected() is True

    # Send command
    assert t.send_command("F") is True
    status = t.get_status()
    assert status["last_command"] == "F"
    assert status["connected"] is True

    # Read response
    resp = t.read_response()
    assert resp == "OK:F"

    t.disconnect()
    assert t.is_connected() is False


def test_mock_transport_watchdog():
    t = MockTransport(simulate_watchdog=True)
    t.connect()
    t.send_command("F")
    assert t.last_command == "F"

    # Wait for watchdog timeout (>0.5s)
    time.sleep(0.55)
    resp = t.read_response()
    assert "WATCHDOG" in resp
    assert t.last_command == "S"

    t.disconnect()


def test_transport_factory_fallback():
    # Unknown transport should fall back safely to Mock
    t = create_transport("non_existent_protocol")
    assert isinstance(t, MockTransport)


@pytest.mark.parametrize("transport_type", [SerialTransport, BluetoothTransport])
def test_serial_write_failure_releases_connection(transport_type):
    class FailingConnection:
        is_open = True

        def write(self, payload):
            raise OSError("simulated write failure")

        def close(self):
            self.is_open = False

    transport = transport_type()
    transport.serial_conn = FailingConnection()

    assert transport.send_command("F") is False
    assert transport.serial_conn is None
    assert transport.get_status()["connected"] is False
