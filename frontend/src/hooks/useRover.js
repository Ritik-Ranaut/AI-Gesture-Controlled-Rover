import { useState, useEffect, useCallback } from 'react';
import { wsClient } from '../services/websocket';

export function useRover() {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [telemetry, setTelemetry] = useState({
    hand_detected: false,
    handedness: 'Unknown',
    finger_states: { thumb: false, index: false, middle: false, ring: false, pinky: false },
    orientation: 'NONE',
    active_command: 'S',
    confirmed_gesture: 'STOP',
    confidence: 0,
    mode: 'GESTURE',
    is_armed: false,
    estop_active: false,
    fps: 0,
    camera_fps: 0,
    camera_width: 0,
    camera_height: 0,
    camera_configured_fps: 0,
    frame_interval_ms: 0,
    classification_latency_ms: 0,
    gesture_to_command_latency_ms: 0,
    detection_fps: 0,
    latency_ms: 0,
    command_latency_ms: 0,
    transport: { type: 'mock', connected: false, port: '', baudrate: 9600 },
    recent_logs: []
  });

  useEffect(() => {
    wsClient.connect();
    const latestTelemetryRef = { current: null };
    let renderTimer = null;

    const unsubscribeState = wsClient.onStateChange((state) => {
      setConnectionState(state);
    });

    const unsubscribeData = wsClient.subscribe((data) => {
      latestTelemetryRef.current = data;
      if (renderTimer !== null) return;

      // Keep React at a readable 10 Hz; gesture processing remains in Python
      // at camera speed and is not delayed by dashboard rendering.
      renderTimer = window.setTimeout(() => {
        renderTimer = null;
        const next = latestTelemetryRef.current;
        if (!next) return;
        setTelemetry((prev) => ({
          ...prev,
          ...next,
          finger_states: next.finger_states || prev.finger_states,
          transport: next.transport || prev.transport,
          recent_logs: next.recent_logs || prev.recent_logs
        }));
      }, 100);
    });

    return () => {
      unsubscribeState();
      unsubscribeData();
      if (renderTimer !== null) window.clearTimeout(renderTimer);
    };
  }, []);

  const armRover = useCallback(() => {
    wsClient.sendArm();
  }, []);

  const disarmRover = useCallback(() => {
    wsClient.sendDisarm();
  }, []);

  const triggerEstop = useCallback(() => {
    wsClient.sendEstop();
  }, []);

  const setMode = useCallback((mode) => {
    wsClient.sendMode(mode);
  }, []);

  const sendManualCommand = useCallback((cmd) => {
    wsClient.sendManualCommand(cmd);
  }, []);

  const updateSettings = useCallback((settings) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('rover_settings', JSON.stringify(settings));
    }

    return fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings })
    }).then(async (response) => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `Backend returned HTTP ${response.status}.`);
      }
      return data;
    });
  }, []);

  // Keyboard shortcut handler for Manual Mode
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger if user is typing in an input field
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        sendManualCommand('SPACE');
        return;
      }

      // Emergency stop global shortcut: Escape
      if (e.key === 'Escape') {
        triggerEstop();
        return;
      }

      if (telemetry.mode !== 'MANUAL') {
        return;
      }

      const key = e.key.toUpperCase();
      if (['W', 'S', 'A', 'D', 'C', 'T'].includes(key)) {
        e.preventDefault();
        sendManualCommand(key);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        sendManualCommand('W');
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        sendManualCommand('S');
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        sendManualCommand('A');
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        sendManualCommand('D');
      }
    };

    const handleKeyUp = (e) => {
      if (telemetry.mode !== 'MANUAL') return;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      const key = e.key.toUpperCase();
      // On key release in manual mode, send STOP if moving
      if (['W', 'S', 'A', 'D', 'ARROWUP', 'ARROWDOWN', 'ARROWLEFT', 'ARROWRIGHT'].includes(key)) {
        sendManualCommand('SPACE');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [telemetry.mode, sendManualCommand, triggerEstop]);

  return {
    connectionState,
    telemetry,
    armRover,
    disarmRover,
    triggerEstop,
    setMode,
    sendManualCommand,
    updateSettings
  };
}
