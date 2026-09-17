"""Unit tests for the Geometric Hand Gesture Classifier."""

import sys
import os
import pytest

# Add gesture-service directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gesture-service")))

from config import RoverConfig
from gesture_classifier import GestureClassifier


def make_blank_landmarks():
    """Create a list of 21 blank landmarks at default wrist position."""
    return [{"index": i, "x": 0.5, "y": 0.7, "z": 0.0} for i in range(21)]


def make_open_palm_landmarks():
    """Simulate an open palm pointing upwards (STOP gesture)."""
    lm = make_blank_landmarks()
    lm[0] = {"x": 0.5, "y": 0.8, "z": 0.0}  # Wrist

    # Thumb extended left/up
    lm[1] = {"x": 0.44, "y": 0.72, "z": 0.0}
    lm[2] = {"x": 0.40, "y": 0.64, "z": 0.0}
    lm[3] = {"x": 0.36, "y": 0.58, "z": 0.0}
    lm[4] = {"x": 0.32, "y": 0.50, "z": 0.0}  # Thumb tip extended outwards

    # Index extended UP
    lm[5] = {"x": 0.45, "y": 0.55, "z": 0.0}  # MCP
    lm[6] = {"x": 0.45, "y": 0.45, "z": 0.0}  # PIP
    lm[7] = {"x": 0.45, "y": 0.38, "z": 0.0}  # DIP
    lm[8] = {"x": 0.45, "y": 0.30, "z": 0.0}  # TIP

    # Middle extended UP
    lm[9] = {"x": 0.50, "y": 0.54, "z": 0.0}
    lm[10] = {"x": 0.50, "y": 0.43, "z": 0.0}
    lm[11] = {"x": 0.50, "y": 0.35, "z": 0.0}
    lm[12] = {"x": 0.50, "y": 0.27, "z": 0.0}

    # Ring extended UP
    lm[13] = {"x": 0.55, "y": 0.55, "z": 0.0}
    lm[14] = {"x": 0.55, "y": 0.45, "z": 0.0}
    lm[15] = {"x": 0.55, "y": 0.38, "z": 0.0}
    lm[16] = {"x": 0.55, "y": 0.30, "z": 0.0}

    # Pinky extended UP
    lm[17] = {"x": 0.60, "y": 0.58, "z": 0.0}
    lm[18] = {"x": 0.60, "y": 0.50, "z": 0.0}
    lm[19] = {"x": 0.60, "y": 0.44, "z": 0.0}
    lm[20] = {"x": 0.60, "y": 0.38, "z": 0.0}

    return lm


def make_closed_fist_landmarks():
    """Simulate a tightly closed fist (TURN_360 gesture)."""
    lm = make_blank_landmarks()
    lm[0] = {"x": 0.5, "y": 0.8, "z": 0.0}  # Wrist

    # Thumb curled across palm
    lm[1] = {"x": 0.46, "y": 0.74, "z": 0.0}
    lm[2] = {"x": 0.44, "y": 0.68, "z": 0.0}
    lm[3] = {"x": 0.46, "y": 0.64, "z": 0.0}
    lm[4] = {"x": 0.48, "y": 0.65, "z": 0.0}  # Curled

    # Index curled
    lm[5] = {"x": 0.45, "y": 0.60, "z": 0.0}
    lm[6] = {"x": 0.45, "y": 0.54, "z": 0.0}
    lm[7] = {"x": 0.45, "y": 0.58, "z": 0.0}
    lm[8] = {"x": 0.45, "y": 0.62, "z": 0.0}  # Curled down near MCP

    # Middle curled
    lm[9] = {"x": 0.50, "y": 0.60, "z": 0.0}
    lm[10] = {"x": 0.50, "y": 0.54, "z": 0.0}
    lm[11] = {"x": 0.50, "y": 0.58, "z": 0.0}
    lm[12] = {"x": 0.50, "y": 0.62, "z": 0.0}

    # Ring curled
    lm[13] = {"x": 0.55, "y": 0.60, "z": 0.0}
    lm[14] = {"x": 0.55, "y": 0.54, "z": 0.0}
    lm[15] = {"x": 0.55, "y": 0.58, "z": 0.0}
    lm[16] = {"x": 0.55, "y": 0.62, "z": 0.0}

    # Pinky curled
    lm[17] = {"x": 0.60, "y": 0.62, "z": 0.0}
    lm[18] = {"x": 0.60, "y": 0.56, "z": 0.0}
    lm[19] = {"x": 0.60, "y": 0.60, "z": 0.0}
    lm[20] = {"x": 0.60, "y": 0.64, "z": 0.0}

    return lm


def make_forward_landmarks():
    """Simulate Index pointing UP, other fingers curled (FORWARD gesture)."""
    lm = make_closed_fist_landmarks()
    # Extend only index finger UP
    lm[5] = {"x": 0.45, "y": 0.60, "z": 0.0}  # MCP
    lm[6] = {"x": 0.45, "y": 0.50, "z": 0.0}  # PIP
    lm[7] = {"x": 0.45, "y": 0.42, "z": 0.0}  # DIP
    lm[8] = {"x": 0.45, "y": 0.32, "z": 0.0}  # TIP
    return lm


