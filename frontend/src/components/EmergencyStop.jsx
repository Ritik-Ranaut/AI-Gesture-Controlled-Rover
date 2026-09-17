import React from 'react';
import { AlertOctagon, ShieldCheck, ShieldAlert, Power } from 'lucide-react';

export default function EmergencyStop({ telemetry, onArm, onDisarm, onEstop }) {
  const isArmed = telemetry.is_armed;
  const isEstop = telemetry.estop_active;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
      {/* Safety Status & Arm Switch */}
      <div className="flex items-center space-x-4 w-full md:w-auto">
        <div className={`p-3 rounded-2xl border ${
          isEstop
            ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
            : isArmed
            ? 'bg-emerald-950/80 border-emerald-500 text-emerald-400'
            : 'bg-amber-950/80 border-amber-500 text-amber-400'
        }`}>
          {isEstop ? (
            <ShieldAlert className="w-8 h-8" />
          ) : isArmed ? (
            <ShieldCheck className="w-8 h-8" />
          ) : (
            <ShieldAlert className="w-8 h-8" />
          )}
        </div>

        <div>
          <div className="text-xs uppercase font-mono tracking-wider text-slate-400">
            ROVER MOTOR INTERLOCK
          </div>
          <div className="text-lg font-bold font-mono text-white">
            {isEstop ? (
              <span className="text-rose-400">EMERGENCY STOP TRIPPED</span>
            ) : isArmed ? (
              <span className="text-emerald-400">MOTORS ENABLED (LIVE)</span>
            ) : (
              <span className="text-amber-400">ROVER DISABLED (SAFE)</span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {isEstop
              ? 'Click Enable Rover below to reset emergency stop latch.'
              : isArmed
              ? 'Commands are active. 500ms watchdog protection armed.'
              : 'Physical motors locked. Click Enable to begin.'}
          </p>
        </div>
      </div>

      {/* Action Buttons: Arm/Disarm Toggle + HUGE Emergency Stop */}
      <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
        {isArmed ? (
          <button
            onClick={onDisarm}
            className="px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-mono text-xs font-bold flex items-center space-x-2 transition-all cursor-pointer"
          >
            <Power className="w-4 h-4 text-amber-400" />
            <span>DISABLE ROVER</span>
          </button>
        ) : (
          <button
            onClick={onArm}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono text-xs font-extrabold flex items-center space-x-2 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer active:scale-95"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-100" />
            <span>ENABLE ROVER</span>
          </button>
        )}

        {/* Massive Emergency Stop Button */}
        <button
          onClick={onEstop}
          className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-500 hover:to-red-600 text-white font-mono text-sm font-black tracking-wider flex items-center space-x-2.5 shadow-xl shadow-rose-600/40 border-2 border-rose-400 active:scale-90 transition-all cursor-pointer ring-4 ring-rose-500/20"
        >
          <AlertOctagon className="w-5 h-5 fill-current text-white animate-pulse" />
          <span>EMERGENCY STOP</span>
        </button>
      </div>
    </div>
  );
}
