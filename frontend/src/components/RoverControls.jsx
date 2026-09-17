import React from 'react';
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square, RotateCw, Shuffle, Gamepad2, Sparkles } from 'lucide-react';

export default function RoverControls({ telemetry, onSendCommand, onSetMode }) {
  const activeCmd = telemetry.active_command || 'S';
  const isArmed = telemetry.is_armed;
  const mode = telemetry.mode;
  const isManual = mode === 'MANUAL';

  const handleCommand = (cmd) => {
    onSendCommand(cmd);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-5">
      {/* Header with Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide font-mono flex items-center space-x-2">
            <Gamepad2 className="w-4 h-4 text-cyan-400" />
            <span>ROVER CONTROL DECK</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {isManual 
              ? 'Tactile buttons & Keyboard (W/A/S/D/C/T/SPACE) active' 
              : 'Webcam AI Hand Gesture Recognition active'}
          </p>
        </div>

        {/* Mode Selector Toggle */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => onSetMode('GESTURE')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              !isManual
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>GESTURE MODE</span>
          </button>

          <button
            onClick={() => onSetMode('MANUAL')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              isManual
                ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Gamepad2 className="w-3.5 h-3.5" />
            <span>MANUAL MODE</span>
          </button>
        </div>
      </div>

      {/* Tactile 8-Way Movement Pad */}
      <div className="flex flex-col items-center justify-center space-y-3 py-2">
        {/* Row 1: FORWARD */}
        <button
          onClick={() => handleCommand('W')}
          disabled={!isArmed}
          className={`w-40 py-3.5 rounded-xl border font-mono font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
            activeCmd === 'F'
              ? 'bg-emerald-500 text-slate-950 border-emerald-400 ring-4 ring-emerald-500/30 shadow-lg shadow-emerald-500/40 scale-105'
              : 'bg-slate-950/80 hover:bg-slate-800 text-slate-200 border-slate-800 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
          }`}
        >
          <ArrowUp className="w-4 h-4" />
          <span>FORWARD (W)</span>
        </button>

        {/* Row 2: LEFT - STOP - RIGHT */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleCommand('A')}
            disabled={!isArmed}
            className={`w-32 py-3.5 rounded-xl border font-mono font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeCmd === 'L'
                ? 'bg-cyan-500 text-slate-950 border-cyan-400 ring-4 ring-cyan-500/30 shadow-lg shadow-cyan-500/40 scale-105'
                : 'bg-slate-950/80 hover:bg-slate-800 text-slate-200 border-slate-800 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
            }`}
          >
            <ArrowLeft className="w-4 h-4" />
            <span>LEFT (A)</span>
          </button>

          <button
            onClick={() => handleCommand('SPACE')}
            className={`w-32 py-3.5 rounded-xl border font-mono font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeCmd === 'S'
                ? 'bg-rose-600 text-white border-rose-500 ring-4 ring-rose-600/30 shadow-lg shadow-rose-600/40 scale-105'
                : 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border-rose-800 active:scale-95'
            }`}
          >
            <Square className="w-4 h-4 fill-current" />
            <span>STOP</span>
          </button>

          <button
            onClick={() => handleCommand('D')}
            disabled={!isArmed}
            className={`w-32 py-3.5 rounded-xl border font-mono font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeCmd === 'R'
                ? 'bg-cyan-500 text-slate-950 border-cyan-400 ring-4 ring-cyan-500/30 shadow-lg shadow-cyan-500/40 scale-105'
                : 'bg-slate-950/80 hover:bg-slate-800 text-slate-200 border-slate-800 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
            }`}
          >
            <span>RIGHT (D)</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Row 3: BACKWARD */}
        <button
          onClick={() => handleCommand('B')}
          disabled={!isArmed}
          className={`w-40 py-3.5 rounded-xl border font-mono font-bold text-sm flex items-center justify-center space-x-2 transition-all cursor-pointer ${
            activeCmd === 'B'
              ? 'bg-emerald-500 text-slate-950 border-emerald-400 ring-4 ring-emerald-500/30 shadow-lg shadow-emerald-500/40 scale-105'
              : 'bg-slate-950/80 hover:bg-slate-800 text-slate-200 border-slate-800 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
          }`}
        >
          <ArrowDown className="w-4 h-4" />
          <span>BACKWARD (S)</span>
        </button>

        {/* Row 4: Special Movements (CRAB WALK & 360° TURN) */}
        <div className="flex items-center space-x-3 pt-2">
          <button
            onClick={() => handleCommand('C')}
            disabled={!isArmed}
            className={`w-48 py-3 rounded-xl border font-mono font-bold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeCmd === 'C'
                ? 'bg-purple-500 text-slate-950 border-purple-400 ring-4 ring-purple-500/30 shadow-lg shadow-purple-500/40 scale-105'
                : 'bg-purple-950/40 hover:bg-purple-900/60 text-purple-300 border-purple-800/80 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
            }`}
          >
            <Shuffle className="w-4 h-4" />
            <span>CRAB WALK (C)</span>
          </button>

          <button
            onClick={() => handleCommand('T')}
            disabled={!isArmed}
            className={`w-48 py-3 rounded-xl border font-mono font-bold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeCmd === 'T'
                ? 'bg-amber-500 text-slate-950 border-amber-400 ring-4 ring-amber-500/30 shadow-lg shadow-amber-500/40 scale-105'
                : 'bg-amber-950/40 hover:bg-amber-900/60 text-amber-300 border-amber-800/80 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed'
            }`}
          >
            <RotateCw className="w-4 h-4" />
            <span>360° TURN (T)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
