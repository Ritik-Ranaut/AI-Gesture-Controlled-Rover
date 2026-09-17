import React, { useState } from 'react';
import { Activity, Terminal, CheckCircle2, XCircle, Sliders, Cpu } from 'lucide-react';

export default function CalibrationPanel({ telemetry }) {
  const [activeTab, setActiveTab] = useState('fingers'); // 'fingers' | 'logs'
  const fingerStates = telemetry.finger_states || {};
  const recentLogs = telemetry.recent_logs || [];

  const fingers = [
    { key: 'thumb', label: 'THUMB', id: '1-4' },
    { key: 'index', label: 'INDEX', id: '5-8' },
    { key: 'middle', label: 'MIDDLE', id: '9-12' },
    { key: 'ring', label: 'RING', id: '13-16' },
    { key: 'pinky', label: 'PINKY', id: '17-20' }
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-4">
      {/* Header with Tab Navigation */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white tracking-wide font-mono">
            CALIBRATION & DIAGNOSTICS
          </h3>
        </div>

        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('fingers')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all cursor-pointer ${
              activeTab === 'fingers'
                ? 'bg-slate-800 text-cyan-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Finger States
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all cursor-pointer ${
              activeTab === 'logs'
                ? 'bg-slate-800 text-cyan-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Command Log ({recentLogs.length})
          </button>
        </div>
      </div>

      {activeTab === 'fingers' ? (
        <div className="space-y-4">
          {/* Finger State Cards */}
          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2">
              MediaPipe Anatomical Joint Extension
            </div>
            <div className="grid grid-cols-5 gap-2">
              {fingers.map((f) => {
                const isExtended = Boolean(fingerStates[f.key]);
                return (
                  <div
                    key={f.key}
                    className={`p-3 rounded-xl border flex flex-col items-center text-center transition-all ${
                      isExtended
                        ? 'bg-emerald-950/50 border-emerald-500/60 shadow-sm shadow-emerald-500/10'
                        : 'bg-slate-950/60 border-slate-800'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-slate-500 mb-1">{f.id}</div>
                    <div className="text-xs font-bold font-mono text-slate-200 mb-1.5">{f.label}</div>
                    {isExtended ? (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>UP</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-medium text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        <XCircle className="w-3 h-3" />
                        <span>DOWN</span>
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Diagnostic Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-3 pt-2">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">CAMERA FPS</div>
              <div className="text-lg font-bold font-mono text-cyan-400">{telemetry.camera_fps || 0}</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">DETECTION FPS</div>
              <div className="text-lg font-bold font-mono text-cyan-400">{telemetry.detection_fps || telemetry.fps || 0}</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">RESOLUTION</div>
              <div className="text-lg font-bold font-mono text-cyan-400">
                {telemetry.camera_width && telemetry.camera_height
                  ? `${telemetry.camera_width}x${telemetry.camera_height} @ ${telemetry.camera_configured_fps || '?'} FPS`
                  : 'N/A'}
              </div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">LATENCY</div>
              <div className="text-lg font-bold font-mono text-purple-400">{telemetry.latency_ms || 0} ms</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">FRAME INTERVAL</div>
              <div className="text-lg font-bold font-mono text-purple-400">{telemetry.frame_interval_ms || 0} ms</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">COMMAND RTT</div>
              <div className="text-lg font-bold font-mono text-amber-400">{telemetry.command_latency_ms || 0} ms</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">GESTURE TO CMD</div>
              <div className="text-lg font-bold font-mono text-amber-400">{telemetry.gesture_to_command_latency_ms || 0} ms</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">ORIENTATION</div>
              <div className="text-lg font-bold font-mono text-emerald-400">{telemetry.orientation || 'NONE'}</div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase">HANDEDNESS</div>
              <div className="text-lg font-bold font-mono text-slate-300">{telemetry.handedness || 'NONE'}</div>
            </div>
          </div>
        </div>
      ) : (
        /* Command Log Tab */
        <div className="space-y-2">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Transmission Log</span>
            <span className="text-slate-500 text-[10px]">Real-time Watchdog + Transport Echo</span>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs max-h-48 overflow-y-auto space-y-1">
            {recentLogs.length > 0 ? (
              recentLogs.slice().reverse().map((log, idx) => (
                <div key={idx} className="flex items-center justify-between py-1 border-b border-slate-900 last:border-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 text-[10px]">{log.time_str || '00:00:00'}</span>
                    <span className={`font-bold px-1.5 py-0.2 rounded text-[11px] ${
                      log.command === 'S' 
                        ? 'bg-rose-950 text-rose-300 border border-rose-800' 
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      CMD: {log.command}
                    </span>
                    <span className="text-slate-400 text-[11px]">via {log.source}</span>
                  </div>
                  <span className="text-slate-500 text-[10px]">
                    Conf: {Math.round((log.confidence || 0) * 100)}%
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center text-slate-600 py-4">No commands recorded yet.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
