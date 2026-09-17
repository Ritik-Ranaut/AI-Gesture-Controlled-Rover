"""Deterministic Landmark-based Gesture Classifier for Rover Control."""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from config import config, RoverConfig


@dataclass
class GestureClassificationResult:
    gesture: str = "NONE"
    command: str = "S"
    confidence: float = 0.0
    finger_states: Dict[str, bool] = field(default_factory=dict)
    orientation: str = "NONE"
    details: Dict[str, Any] = field(default_factory=dict)


class GestureClassifier:
    """Classifies hand gestures from 21 MediaPipe 3D landmarks with high precision and low latency."""

    def __init__(self, current_config: Optional[RoverConfig] = None):
        self.config = current_config or config

    @staticmethod
    def _dist_2d(p1: Dict[str, float], p2: Dict[str, float]) -> float:
        """Euclidean distance in normalized 2D plane (x, y)."""
        return math.hypot(p1.get("x", 0.0) - p2.get("x", 0.0), p1.get("y", 0.0) - p2.get("y", 0.0))

    @staticmethod
    def _dist_3d(p1: Dict[str, float], p2: Dict[str, float]) -> float:
        """Euclidean distance in 3D space (x, y, z)."""
        return math.sqrt(
            (p1.get("x", 0.0) - p2.get("x", 0.0))**2 +
            (p1.get("y", 0.0) - p2.get("y", 0.0))**2 +
            (p1.get("z", 0.0) - p2.get("z", 0.0))**2
        )

    def extract_finger_states(self, landmarks: List[Dict[str, float]], handedness: str = "Right") -> Tuple[Dict[str, bool], Dict[str, float]]:
        """Determine extension state for all 5 fingers and their extension ratios.

        Returns:
            finger_states: { 'thumb': bool, 'index': bool, 'middle': bool, 'ring': bool, 'pinky': bool }
            ratios: { 'thumb': float, 'index': float, 'middle': float, 'ring': float, 'pinky': float }
        """
        if len(landmarks) < 21:
            return {k: False for k in ["thumb", "index", "middle", "ring", "pinky"]}, {}

        wrist = landmarks[0]

        # Finger joint indices: (MCP, PIP, DIP, TIP)
        joints = {
            "index": (5, 6, 7, 8),
            "middle": (9, 10, 11, 12),
            "ring": (13, 14, 15, 16),
            "pinky": (17, 18, 19, 20)
        }

        states: Dict[str, bool] = {}
        ratios: Dict[str, float] = {}

        # 4 Main fingers (Index, Middle, Ring, Pinky)
        for finger_name, (mcp_i, pip_i, dip_i, tip_i) in joints.items():
            mcp = landmarks[mcp_i]
            pip = landmarks[pip_i]
            tip = landmarks[tip_i]

            dist_wrist_tip = self._dist_2d(wrist, tip)
            dist_wrist_pip = self._dist_2d(wrist, pip)
            dist_mcp_tip = self._dist_2d(mcp, tip)
            dist_mcp_pip = self._dist_2d(mcp, pip)

            # Ratio of wrist-to-tip distance vs wrist-to-pip distance
            ratio = dist_wrist_tip / max(0.001, dist_wrist_pip)
            ratios[finger_name] = ratio

            # Finger is extended if tip is distinctly further from wrist and MCP than PIP
            is_extended = (ratio > 1.15) and (dist_mcp_tip > dist_mcp_pip * 1.1)
            states[finger_name] = is_extended

        # Thumb detection: Tip (4), IP (3), MCP (2), CMC (1)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        index_mcp = landmarks[5]
        pinky_mcp = landmarks[17]

        dist_thumb_pinky = self._dist_2d(thumb_tip, pinky_mcp)
        dist_ip_pinky = self._dist_2d(thumb_ip, pinky_mcp)
        dist_thumb_index = self._dist_2d(thumb_tip, index_mcp)

        thumb_ratio = dist_thumb_pinky / max(0.001, dist_ip_pinky)
        ratios["thumb"] = thumb_ratio

        # Thumb extended if pointing away from palm / pinky MCP and not tucked close to index
        thumb_extended = (thumb_ratio > 1.18) and (dist_thumb_index > 0.08)
        states["thumb"] = thumb_extended

        return states, ratios

    def classify(self, landmarks: List[Dict[str, float]], handedness: str = "Right") -> GestureClassificationResult:
        """Classify gesture using geometric relationships of hand landmarks."""
        if not landmarks or len(landmarks) < 21:
            return GestureClassificationResult(gesture="NONE", command="S", confidence=0.0)

        finger_states, ratios = self.extract_finger_states(landmarks, handedness)
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        index_tip = landmarks[8]

        # Vector from index MCP to index TIP
        dx = index_tip["x"] - index_mcp["x"]
        dy = index_tip["y"] - index_mcp["y"]  # In screen coords: +y is down, -y is up
        vector_len = math.hypot(dx, dy)

        # Compute primary orientation of extended index finger
        orientation = "NONE"
        orientation_confidence = 0.85
        if vector_len > 0.01:
            abs_dx = abs(dx)
            abs_dy = abs(dy)
            total = abs_dx + abs_dy
            if abs_dy >= abs_dx:
                # Vertical dominant
                if dy < 0:
                    orientation = "UP"
                    orientation_confidence = min(0.99, 0.70 + 0.30 * (abs_dy / total))
                else:
                    orientation = "DOWN"
                    orientation_confidence = min(0.99, 0.70 + 0.30 * (abs_dy / total))
            else:
                # Horizontal dominant
                if dx > 0:
                    orientation = "RIGHT"
                    orientation_confidence = min(0.99, 0.70 + 0.30 * (abs_dx / total))
                else:
                    orientation = "LEFT"
                    orientation_confidence = min(0.99, 0.70 + 0.30 * (abs_dx / total))

        # Check extended counts
        four_fingers = [finger_states["index"], finger_states["middle"], finger_states["ring"], finger_states["pinky"]]
        extended_count = sum(four_fingers)
        thumb_ext = finger_states["thumb"]

        gesture = "NONE"
        confidence = 0.0

        # GESTURE 1: STOP (Open Palm)
        # All 4 main fingers extended, or 4 + thumb extended
        if extended_count >= 4 or (extended_count == 3 and thumb_ext and finger_states["index"] and finger_states["middle"]):
            gesture = "STOP"
            avg_ratio = (ratios.get("index", 1.0) + ratios.get("middle", 1.0) + ratios.get("ring", 1.0) + ratios.get("pinky", 1.0)) / 4.0
            confidence = min(0.98, max(0.80, 0.70 + 0.18 * (avg_ratio - 1.1)))

        # GESTURE 2: TURN_360 (Closed Fist)
        # All 4 main fingers folded into fist with tips curled close to palm
        elif extended_count == 0:
            avg_curl = (ratios.get("index", 1.0) + ratios.get("middle", 1.0) + ratios.get("ring", 1.0) + ratios.get("pinky", 1.0)) / 4.0
            if avg_curl < 1.15:
                gesture = "TURN_360"
                # Higher confidence if thumb is also curled
                fist_score = 0.90 if not thumb_ext else 0.85
                confidence = fist_score
            else:
                gesture = "NONE"
                confidence = 0.50

        # GESTURE 3: CRAB_WALK (🤟 Rock-on / I-Love-You: Thumb + Index + Pinky extended; Middle & Ring folded)
        elif finger_states["index"] and finger_states["pinky"] and not finger_states["middle"] and not finger_states["ring"]:
            gesture = "CRAB_WALK"
            # High confidence if middle & ring are clearly curled
            curl_margin = min(1.0, max(0.75, 0.82 + (0.15 if thumb_ext else 0.08)))
            confidence = curl_margin

        # DIRECTIONAL GESTURES (Single Index Finger Extended, other 3 fingers folded)
        elif finger_states["index"] and not finger_states["middle"] and not finger_states["ring"] and not finger_states["pinky"]:
            if orientation == "UP":
                gesture = "FORWARD"
                confidence = orientation_confidence
            elif orientation == "DOWN":
                gesture = "BACKWARD"
                confidence = orientation_confidence
            elif orientation == "LEFT":
                gesture = "LEFT"
                confidence = orientation_confidence
            elif orientation == "RIGHT":
                gesture = "RIGHT"
                confidence = orientation_confidence
            else:
                gesture = "NONE"
                confidence = 0.50

        # Hand/palm pointing DOWN with 2 or more fingers pointing downwards
        elif orientation == "DOWN" and dy > 0.08 and extended_count <= 2:
            gesture = "BACKWARD"
            confidence = 0.82

        # Map to protocol command character using centralized mapping
        command = self.config.gesture_mappings.get(gesture, "S")

        details = {
            "ratios": ratios,
            "dx": round(dx, 4),
            "dy": round(dy, 4),
            "orientation": orientation,
            "extended_count": extended_count,
            "thumb_extended": thumb_ext
        }

        return GestureClassificationResult(
            gesture=gesture,
            command=command,
            confidence=round(confidence, 3),
            finger_states=finger_states,
            orientation=orientation,
            details=details
        )
