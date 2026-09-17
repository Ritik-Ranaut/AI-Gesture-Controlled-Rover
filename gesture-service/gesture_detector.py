"""Gesture Detector module using MediaPipe for high-performance hand landmark extraction."""

import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import cv2
import numpy as np


# Hand landmark connections for drawing (MediaPipe hand topology)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                 # Palm base
]

LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP",
    "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP",
    "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"
]


@dataclass
class LandmarkPoint:
    x: float
    y: float
    z: float


@dataclass
class HandDetectionResult:
    detected: bool = False
    landmarks: List[Dict[str, float]] = field(default_factory=list)
    raw_landmarks: List[LandmarkPoint] = field(default_factory=list)
    handedness: str = "Unknown"
    bbox: Optional[Tuple[int, int, int, int]] = None
    fps: float = 0.0
    latency_ms: float = 0.0
    annotated_frame: Optional[np.ndarray] = None


class GestureDetector:
    """Wrapper for MediaPipe HandLandmarker with fallback and asset auto-download."""

    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        os.makedirs(model_dir, exist_ok=True)
        self.model_path = os.path.join(model_dir, "hand_landmarker.task")

        self._ensure_model_exists()
        self.landmarker = None
        self.use_tasks_api = False
        self._last_timestamp_ms = 0
        self._init_mediapipe()

        self._last_time = time.perf_counter()
        self._fps_history: List[float] = []

    def _ensure_model_exists(self) -> None:
        """Download official MediaPipe task bundle if missing."""
        if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) < 1000:
            print(f"[INFO] Downloading MediaPipe hand model to {self.model_path}...")
            try:
                urllib.request.urlretrieve(self.MODEL_URL, self.model_path)
                print(f"[INFO] Downloaded successfully: {os.path.getsize(self.model_path)} bytes.")
            except Exception as exc:
                print(f"[WARNING] Failed to download model: {exc}")

    def _init_mediapipe(self) -> None:
        """Initialize either MediaPipe Tasks or Solutions API."""
        try:
            import mediapipe as mp
            # Try Tasks API first
            if hasattr(mp, "tasks") and hasattr(mp.tasks, "vision"):
                from mediapipe.tasks.python import vision, BaseOptions
                base_options = BaseOptions(model_asset_path=self.model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    # VIDEO mode enables MediaPipe's temporal tracking path;
                    # IMAGE mode reruns hand detection from scratch per frame.
                    running_mode=vision.RunningMode.VIDEO,
                    num_hands=1,
                    min_hand_detection_confidence=0.5,
                    min_hand_presence_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.landmarker = vision.HandLandmarker.create_from_options(options)
                self.use_tasks_api = True
                print("[INFO] MediaPipe Tasks HandLandmarker initialized.")
                return
        except Exception as e:
            print(f"[WARNING] MediaPipe Tasks initialization failed: {e}")

        # Fallback to Solutions API
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.landmarker = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.use_tasks_api = False
                print("[INFO] MediaPipe Solutions Hands initialized.")
                return
        except Exception as e:
            print(f"[ERROR] Both MediaPipe APIs failed to initialize: {e}")

    def process_frame(self, frame: np.ndarray, draw_annotations: bool = True) -> HandDetectionResult:
        """Process an OpenCV BGR frame and return detected landmarks + annotations."""
        t_start = time.perf_counter()

        # Compute FPS
        dt = t_start - self._last_time
        self._last_time = t_start
        fps = min(120.0, (1.0 / dt)) if dt > 0 else 0.0
        self._fps_history.append(fps)
        if len(self._fps_history) > 15:
            self._fps_history.pop(0)
        smoothed_fps = float(np.mean(self._fps_history)) if self._fps_history else 0.0

        if frame is None or self.landmarker is None:
            return HandDetectionResult(fps=smoothed_fps, latency_ms=0.0, annotated_frame=frame)

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        annotated = frame.copy() if draw_annotations else frame

        detected = False
        landmarks_dict_list: List[Dict[str, float]] = []
        raw_pts: List[LandmarkPoint] = []
        handedness_str = "Unknown"
        bbox = None

        if self.use_tasks_api:
            import mediapipe as mp
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = time.monotonic_ns() // 1_000_000
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = timestamp_ms
            result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.hand_landmarks and len(result.hand_landmarks) > 0:
                detected = True
                hand_pts = result.hand_landmarks[0]
                if result.handedness and len(result.handedness) > 0:
                    handedness_str = result.handedness[0][0].category_name

                # Parse landmarks
                xs, ys = [], []
                for idx, lm in enumerate(hand_pts):
                    raw_pts.append(LandmarkPoint(x=lm.x, y=lm.y, z=lm.z))
                    landmarks_dict_list.append({
                        "index": idx,
                        "name": LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"PT_{idx}",
                        "x": float(lm.x),
                        "y": float(lm.y),
                        "z": float(lm.z),
                        "px": int(lm.x * w),
                        "py": int(lm.y * h)
                    })
                    xs.append(int(lm.x * w))
                    ys.append(int(lm.y * h))

                if xs and ys:
                    pad = 20
                    bbox = (
                        max(0, min(xs) - pad),
                        max(0, min(ys) - pad),
                        min(w, max(xs) + pad),
                        min(h, max(ys) + pad)
                    )
        else:
            # Legacy Solutions API
            result = self.landmarker.process(rgb_frame)
            if result.multi_hand_landmarks and len(result.multi_hand_landmarks) > 0:
                detected = True
                hand_pts = result.multi_hand_landmarks[0]
                if result.multi_handedness and len(result.multi_handedness) > 0:
                    handedness_str = result.multi_handedness[0].classification[0].label

                xs, ys = [], []
                for idx, lm in enumerate(hand_pts.landmark):
                    raw_pts.append(LandmarkPoint(x=lm.x, y=lm.y, z=lm.z))
                    landmarks_dict_list.append({
                        "index": idx,
                        "name": LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"PT_{idx}",
                        "x": float(lm.x),
                        "y": float(lm.y),
                        "z": float(lm.z),
                        "px": int(lm.x * w),
                        "py": int(lm.y * h)
                    })
                    xs.append(int(lm.x * w))
                    ys.append(int(lm.y * h))

                if xs and ys:
                    pad = 20
                    bbox = (
                        max(0, min(xs) - pad),
                        max(0, min(ys) - pad),
                        min(w, max(xs) + pad),
                        min(h, max(ys) + pad)
                    )

        # Draw overlays if requested
        if draw_annotations and detected and landmarks_dict_list:
            self._draw_hand_landmarks(annotated, landmarks_dict_list, bbox, handedness_str)

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0

        if draw_annotations:
            # Draw telemetry badge on top-left
            status_color = (0, 255, 128) if detected else (100, 100, 255)
            status_text = f"HAND: {'DETECTED (' + handedness_str + ')' if detected else 'SEARCHING'}"
            cv2.putText(annotated, status_text, (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2, cv2.LINE_AA)
            cv2.putText(annotated, f"FPS: {smoothed_fps:4.1f} | LAT: {latency_ms:4.1f}ms", (16, 54),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

        return HandDetectionResult(
            detected=detected,
            landmarks=landmarks_dict_list,
            raw_landmarks=raw_pts,
            handedness=handedness_str,
            bbox=bbox,
            fps=smoothed_fps,
            latency_ms=latency_ms,
            annotated_frame=annotated
        )

    def _draw_hand_landmarks(self, frame: np.ndarray, landmarks: List[Dict[str, Any]],
                             bbox: Optional[Tuple[int, int, int, int]], handedness: str) -> None:
        """Draw aesthetic bounding box, skeletal links, and joint nodes."""
        # Draw bounding box
        if bbox:
            bx1, by1, bx2, by2 = bbox
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 200), 1, cv2.LINE_AA)
            cv2.putText(frame, handedness, (bx1, max(15, by1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 1, cv2.LINE_AA)

        # Draw skeleton connections
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            if p1_idx < len(landmarks) and p2_idx < len(landmarks):
                pt1 = (landmarks[p1_idx]["px"], landmarks[p1_idx]["py"])
                pt2 = (landmarks[p2_idx]["px"], landmarks[p2_idx]["py"])
                cv2.line(frame, pt1, pt2, (40, 220, 255), 2, cv2.LINE_AA)

        # Draw joint nodes
        for lm in landmarks:
            px, py = lm["px"], lm["py"]
            idx = lm["index"]
            # Fingertips have distinct glowing circle
            if idx in (4, 8, 12, 16, 20):
                cv2.circle(frame, (px, py), 6, (0, 165, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 8, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (px, py), 4, (0, 255, 120), -1, cv2.LINE_AA)

    def close(self) -> None:
        """Release MediaPipe resources for clean service restarts."""
        if self.landmarker is not None and hasattr(self.landmarker, "close"):
            self.landmarker.close()
        self.landmarker = None
