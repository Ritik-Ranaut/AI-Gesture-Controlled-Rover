import React from 'react';
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Hand, RotateCw, Shuffle, CheckCircle, AlertTriangle } from 'lucide-react';

const GESTURE_CATALOG = [
  { id: 'FORWARD', name: 'FORWARD', cmd: 'F', emoji: '☝️', icon: ArrowUp, desc: 'Point index finger UP' },
  { id: 'BACKWARD', name: 'BACKWARD', cmd: 'B', emoji: '👇', icon: ArrowDown, desc: 'Point index finger DOWN' },
  { id: 'LEFT', name: 'LEFT', cmd: 'L', emoji: '👈', icon: ArrowLeft, desc: 'Point index finger LEFT' },
  { id: 'RIGHT', name: 'RIGHT', cmd: 'R', emoji: '👉', icon: ArrowRight, desc: 'Point index finger RIGHT' },
  { id: 'STOP', name: 'STOP', cmd: 'S', emoji: '✋', icon: Hand, desc: 'Open palm (all fingers up)' },
  { id: 'CRAB_WALK', name: 'CRAB WALK', cmd: 'C', emoji: '🤟', icon: Shuffle, desc: 'Thumb + Index + Pinky up' },
  { id: 'TURN_360', name: '360° TURN', cmd: 'T', emoji: '✊', icon: RotateCw, desc: 'Closed fist (all curled)' },
];

export default function GestureDisplay({ telemetry }) {
  const detected = telemetry.hand_detected;
  const currentGesture = telemetry.confirmed_gesture || 'STOP';
  const activeCommand = telemetry.active_command || 'S';
  const confidencePct = Math.round((telemetry.confidence || 0) * 100);

  const activeMeta = GESTURE_CATALOG.find(g => g.id === currentGesture) || {
    id: 'NONE', name: 'SEARCHING...', cmd: 'S', emoji: '🔍', icon: Hand, desc: 'Place hand in camera view'
  };

  const IconComp = activeMeta.icon;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-4">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-inner border transition-all duration-300 ${
            detected 
              ? 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60 shadow-cyan-500/20 ring-2 ring-cyan-500/30' 
              : 'bg-slate-800 text-slate-500 border-slate-700'
          }`}>
            <span>{detected ? activeMeta.emoji : '🔍'}</span>
          </div>
          <div>
            <div className="text-xs uppercase font-mono tracking-widest text-slate-400">
              DETECTED GESTURE
            </div>
            <div className="text-2xl font-black text-white tracking-wide font-mono flex items-center space-x-2">
              <span>{detected ? activeMeta.name : 'NO HAND DETECTED'}</span>
              {detected && (
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {telemetry.orientation || 'UP'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Rover Command & Confidence Readouts */}
        <div className="flex items-center space-x-4">
          <div className="bg-slate-950 border border-slate-800 px-4 py-2 rounded-xl">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">COMMAND</div>
            <div className="text-xl font-black font-mono text-emerald-400 tracking-wider">
              {activeCommand} <span className="text-xs text-slate-500 font-normal">({activeMeta.name})</span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 px-4 py-2 rounded-xl min-w-[120px]">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">CONFIDENCE</div>
            <div className="flex items-center space-x-2">
              <div className="text-xl font-black font-mono text-cyan-300">
                {confidencePct}%
              </div>
              <div className="w-12 bg-slate-800 h-2 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-300 ${
                    confidencePct >= 80 ? 'bg-emerald-400' : confidencePct >= 60 ? 'bg-amber-400' : 'bg-rose-500'
                  }`}
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Supported Gestures Row */}
      <div>
        <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Supported Gestures & Live Mapping</span>
          <span className="text-slate-500 text-[10px]">Filter: 3-Frame Confirmation</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
          {GESTURE_CATALOG.map((g) => {
            const isActive = detected && currentGesture === g.id;
            return (
              <div
                key={g.id}
                className={`p-2.5 rounded-xl border flex flex-col items-center text-center transition-all duration-200 ${
                  isActive
                    ? 'bg-cyan-950/70 border-cyan-500 ring-2 ring-cyan-500/40 shadow-lg shadow-cyan-950 scale-102'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400'
                }`}
              >
                <div className="text-2xl mb-1">{g.emoji}</div>
                <div className={`text-xs font-bold font-mono ${isActive ? 'text-cyan-300' : 'text-slate-300'}`}>
                  {g.name}
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  CMD: <strong className={isActive ? 'text-emerald-400' : 'text-slate-400'}>{g.cmd}</strong>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
