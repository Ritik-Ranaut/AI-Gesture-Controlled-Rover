"""Unit tests for the Safety Command Controller and Watchdog."""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gesture-service")))

from config import RoverConfig
from command_controller import CommandController
from gesture_classifier import GestureClassificationResult
from transport.mock_transport import MockTransport


def create_test_controller():
    cfg = RoverConfig(
        transport_type="mock",
        confirmation_frames=3,
        turn_cooldown_sec=1.0,
        command_timeout_ms=300,
        confidence_threshold=0.80,
        rover_armed=True
    )
    ctrl = CommandController(cfg)
    return ctrl


def test_frame_stabilization():
    ctrl = create_test_controller()
    fwd_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.90)

    # Frame 1: should not yet confirm
    ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.confirmed_gesture != "FORWARD"

    # Frame 2: should not yet confirm
    ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.confirmed_gesture != "FORWARD"

    # Frame 3: confirmed!
    ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.confirmed_gesture == "FORWARD"
    assert ctrl.active_command == "F"

    ctrl.close()


def test_repeated_gesture_frames_are_rate_limited():
    ctrl = create_test_controller()
    fwd_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.90)

    for _ in range(20):
        ctrl.process_gesture_frame(True, fwd_res)

    forward_commands = [entry for entry in ctrl.transport.command_history if entry["command"] == "F"]
    assert len(forward_commands) == 1
    ctrl.close()


def test_confidence_threshold_rejection():
    ctrl = create_test_controller()
    # Confidence 0.65 is below threshold (0.80)
    low_conf_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.65)

    for _ in range(5):
        ctrl.process_gesture_frame(True, low_conf_res)

    assert ctrl.confirmed_gesture != "FORWARD"
    assert ctrl.active_command != "F"

    ctrl.close()


def test_turn360_cooldown_behavior():
    ctrl = create_test_controller()
    turn_res = GestureClassificationResult(gesture="TURN_360", command="T", confidence=0.95)

    # Confirm 3 frames of fist
    for _ in range(3):
        ctrl.process_gesture_frame(True, turn_res)

    assert ctrl.active_command == "T"
    assert len(ctrl.command_log) > 0

    # Count how many 'T' commands were sent
    t_count_1 = sum(1 for log in ctrl.command_log if log["command"] == "T")
    assert t_count_1 == 1

    # Keep holding fist in front of camera for next 5 frames immediately
    for _ in range(5):
        ctrl.process_gesture_frame(True, turn_res)

    t_count_2 = sum(1 for log in ctrl.command_log if log["command"] == "T")
    # Should still only be 1 because of cooldown!
    assert t_count_2 == 1

    ctrl.close()


def test_disarmed_rover_suppresses_motion():
    ctrl = create_test_controller()
    ctrl.disarm_rover()
    assert not ctrl.is_armed

    fwd_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.95)
    for _ in range(3):
        ctrl.process_gesture_frame(True, fwd_res)

    # Disarmed rover should NOT dispatch 'F' to transport
    mock_transport: MockTransport = ctrl.transport
    # The last command actually sent to mock transport must not be 'F'
    assert mock_transport.last_command != "F"

    ctrl.close()


def test_emergency_stop_immediate_override():
    ctrl = create_test_controller()
    fwd_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.95)
    for _ in range(3):
        ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.active_command == "F"

    # Trigger E-STOP
    ctrl.emergency_stop()
    assert ctrl.estop_active is True
    assert ctrl.is_armed is False
    assert ctrl.active_command == "S"

    # Subsequent frames must be ignored while estop is active
    for _ in range(3):
        ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.active_command == "S"

    ctrl.close()


def test_disarm_and_estop_clear_physical_arm_latch():
    ctrl = create_test_controller()
    mock_transport: MockTransport = ctrl.transport

    ctrl.disarm_rover()
    assert mock_transport.command_history[-1]["command"] == "D"

    ctrl.arm_rover()
    ctrl.emergency_stop()
    assert mock_transport.command_history[-1]["command"] == "E"
    ctrl.close()


def test_timed_turn_is_not_stopped_by_continuous_watchdog():
    ctrl = create_test_controller()
    turn_res = GestureClassificationResult(gesture="TURN_360", command="T", confidence=0.95)

    for _ in range(3):
        ctrl.process_gesture_frame(True, turn_res)
    time.sleep(0.4)

    commands = [entry["command"] for entry in ctrl.transport.command_history]
    assert commands.count("T") == 1
    assert "S" not in commands[commands.index("T") + 1:]
    ctrl.close()


def test_hand_lost_triggers_stop():
    ctrl = create_test_controller()
    fwd_res = GestureClassificationResult(gesture="FORWARD", command="F", confidence=0.95)
    for _ in range(3):
        ctrl.process_gesture_frame(True, fwd_res)
    assert ctrl.active_command == "F"

    # Hand removed
    time.sleep(0.16)
    none_res = GestureClassificationResult(gesture="NONE", command="S", confidence=0.0)
    ctrl.process_gesture_frame(False, none_res)

    assert ctrl.active_command == "S"

    ctrl.close()
