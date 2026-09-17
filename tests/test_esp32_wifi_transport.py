"""Unit tests for the Normal ESP32 WiFiTransport and Connection Diagnostics."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gesture-service")))

from transport.wifi_transport import WiFiTransport


def test_wifi_transport_init():
    t = WiFiTransport(host="192.168.4.1", port=80)
    assert t.host == "192.168.4.1"
    assert t.port == 80
    assert t.base_url == "http://192.168.4.1:80"
    assert t.is_connected() is False


@patch("requests.Session.get")
def test_wifi_transport_connect_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "connected": True,
        "device": "ESP32-Rover-Bridge",
        "wifiMode": "AP",
        "ip": "192.168.4.1"
    }
    mock_get.return_value = mock_resp

    t = WiFiTransport(host="192.168.4.1", port=80)
    assert t.connect() is True
    assert t.is_connected() is True


@patch("requests.Session.post")
def test_wifi_transport_send_command(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "command": "F"}
    mock_post.return_value = mock_resp

    t = WiFiTransport(host="192.168.4.1", port=80)
    success = t.send_command("F")
    assert success is True
    assert t.get_status()["last_command"] == "F"

    # Verify POST was called with expected JSON body
    mock_post.assert_called_with(
        "http://192.168.4.1:80/command",
        json={"command": "F"},
        timeout=0.3
    )


@patch("requests.Session.get")
@patch("requests.Session.post")
def test_wifi_transport_legacy_get_command_fallback(mock_post, mock_get):
    post_response = MagicMock()
    post_response.status_code = 404
    mock_post.return_value = post_response

    get_response = MagicMock()
    get_response.status_code = 200
    mock_get.return_value = get_response

    t = WiFiTransport(host="192.168.4.1", port=80)
    assert t.send_command("F") is True
    mock_get.assert_called_with(
        "http://192.168.4.1:80/command",
        params={"cmd": "F"},
        timeout=0.3
    )


@patch("requests.Session.get")
def test_two_tier_connection_test_both_pass(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "laptopToEsp32": "PASS",
        "esp32ToArduino": "PASS",
        "wifiMode": "AP",
        "uptime": 120
    }
    mock_get.return_value = mock_resp

    t = WiFiTransport(host="192.168.4.1", port=80)
    diag = t.test_connection()

    assert diag["success"] is True
    assert diag["laptopToEsp32"] == "PASS"
    assert diag["esp32ToArduino"] == "PASS"


@patch("requests.Session.get")
def test_two_tier_connection_test_arduino_fail(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "laptopToEsp32": "PASS",
        "esp32ToArduino": "FAIL",
        "wifiMode": "AP",
        "uptime": 120
    }
    mock_get.return_value = mock_resp

    t = WiFiTransport(host="192.168.4.1", port=80)
    diag = t.test_connection()

    assert diag["success"] is True
    assert diag["laptopToEsp32"] == "PASS"
    assert diag["esp32ToArduino"] == "FAIL"


@patch("requests.Session.get")
def test_two_tier_connection_test_esp32_unreachable(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection timed out")

    t = WiFiTransport(host="192.168.4.1", port=80)
    diag = t.test_connection()

    assert diag["success"] is False
    assert diag["laptopToEsp32"] == "FAIL"
    assert diag["esp32ToArduino"] == "FAIL"
