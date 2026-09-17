import React, { useState, useEffect } from 'react';
import { Bot, Radio, ShieldAlert, ShieldCheck, Settings, Cpu, Activity } from 'lucide-react';

export default function Header({ connectionState, telemetry, onOpenSettings }) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour12: false }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const isWsConnected = connectionState === 'connected';
  const isHardwareConnected = telemetry.transport?.connected;

  return (
    <header className="bg-slate-900/90 border-b border-slate-800 backdrop-blur-md px-4 py-3 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 ring-1 ring-cyan-400/30">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-extrabold tracking-wider text-white font-mono">
                STAIROVER
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono">
                v1.0-PRO
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Hand Gesture Robotics Mission Control</p>
          </div>
        </div>

        {/* Real-time Status Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Backend Connection */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
            isWsConnected 
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50' 
              : 'bg-rose-950/60 text-rose-300 border-rose-800/50'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span>{isWsConnected ? 'SERVICE: ONLINE' : 'SERVICE: OFFLINE'}</span>
          </div>

          {/* Hardware / Bluetooth Transport */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
            isHardwareConnected
              ? 'bg-blue-950/60 text-blue-300 border-blue-800/50'
              : 'bg-amber-950/60 text-amber-300 border-amber-800/50'
          }`}>
            <Radio className="w-3.5 h-3.5" />
            <span className="uppercase">
              {telemetry.transport?.type || 'ROVER'}: {isHardwareConnected ? (telemetry.transport?.port || 'LINKED') : 'DISCONNECTED'}
            </span>
          </div>

          {/* Safety / Arm State */}
          {telemetry.estop_active ? (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-rose-600 text-white font-bold animate-bounce shadow-lg shadow-rose-600/40">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>E-STOP ACTIVE</span>
            </div>
          ) : telemetry.is_armed ? (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-600/20 text-emerald-300 border border-emerald-500/50">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>ROVER ARMED</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-amber-600/20 text-amber-300 border border-amber-500/50">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>DISARMED (SAFE)</span>
            </div>
          )}

          {/* Mode Pill */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
            telemetry.mode === 'GESTURE'
              ? 'bg-purple-950/60 text-purple-300 border-purple-800/50'
              : 'bg-amber-950/60 text-amber-300 border-amber-800/50'
          }`}>
            <Activity className="w-3.5 h-3.5" />
            <span>MODE: {telemetry.mode}</span>
          </div>
        </div>

        {/* Right Section: Clock & Settings */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:block text-xs font-mono text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800">
            {timeStr || '00:00:00'}
          </div>

          <button
            onClick={onOpenSettings}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all shadow-sm active:scale-95 cursor-pointer"
            title="Open Configuration Settings"
          >
            <Settings className="w-4 h-4 text-cyan-400" />
            <span className="hidden md:inline">Settings</span>
          </button>
        </div>
      </div>
    </header>
  );
}