def make_backward_landmarks():
    """Simulate Index pointing DOWN, other fingers curled (BACKWARD gesture)."""
    lm = make_blank_landmarks()
    lm[0] = {"x": 0.5, "y": 0.4, "z": 0.0}  # Wrist near top

    # Curled fingers
    for mcp_idx, base_x in [(9, 0.5), (13, 0.55), (17, 0.6)]:
        lm[mcp_idx] = {"x": base_x, "y": 0.50, "z": 0.0}
        lm[mcp_idx+1] = {"x": base_x, "y": 0.55, "z": 0.0}
        lm[mcp_idx+2] = {"x": base_x, "y": 0.52, "z": 0.0}
        lm[mcp_idx+3] = {"x": base_x, "y": 0.48, "z": 0.0}

    # Thumb curled
    lm[1] = {"x": 0.46, "y": 0.45, "z": 0.0}
    lm[2] = {"x": 0.44, "y": 0.48, "z": 0.0}
    lm[3] = {"x": 0.46, "y": 0.50, "z": 0.0}
    lm[4] = {"x": 0.48, "y": 0.48, "z": 0.0}

    # Index pointing DOWN
    lm[5] = {"x": 0.45, "y": 0.50, "z": 0.0}  # MCP
    lm[6] = {"x": 0.45, "y": 0.60, "z": 0.0}  # PIP
    lm[7] = {"x": 0.45, "y": 0.68, "z": 0.0}  # DIP
    lm[8] = {"x": 0.45, "y": 0.78, "z": 0.0}  # TIP
    return lm


def make_right_landmarks():
    """Simulate Index pointing RIGHT, other fingers curled (RIGHT gesture)."""
    lm = make_closed_fist_landmarks()
    # Extend index pointing RIGHT (+x)
    lm[5] = {"x": 0.45, "y": 0.60, "z": 0.0}  # MCP
    lm[6] = {"x": 0.55, "y": 0.60, "z": 0.0}  # PIP
    lm[7] = {"x": 0.65, "y": 0.60, "z": 0.0}  # DIP
    lm[8] = {"x": 0.76, "y": 0.60, "z": 0.0}  # TIP
    return lm


def make_left_landmarks():
    """Simulate Index pointing LEFT, other fingers curled (LEFT gesture)."""
    lm = make_closed_fist_landmarks()
    # Extend index pointing LEFT (-x)
    lm[5] = {"x": 0.55, "y": 0.60, "z": 0.0}  # MCP
    lm[6] = {"x": 0.45, "y": 0.60, "z": 0.0}  # PIP
    lm[7] = {"x": 0.35, "y": 0.60, "z": 0.0}  # DIP
    lm[8] = {"x": 0.24, "y": 0.60, "z": 0.0}  # TIP
    return lm


def make_crab_walk_landmarks():
    """Simulate Rock-on / I-Love-You (CRAB_WALK): Thumb, Index, Pinky extended; Middle & Ring curled."""
    lm = make_closed_fist_landmarks()

    # Extend Thumb outwards
    lm[1] = {"x": 0.44, "y": 0.72, "z": 0.0}
    lm[2] = {"x": 0.40, "y": 0.64, "z": 0.0}
    lm[3] = {"x": 0.36, "y": 0.58, "z": 0.0}
    lm[4] = {"x": 0.30, "y": 0.50, "z": 0.0}

    # Extend Index UP
    lm[5] = {"x": 0.45, "y": 0.60, "z": 0.0}
    lm[6] = {"x": 0.45, "y": 0.50, "z": 0.0}
    lm[7] = {"x": 0.45, "y": 0.42, "z": 0.0}
    lm[8] = {"x": 0.45, "y": 0.32, "z": 0.0}

    # Extend Pinky UP
    lm[17] = {"x": 0.60, "y": 0.62, "z": 0.0}
    lm[18] = {"x": 0.60, "y": 0.54, "z": 0.0}
    lm[19] = {"x": 0.60, "y": 0.46, "z": 0.0}
    lm[20] = {"x": 0.60, "y": 0.38, "z": 0.0}

    return lm


def test_classify_stop_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_open_palm_landmarks())
    assert res.gesture == "STOP"
    assert res.command == "S"
    assert res.confidence >= 0.80


def test_classify_turn360_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_closed_fist_landmarks())
    assert res.gesture == "TURN_360"
    assert res.command == "T"
    assert res.confidence >= 0.80


def test_classify_forward_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_forward_landmarks())
    assert res.gesture == "FORWARD"
    assert res.command == "F"
    assert res.confidence >= 0.80


def test_classify_backward_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_backward_landmarks())
    assert res.gesture == "BACKWARD"
    assert res.command == "B"
    assert res.confidence >= 0.80


def test_classify_right_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_right_landmarks())
    assert res.gesture == "RIGHT"
    assert res.command == "R"
    assert res.confidence >= 0.80


def test_classify_left_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_left_landmarks())
    assert res.gesture == "LEFT"
    assert res.command == "L"
    assert res.confidence >= 0.80


def test_classify_crab_walk_gesture():
    classifier = GestureClassifier()
    res = classifier.classify(make_crab_walk_landmarks())
    assert res.gesture == "CRAB_WALK"
    assert res.command == "C"
    assert res.confidence >= 0.80


def test_empty_landmarks_returns_none():
    classifier = GestureClassifier()
    res = classifier.classify([])
    assert res.gesture == "NONE"
    assert res.command == "S"
    assert res.confidence == 0.0
