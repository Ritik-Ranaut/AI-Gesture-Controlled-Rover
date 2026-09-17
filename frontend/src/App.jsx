import React, { useState } from 'react';
import Header from './components/Header';
import CameraFeed from './components/CameraFeed';
import GestureDisplay from './components/GestureDisplay';
import RoverControls from './components/RoverControls';
import RoverWirelessLink from './components/RoverWirelessLink';
import EmergencyStop from './components/EmergencyStop';
import CalibrationPanel from './components/CalibrationPanel';
import SettingsModal from './components/SettingsModal';
import { useRover } from './hooks/useRover';
import { getEsp32Ip } from './services/esp32';
import { AlertTriangle } from 'lucide-react';

export default function App() {
  const {
    connectionState,
    telemetry,
    armRover,
    disarmRover,
    triggerEstop,
    setMode,
    sendManualCommand,
    updateSettings
  } = useRover();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [esp32CamUrl, setEsp32CamUrl] = useState(import.meta.env.VITE_ESP32_CAM_URL || '');
  const [systemSettings, setSystemSettings] = useState(() => {
    try {
      return JSON.parse(window.localStorage.getItem('rover_settings') || '{}');
    } catch {
      return {};
    }
  });

  const handleSaveSettings = (newSettings) => {
    if (newSettings.esp32_cam_url) {
      setEsp32CamUrl(newSettings.esp32_cam_url);
    }
    setSystemSettings(newSettings);
    return updateSettings(newSettings);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-black">
      {/* 1. Header */}
      <Header
        connectionState={connectionState}
        telemetry={telemetry}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* 2. Safety Interlock Notice Banner */}
      {!telemetry.is_armed && !telemetry.estop_active && (
        <div className="bg-amber-950/40 border-b border-amber-900/60 px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center justify-between text-xs font-mono text-amber-300">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>ROVER IN SAFE STANDBY: Motors locked. Enable rover below or perform gestures to inspect recognition.</span>
            </div>
            <button
              onClick={armRover}
              className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold transition-all cursor-pointer ml-2"
            >
              ARM ROVER
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* 3. Dual Camera Views: User Webcam + Rover Live Video */}
       <CameraFeed
  telemetry={telemetry}
  esp32CamUrl={esp32CamUrl}
  onOpenSettings={() => setIsSettingsOpen(true)}
/>

        {/* 4. Large Detected Gesture & Command Display */}
        <GestureDisplay telemetry={telemetry} />

        {/* 5. Dedicated Normal ESP32 Wireless Link & Diagnostics */}
        <RoverWirelessLink
          telemetry={telemetry}
          onUpdateTransport={updateSettings}
          onSendCommand={sendManualCommand}
        />

        {/* 6. Rover Controls Deck & Diagnostics Side-by-Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RoverControls
            telemetry={telemetry}
            onSendCommand={sendManualCommand}
            onSetMode={setMode}
          />

          <CalibrationPanel telemetry={telemetry} />
        </div>

        {/* 6. High-Priority Safety Interlock & Massive Emergency Stop */}
        <EmergencyStop
          telemetry={telemetry}
          onArm={armRover}
          onDisarm={disarmRover}
          onEstop={triggerEstop}
        />
      </main>

      {/* 7. Footer */}
      <footer className="bg-slate-950 border-t border-slate-900 px-4 py-3 text-center text-xs font-mono text-slate-500">
        STAIROVER Robotics Control System &copy; 2026 &bull; Arduino Nano &bull; PCA9685 &bull; BTS7960 &bull; ESP32-CAM &bull; MediaPipe AI
      </footer>

      {/* 8. Settings & Tuning Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaveSettings={handleSaveSettings}
        initialSettings={{
          ...systemSettings,
          esp32_cam_url: esp32CamUrl,
          transport_type: telemetry.transport?.type || 'wifi',
          esp32_ip: getEsp32Ip(),
          com_port: telemetry.transport?.port || 'COM7',
          baud_rate: telemetry.transport?.baudrate || 9600
        }}
      />
    </div>
  );
}
