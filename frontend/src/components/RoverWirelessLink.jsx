import React, { useEffect, useState } from 'react';
import { CheckCircle2, RefreshCw, Wifi, XCircle, ArrowLeft, ArrowRight, Hand, Gauge } from 'lucide-react';
import {
  getEsp32Ip,
  getEsp32Status,
  gestureToServoAngle,
  moveEsp32Servo,
  normalizeGesture,
  sendEsp32Gesture,
  setEsp32Ip
} from '../services/esp32';

const PRESET_ANGLES = [0, 45, 90, 135, 180];
const GESTURE_TESTS = [
  { label: 'LEFT', value: 'LEFT' },
  { label: 'CENTER', value: 'CENTER' },
  { label: 'RIGHT', value: 'RIGHT' }
];

export default function RoverWirelessLink({ telemetry = {} }) {
  const [esp32Ip, setEsp32IpValue] = useState(getEsp32Ip());
  const [status, setStatus] = useState(null);
  const [angle, setAngle] = useState(90);
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState('Enter the ESP32 address and test the direct Wi-Fi link.');
  const [connectionState, setConnectionState] = useState('Disconnected');
  const [lastGesture, setLastGesture] = useState('NONE');
  const [lastCommand, setLastCommand] = useState('NONE');
  const [lastServoAngle, setLastServoAngle] = useState(90);

  useEffect(() => {
    setEsp32IpValue(getEsp32Ip());
  }, []);

  const updateConnectionState = (state) => {
    setConnectionState(state);
  };

  const handleSaveIp = () => {
    try {
      const savedIp = setEsp32Ip(esp32Ip);
      setEsp32IpValue(savedIp);
      setStatus(null);
      setMessage(`ESP32 target saved: ${savedIp}`);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setConnectionState('Testing');
    setStatus(null);
    setMessage('Testing the ESP32 directly...');
    try {
      const savedIp = setEsp32Ip(esp32Ip);
      setEsp32IpValue(savedIp);
      const data = await getEsp32Status();
      setStatus(data);
      setConnectionState('Connected');
      setMessage('ESP32 connected. The response was verified from the ESP32.');
    } catch (error) {
      setConnectionState('Disconnected');
      setMessage(`ESP32 connection failed: ${error.message}`);
    } finally {
      setIsTesting(false);
    }
  };

  const handleUseApAddress = () => {
    const apAddress = setEsp32Ip('192.168.4.1');
    setEsp32IpValue(apAddress);
    setStatus(null);
    setConnectionState('Disconnected');
    setMessage('Direct AP target selected: 192.168.4.1');
  };

  const handleMove = async (requestedAngle) => {
    const selectedAngle = Number(requestedAngle);
    setAngle(selectedAngle);
    setLastServoAngle(selectedAngle);
    setLastCommand(`${selectedAngle}°`);
    setMessage(`Sending ${selectedAngle} degrees to GPIO 18...`);
    try {
      const data = await moveEsp32Servo(selectedAngle);
      setStatus((previous) => (previous ? { ...previous, servoAngle: data.angle ?? selectedAngle } : previous));
      setConnectionState('Connected');
      setMessage(`Servo moved to ${data.angle ?? selectedAngle} degrees.`);
    } catch (error) {
      setConnectionState('Disconnected');
      setMessage(`ESP32 disconnected: ${error.message}`);
    }
  };

  const handleGestureTest = async (gesture) => {
    const normalized = normalizeGesture(gesture);
    const targetAngle = gestureToServoAngle(normalized);
    setLastGesture(normalized);
    setLastCommand(normalized);
    setLastServoAngle(targetAngle);
    setAngle(targetAngle);
    setMessage(`Testing ESP32 command: ${normalized}`);
    try {
      const response = await sendEsp32Gesture(normalized, { confidence: 1, threshold: 0 });
      setStatus((previous) => (previous ? { ...previous, servoAngle: response.angle ?? targetAngle } : previous));
      setConnectionState('Connected');
      setMessage(`ESP32 response: ${response.status || 'success'} | ${normalized} -> ${targetAngle}°`);
    } catch (error) {
      setConnectionState('Disconnected');
      setMessage(`ESP32 disconnected: ${error.message}`);
    }
  };

  return (
    <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-950 flex items-center justify-center border border-emerald-700/60 text-emerald-400">
            <Wifi className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide font-mono">ESP32 WI-FI LINK</h3>
            <p className="text-xs text-slate-400">Dashboard target only; the ESP32 address is configured in its sketch</p>
          </div>
        </div>
        {connectionState === 'Connected' ? (
          <span className="inline-flex items-center space-x-1.5 text-xs font-mono font-bold text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>ESP32 CONNECTED</span>
          </span>
        ) : connectionState === 'Testing' ? (
          <span className="inline-flex items-center space-x-1.5 text-xs font-mono text-amber-300">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>TESTING</span>
          </span>
        ) : (
          <span className="inline-flex items-center space-x-1.5 text-xs font-mono text-slate-500">
            <XCircle className="w-4 h-4" />
            <span>ESP32 DISCONNECTED</span>
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3">
        <label className="text-xs text-slate-400 font-mono">
          Dashboard ESP32 target IP
          <input
            value={esp32Ip}
            onChange={(event) => setEsp32IpValue(event.target.value)}
            onBlur={handleSaveIp}
            placeholder="192.168.4.1"
            className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
          />
        </label>
        <div className="flex items-end gap-2">
          <button onClick={handleUseApAddress} className="px-3 py-2 rounded-lg bg-cyan-900 hover:bg-cyan-800 text-cyan-200 text-xs font-mono cursor-pointer">USE AP IP</button>
          <button onClick={handleSaveIp} className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono cursor-pointer">SAVE IP</button>
          <button onClick={handleTestConnection} disabled={isTesting} className="px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-mono font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50">
            <RefreshCw className={`w-3 h-3 ${isTesting ? 'animate-spin' : ''}`} />
            TEST CONNECTION
          </button>
        </div>
      </div>

      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-xs font-mono font-bold text-cyan-300">ESP32 STATUS</h4>
          <span className="text-xs font-mono text-slate-400">{connectionState}</span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs font-mono">
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-slate-500 uppercase tracking-wider">ESP32 IP</div>
            <div className="mt-1 text-slate-100">{esp32Ip}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-slate-500 uppercase tracking-wider">Connection</div>
            <div className="mt-1 text-slate-100">{connectionState}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-slate-500 uppercase tracking-wider">Last Gesture</div>
            <div className="mt-1 text-slate-100">{lastGesture}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-slate-500 uppercase tracking-wider">Servo Angle</div>
            <div className="mt-1 text-slate-100">{lastServoAngle}°</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 col-span-2">
            <div className="text-slate-500 uppercase tracking-wider">Last Command</div>
            <div className="mt-1 text-slate-100">{lastCommand}</div>
          </div>
        </div>
      </div>

      {status && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono">
          <div><span className="text-slate-500">ESP32</span><br />{status.ip}</div>
          <div><span className="text-slate-500">Mode</span><br />{status.wifiMode}</div>
          <div><span className="text-slate-500">IP source</span><br />{status.ipSource}</div>
          <div><span className="text-slate-500">Gateway</span><br />{status.gateway}</div>
          <div><span className="text-slate-500">RSSI</span><br />{status.rssi} dBm</div>
          <div><span className="text-slate-500">Servo</span><br />GPIO {status.servoPin}</div>
        </div>
      )}

      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center justify-between gap-2 mb-3">
          <h4 className="text-xs font-mono font-bold text-cyan-300">SERVO TEST, GPIO 18</h4>
          <span className="text-xs font-mono text-slate-400">{angle}&deg;</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_ANGLES.map((preset) => (
            <button key={preset} onClick={() => handleMove(preset)} className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-cyan-700 text-slate-200 text-xs font-mono cursor-pointer">
              {preset}&deg;
            </button>
          ))}
          <input type="number" min="0" max="180" value={angle} onChange={(event) => setAngle(event.target.value)} className="w-20 bg-slate-900 border border-slate-700 rounded-lg px-2 text-sm font-mono" />
          <button onClick={() => handleMove(angle)} className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-mono font-bold cursor-pointer">MOVE</button>
        </div>
      </div>

      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center justify-between gap-2 mb-3">
          <h4 className="text-xs font-mono font-bold text-cyan-300">HAND GESTURE HARDWARE TEST</h4>
          <span className="text-xs font-mono text-slate-500">ESP32 command</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {GESTURE_TESTS.map((test) => (
            <button
              key={test.value}
              onClick={() => handleGestureTest(test.value)}
              className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-emerald-700 text-slate-200 text-xs font-mono cursor-pointer flex items-center gap-2"
            >
              {test.value === 'LEFT' && <ArrowLeft className="w-3 h-3" />}
              {test.value === 'CENTER' && <Gauge className="w-3 h-3" />}
              {test.value === 'RIGHT' && <ArrowRight className="w-3 h-3" />}
              {test.label}
            </button>
          ))}
        </div>
      </div>

      <p className={`text-xs font-mono ${connectionState === 'Connected' ? 'text-emerald-300' : connectionState === 'Testing' ? 'text-amber-300' : 'text-rose-300'}`}>{message}</p>
    </section>
  );
}
