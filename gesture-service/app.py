"""FastAPI Application serving WebSocket telemetry, MJPEG video streaming, and REST APIs."""

import asyncio
import json
import time
import threading
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
import serial.tools.list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config, RoverConfig
from gesture_detector import GestureDetector, HandDetectionResult
from gesture_classifier import GestureClassifier, GestureClassificationResult
from command_controller import CommandController


app = FastAPI(
    title="Stair-Climbing Rover Gesture Control API",
    description="Real-time MediaPipe Hand Gesture Recognition & Robotics Telemetry Server",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core subsystems
detector: Optional[GestureDetector] = None
classifier: Optional[GestureClassifier] = None
controller: Optional[CommandController] = None

# Video streaming globals
video_capture: Optional[cv2.VideoCapture] = None
latest_frame_lock = threading.Lock()
latest_annotated_jpeg: Optional[bytes] = None
latest_telemetry_payload: Dict[str, Any] = {}
camera_running = False
camera_thread: Optional[threading.Thread] = None

# Active WebSocket connections
connected_clients: List[WebSocket] = []


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


class CommandRequest(BaseModel):
    command: str


class ModeRequest(BaseModel):
    mode: str


def get_available_com_ports() -> List[Dict[str, str]]:
    """Scan and list all available serial COM ports."""
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            "device": port.device,
            "description": port.description,
            "hwid": port.hwid
        })
    return ports


