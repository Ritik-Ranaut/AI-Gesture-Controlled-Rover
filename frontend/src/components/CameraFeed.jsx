import React, { useState } from 'react';
import { Camera, Video, RefreshCw, ExternalLink, Maximize2, Shield, Eye, Play, PowerOff } from 'lucide-react';

export default function CameraFeed({ telemetry, esp32CamUrl, onOpenSettings }) {
  const [roverCamError, setRoverCamError] = useState(false);
  const [roverCamKey, setRoverCamKey] = useState(Date.now());
  const [isRoverCamEnabled, setIsRoverCamEnabled] = useState(false);
  const [handCamError, setHandCamError] = useState(false);

  const handleRefreshRoverCam = () => {
    setRoverCamError(false);
    setIsRoverCamEnabled(true);
    setRoverCamKey(Date.now());
  };

  const handDetected = telemetry.hand_detected;
  const confidencePct = Math.round((telemetry.confidence || 0) * 100);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* --- PANEL 1: USER HAND CAMERA --- */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
        {/* Header */}
        <div className="bg-slate-950/90 px-4 py-2.5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Camera className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-100 tracking-wide font-mono">
              USER HAND CAMERA
            </h2>
            <span className="text-[10px] bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/60 font-mono">
              OPENCV + MEDIAPIPE
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
              handDetected 
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' 
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}>
              {handDetected ? `● HAND DETECTED (${telemetry.handedness || 'RIGHT'})` : '○ SEARCHING HAND'}
            </span>
          </div>
        </div>

        {/* Video Display Container */}
        <div className="relative bg-slate-950 aspect-video w-full flex items-center justify-center overflow-hidden group">
          {!handCamError ? (
            <img
              src="/video_feed"
              alt="Hand Gesture Recognition Feed"
              className="w-full h-full object-contain"
              onError={() => setHandCamError(true)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-center p-6 space-y-3">
              <Camera className="w-12 h-12 text-slate-600 animate-pulse" />
              <div>
                <p className="text-sm font-semibold text-slate-300">Webcam Feed Offline</p>
                <p className="text-xs text-slate-500 max-w-xs mt-1">
                  Make sure gesture-service is running and your webcam is connected.
                </p>
              </div>
              <button
                onClick={() => setHandCamError(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-400 border border-slate-700 flex items-center space-x-1.5 cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Stream</span>
              </button>
            </div>
          )}

          {/* Real-time Overlays on bottom */}
          <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between pointer-events-none">
            {/* Telemetry pill */}
            <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-2.5 py-1 rounded-md text-[11px] font-mono text-slate-300 flex items-center space-x-3">
              <span>FPS: <strong className="text-cyan-400">{telemetry.fps || 0}</strong></span>
              <span className="text-slate-600">|</span>
              <span>LATENCY: <strong className="text-purple-400">{telemetry.latency_ms || 0}ms</strong></span>
            </div>

            {/* Confidence pill */}
            {handDetected && (
              <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-2.5 py-1 rounded-md text-[11px] font-mono flex items-center space-x-1.5">
                <span className="text-slate-400">CONF:</span>
                <span className={`font-bold ${
                  confidencePct >= 80 ? 'text-emerald-400' : confidencePct >= 60 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {confidencePct}%
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* --- PANEL 2: ROVER CAMERA (ESP32-CAM) --- */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
        {/* Header */}
        <div className="bg-slate-950/90 px-4 py-2.5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Video className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-slate-100 tracking-wide font-mono">
              ROVER CAMERA
            </h2>
            <span className="text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800/60 font-mono">
              ESP32-CAM
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefreshRoverCam}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all cursor-pointer"
              title="Refresh Stream"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onOpenSettings}
              className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 underline cursor-pointer"
            >
              Configure IP
            </button>
          </div>
        </div>

        {/* Video Stream Container */}
        <div className="relative bg-slate-950 aspect-video w-full flex items-center justify-center overflow-hidden">
          {isRoverCamEnabled && !roverCamError && esp32CamUrl ? (
            <img
              key={roverCamKey}
              src={esp32CamUrl}
              alt="ESP32-CAM Rover Stream"
              className="w-full h-full object-contain"
              onError={() => setRoverCamError(true)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-center p-6 space-y-3">
              <Video className="w-12 h-12 text-slate-600 animate-pulse" />
              <div>
                <p className="text-sm font-semibold text-slate-300">
                  {roverCamError ? 'ESP32-CAM Stream Offline' : 'Rover Eye Standby'}
                </p>
                <p className="text-xs text-slate-500 max-w-xs mt-1 font-mono">
                  {esp32CamUrl || 'URL not configured'}
                </p>
                <p className="text-[11px] text-slate-600 mt-1">
                  Ensure ESP32-CAM is powered and connected to Wi-Fi.
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleRefreshRoverCam}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-mono text-slate-950 font-bold border border-emerald-500 flex items-center space-x-1.5 cursor-pointer shadow-md shadow-emerald-600/20"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Rover Stream</span>
                </button>
                <button
                  onClick={onOpenSettings}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 border border-slate-700 cursor-pointer"
                >
                  Change IP
                </button>
              </div>
            </div>
          )}

          {/* Bottom telemetry overlay */}
          <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between pointer-events-none">
            <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-2.5 py-1 rounded-md text-[11px] font-mono text-slate-300 flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${isRoverCamEnabled && !roverCamError ? 'bg-emerald-400 animate-pulse' : 'bg-amber-500'}`} />
              <span>ROVER EYE: {isRoverCamEnabled && !roverCamError ? 'LIVE' : 'STANDBY'}</span>
            </div>

            <div className="bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-2.5 py-1 rounded-md text-[11px] font-mono text-slate-400 truncate max-w-[200px]">
              {esp32CamUrl}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