def create_standby_frame(message="SEARCHING WEBCAM..."):
    """Generate a clean dark diagnostic frame when camera is starting or offline."""
    img = np.zeros((config.frame_height, config.frame_width, 3), dtype=np.uint8)
    # Subtle dark blue gradient grid
    for y in range(0, config.frame_height, 40):
        cv2.line(img, (0, y), (config.frame_width, y), (18, 24, 38), 1)
    for x in range(0, config.frame_width, 40):
        cv2.line(img, (x, 0), (x, config.frame_height), (18, 24, 38), 1)
    
    cv2.rectangle(img, (40, 40), (config.frame_width - 40, config.frame_height - 40), (0, 180, 255), 1)
    cv2.putText(img, "STAIROVER VISION SYSTEM", (60, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
    cv2.putText(img, message, (60, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(img, time.strftime("%Y-%m-%d %H:%M:%S"), (60, config.frame_height - 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 140, 160), 1)
    ret, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return buf.tobytes() if ret else None


def open_camera(target_index=0):
    """Open camera using DirectShow on Windows for instant response, with index fallback."""
    import sys
    cap = None
    indices_to_try = [target_index] + [i for i in [0, 1, 2] if i != target_index]
    
    for idx in indices_to_try:
        print(f"[INFO] Attempting to open camera at index {idx}...")
        if sys.platform == "win32":
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            except Exception:
                cap = cv2.VideoCapture(idx)
        else:
            cap = cv2.VideoCapture(idx)
            
        if cap and cap.isOpened():
            # Prefer the newest frame over an accumulated driver buffer.
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Test a quick read
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
                cap.set(cv2.CAP_PROP_FPS, config.target_fps)
                config.actual_camera_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or test_frame.shape[1])
                config.actual_camera_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or test_frame.shape[0])
                config.actual_camera_fps = round(float(cap.get(cv2.CAP_PROP_FPS) or 0.0), 1)
                print(
                    f"[INFO] Camera opened successfully on index {idx} "
                    f"({config.actual_camera_width}x{config.actual_camera_height} "
                    f"@ {config.actual_camera_fps:g} FPS)"
                )
                config.camera_index = idx
                return cap
            else:
                cap.release()
                
    print("[WARNING] Could not open any hardware webcam. Entering simulated standby mode.")
    return None


def video_processing_worker():
    """Background worker thread capturing camera frames and running gesture pipeline."""
    global video_capture, camera_running, latest_annotated_jpeg, latest_telemetry_payload

    # Provide initial standby frame immediately
    with latest_frame_lock:
        latest_annotated_jpeg = create_standby_frame("INITIALIZING CAMERA...")

    video_capture = open_camera(config.camera_index)
    camera_started_at = time.perf_counter()
    camera_frame_count = 0
    camera_fps = 0.0
    frame_number = 0
    last_capture_at = None
    frame_interval_ms = 0.0
    last_gesture = "NONE"
    gesture_change_at = None

    while camera_running:
        if video_capture and video_capture.isOpened():
            success, frame = video_capture.read()
            if not success or frame is None:
                time.sleep(0.05)
                continue

            camera_frame_count += 1
            frame_number += 1
            captured_at = time.perf_counter()
            if last_capture_at is not None:
                frame_interval_ms = (captured_at - last_capture_at) * 1000.0
            last_capture_at = captured_at
            camera_elapsed = time.perf_counter() - camera_started_at
            if camera_elapsed >= 0.5:
                camera_fps = camera_frame_count / camera_elapsed
                camera_started_at = time.perf_counter()
                camera_frame_count = 0

            # Flip horizontally for intuitive mirror experience
            frame = cv2.flip(frame, 1)

            # Detection stays full-rate; preview annotation/JPEG work is sampled.
            draw_frame = frame_number % max(1, config.video_encode_every_n_frames) == 0
            detect_res: HandDetectionResult = detector.process_frame(frame, draw_annotations=draw_frame)

            # Step 2: Classify gesture
            classification_started = time.perf_counter()
            if detect_res.detected:
                class_res: GestureClassificationResult = classifier.classify(
                    detect_res.landmarks, handedness=detect_res.handedness
                )
            else:
                class_res = GestureClassificationResult(gesture="NONE", command="S", confidence=0.0)
            classification_latency_ms = (time.perf_counter() - classification_started) * 1000.0

            if class_res.gesture != last_gesture:
                gesture_change_at = time.perf_counter()
                last_gesture = class_res.gesture

            # Step 3: Command Controller state machine & safety watchdog
            telemetry = controller.process_gesture_frame(detect_res.detected, class_res)

            # Enrich telemetry with detection data
            telemetry.update({
                "hand_detected": detect_res.detected,
                "handedness": detect_res.handedness,
                "landmarks": detect_res.landmarks,
                "finger_states": class_res.finger_states,
                "orientation": class_res.orientation,
                "fps": round(detect_res.fps, 1),
                "latency_ms": round(detect_res.latency_ms, 1),
                "frame_interval_ms": round(frame_interval_ms, 1),
                "classification_latency_ms": round(classification_latency_ms, 2),
                "gesture_change_age_ms": round((time.perf_counter() - gesture_change_at) * 1000.0, 1) if gesture_change_at else 0.0,
                "detection_fps": round(detect_res.fps, 1),
                "camera_fps": round(camera_fps, 1),
                "camera_width": config.actual_camera_width,
                "camera_height": config.actual_camera_height,
                "camera_configured_fps": config.actual_camera_fps,
                "timestamp": time.time()
            })

            with latest_frame_lock:
                latest_telemetry_payload = telemetry

            # Draw gesture badge on annotated frame
            if draw_frame and detect_res.annotated_frame is not None:
                hud = detect_res.annotated_frame
                g_text = f"GESTURE: {class_res.gesture} ({class_res.confidence * 100:.0f}%)"
                c_text = f"CMD: {controller.active_command} | {'ARMED' if controller.is_armed else 'DISARMED'}"
                color = (0, 255, 0) if controller.is_armed else (0, 165, 255)
                cv2.putText(hud, g_text, (16, hud.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.putText(hud, c_text, (16, hud.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

                # Encode frame as JPEG for MJPEG stream
                ret, buffer = cv2.imencode(".jpg", hud, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if ret:
                    with latest_frame_lock:
                        latest_annotated_jpeg = buffer.tobytes()
        else:
            # Standby mode when camera is unplugged or unavailable
            with latest_frame_lock:
                latest_annotated_jpeg = create_standby_frame("WEBCAM DISCONNECTED - CHECK USB / PERMISSIONS")
            time.sleep(0.5)
            # Periodically retry opening camera
            video_capture = open_camera(config.camera_index)

    if video_capture:
        video_capture.release()
        print("[INFO] Camera released.")


@app.on_event("startup")
async def startup_event():
    """Initialize subsystems on server startup."""
    global detector, classifier, controller, camera_running, camera_thread, latest_telemetry_payload
    print("[INFO] Starting Stair-Climbing Rover Gesture Service...")
    detector = GestureDetector()
    classifier = GestureClassifier(config)
    controller = CommandController(config)
    latest_telemetry_payload = controller.get_telemetry()

    camera_running = True
    camera_thread = threading.Thread(target=video_processing_worker, daemon=True)
    camera_thread.start()

    # Start background broadcast task
    asyncio.create_task(broadcast_telemetry_loop())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    global camera_running, controller, camera_thread, detector
    print("[INFO] Shutting down Gesture Service...")
    camera_running = False
    if camera_thread and camera_thread.is_alive():
        camera_thread.join(timeout=2.0)
    if controller:
        controller.close()
    if detector:
        detector.close()
        detector = None


async def broadcast_telemetry_loop():
    """Periodically broadcast latest telemetry to all connected WebSocket clients."""
    while True:
        await asyncio.sleep(0.04)  # ~25 Hz update rate
        if connected_clients and latest_telemetry_payload:
            payload_str = json.dumps(latest_telemetry_payload)
            disconnected = []
            for client in connected_clients:
                try:
                    await client.send_text(payload_str)
                except Exception:
                    disconnected.append(client)

            for dead in disconnected:
                if dead in connected_clients:
                    connected_clients.remove(dead)


# --- REST ENDPOINTS ---

@app.get("/api/health")
def health_check():
    """Lightweight readiness probe used by the dashboard before opening WebSocket telemetry."""
    return {"status": "ok", "ready": controller is not None}


@app.get("/api/status")
def get_status():
    """Get current status of rover, controller, and transport."""
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    with latest_frame_lock:
        live_telemetry = dict(latest_telemetry_payload)
    if not live_telemetry:
        live_telemetry = controller.get_telemetry()
    return {
        "telemetry": live_telemetry,
        "config": {
            "camera_index": config.camera_index,
            "transport_type": config.transport_type,
            "com_port": config.com_port,
            "baud_rate": config.baud_rate,
            "confidence_threshold": config.confidence_threshold,
            "confirmation_frames": config.confirmation_frames,
            "command_timeout_ms": config.command_timeout_ms,
            "command_refresh_interval_ms": config.command_refresh_interval_ms,
            "esp32_cam_url": config.esp32_cam_url,
            "gesture_mappings": config.gesture_mappings
        },
        "ports": get_available_com_ports()
    }


@app.get("/api/ports")
def list_ports():
    """List detected COM ports."""
    return {"ports": get_available_com_ports()}


@app.post("/api/arm")
def arm_rover():
    """Enable rover motion commands."""
    if controller:
        controller.arm_rover()
        return {"status": "success", "armed": True}
    raise HTTPException(status_code=503, detail="Controller not initialized")


@app.post("/api/disarm")
def disarm_rover():
    """Disable rover motion commands."""
    if controller:
        controller.disarm_rover()
        return {"status": "success", "armed": False}
    raise HTTPException(status_code=503, detail="Controller not initialized")


@app.post("/api/estop")
def emergency_stop():
    """Emergency Stop rover immediately."""
    if controller:
        controller.emergency_stop()
        return {"status": "emergency_stop_triggered"}
    raise HTTPException(status_code=503, detail="Controller not initialized")


@app.post("/api/mode")
def set_mode(req: ModeRequest):
    """Change control mode (GESTURE or MANUAL)."""
    if controller:
        controller.set_mode(req.mode)
        return {"status": "success", "mode": controller.mode}
    raise HTTPException(status_code=503, detail="Controller not initialized")


@app.post("/api/command")
def send_manual_command(req: CommandRequest):
    """Execute a manual direction command."""
    if controller:
        controller.process_manual_command(req.command)
        return {"status": "success", "command": req.command}
    raise HTTPException(status_code=503, detail="Controller not initialized")


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    """Update runtime configuration settings."""
    config.update(req.settings)
    # If transport settings changed, re-initialize transport
    transport_keys = ["transport_type", "com_port", "baud_rate", "esp32_ip", "esp32_port", "wifi_host", "wifi_port"]
    if any(k in req.settings for k in transport_keys):
        if controller:
            controller.update_transport(
                config.transport_type,
                com_port=config.com_port,
                baud_rate=config.baud_rate,
                esp32_ip=config.esp32_ip,
                esp32_port=config.esp32_port,
                wifi_host=config.wifi_host,
                wifi_port=config.wifi_port
            )
    return {"status": "success", "config": config.__dict__}


@app.get("/api/esp32/test")
def test_esp32_link(ip: Optional[str] = None, port: Optional[int] = None):
    """Run Two-Tier Connection Test: Laptop -> ESP32 and ESP32 -> Arduino."""
    from transport.wifi_transport import WiFiTransport
    target_ip = ip or config.esp32_ip
    target_port = port or config.esp32_port
    
    if controller and isinstance(controller.transport, WiFiTransport) and controller.transport.host == target_ip:
        return controller.transport.test_connection()
    else:
        temp = WiFiTransport(host=target_ip, port=target_port)
        return temp.test_connection()


@app.get("/api/esp32/status")
def get_esp32_status(ip: Optional[str] = None, port: Optional[int] = None):
    """Query live ESP32 status endpoint."""
    target_ip = ip or config.esp32_ip
    target_port = port or config.esp32_port
    import requests
    try:
        resp = requests.get(f"http://{target_ip}:{target_port}/status", timeout=1.0)
        if resp.status_code == 200:
            return {"connected": True, "data": resp.json()}
        return {"connected": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def proxy_esp32_request(path: str, ip: Optional[str], port: Optional[int], params: Dict[str, Any]):
    """Relay ESP32 HTTP requests so browsers do not depend on ESP32 CORS support."""
    import requests

    target_ip = ip or config.esp32_ip
    target_port = port or config.esp32_port
    try:
        response = requests.get(
            f"http://{target_ip}:{target_port}{path}",
            params=params,
            timeout=3.0,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        return JSONResponse(status_code=response.status_code, content=payload)
    except requests.RequestException as error:
        return JSONResponse(
            status_code=504,
            content={"status": "error", "message": f"ESP32 request failed: {error}"},
        )


@app.get("/api/esp32/proxy/status")
def proxy_esp32_status(ip: Optional[str] = None, port: Optional[int] = None):
    return proxy_esp32_request("/status", ip, port, {})


@app.get("/api/esp32/proxy/wifi")
def proxy_esp32_wifi(ip: Optional[str] = None, port: Optional[int] = None):
    return proxy_esp32_request("/wifi", ip, port, {})


@app.get("/api/esp32/proxy/servo")
def proxy_esp32_servo(angle: int, ip: Optional[str] = None, port: Optional[int] = None):
    return proxy_esp32_request("/servo", ip, port, {"angle": angle})


@app.get("/api/esp32/proxy/command")
def proxy_esp32_command(command: str, ip: Optional[str] = None, port: Optional[int] = None):
    return proxy_esp32_request("/command", ip, port, {"cmd": command})


# --- MJPEG VIDEO STREAM ENDPOINT ---

def generate_mjpeg_stream():
    """Generator streaming JPEG frames with boundary separators."""
    while True:
        with latest_frame_lock:
            frame_data = latest_annotated_jpeg

        if frame_data is None:
            frame_data = create_standby_frame("STANDBY - INITIALIZING FEED...")

        if frame_data is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")
        time.sleep(0.033)


@app.get("/video_feed")
def video_feed():
    """Endpoint serving real-time annotated webcam feed as MJPEG."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# --- WEBSOCKET ENDPOINT ---

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Bidirectional WebSocket connection for live telemetry and commands."""
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"[INFO] WebSocket client connected. Total clients: {len(connected_clients)}")

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                action = msg.get("action")
                if action == "arm":
                    controller.arm_rover()
                elif action == "disarm":
                    controller.disarm_rover()
                elif action == "estop":
                    controller.emergency_stop()
                elif action == "set_mode":
                    controller.set_mode(msg.get("mode", "GESTURE"))
                elif action == "manual_cmd":
                    controller.process_manual_command(msg.get("command", "S"))
                elif action == "update_settings":
                    new_settings = msg.get("settings", {})
                    config.update(new_settings)
                    transport_keys = {
                        "transport_type", "com_port", "baud_rate", "esp32_ip",
                        "esp32_port", "wifi_host", "wifi_port"
                    }
                    if any(k in new_settings for k in transport_keys):
                        controller.update_transport(
                            config.transport_type,
                            com_port=config.com_port,
                            baud_rate=config.baud_rate,
                            esp32_ip=config.esp32_ip,
                            esp32_port=config.esp32_port,
                            wifi_host=config.wifi_host,
                            wifi_port=config.wifi_port
                        )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"[INFO] WebSocket client disconnected. Remaining: {len(connected_clients)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.server_host, port=config.server_port)
