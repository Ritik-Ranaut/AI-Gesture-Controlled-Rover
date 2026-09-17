import React, { useState, useEffect } from 'react';
import { X, Save, RefreshCw, Cpu, Camera, Radio, Shield, Video } from 'lucide-react';
import { setEsp32Ip } from '../services/esp32';

export default function SettingsModal({ isOpen, onClose, onSaveSettings, initialSettings }) {
  const [formData, setFormData] = useState({
    transport_type: 'wifi',
    com_port: 'COM7',
    baud_rate: 9600,
    confidence_threshold: 0.80,
    confirmation_frames: 3,
    command_timeout_ms: 500,
    command_refresh_interval_ms: 120,
    camera_index: 0,
    esp32_cam_url: ''
  });

  const [availablePorts, setAvailablePorts] = useState([]);
  const [isScanningPorts, setIsScanningPorts] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (initialSettings) {
      setFormData(prev => ({
        ...prev,
        ...initialSettings
      }));
    }
  }, [initialSettings]);

  useEffect(() => {
    if (isOpen) {
      scanPorts();
    }
  }, [isOpen]);

  const scanPorts = async () => {
    setIsScanningPorts(true);
    try {
      const res = await fetch('/api/ports');
      if (res.ok) {
        const data = await res.json();
        setAvailablePorts(data.ports || []);
      }
    } catch (err) {
      console.warn('Failed to scan COM ports:', err);
    } finally {
      setIsScanningPorts(false);
    }
  };

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setSaveError('');
    setIsSaving(true);
    try {
      if (formData.esp32_ip) {
        setEsp32Ip(formData.esp32_ip);
      }
      Promise.resolve(onSaveSettings(formData))
        .then(() => onClose())
        .catch((error) => setSaveError(`Settings were not applied: ${error.message}`))
        .finally(() => setIsSaving(false));
    } catch (error) {
      setSaveError(`Settings were not applied: ${error.message}`);
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-slate-950 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white font-mono">
              SYSTEM CONFIGURATION & TUNING
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto">
          {/* Section 1: Wireless & Hardware Transport */}
          <div className="space-y-3">
            <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-2">
              <Radio className="w-4 h-4" />
              <span>ROVER COMMUNICATION LAYER</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">Transport Type</label>
                <select
                  name="transport_type"
                  value={formData.transport_type}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                >
                  <option value="wifi">ESP32 Wi-Fi (Normal ESP32 Bridge)</option>
                  <option value="bluetooth">Bluetooth HC-05 (Virtual COM)</option>
                  <option value="serial">USB Serial (Direct Nano Cable)</option>
                  <option value="mock">Mock / Simulation (No Hardware)</option>
                </select>
              </div>

              {formData.transport_type === 'wifi' ? (
                <div>
                    <label className="block text-xs text-slate-400 mb-1 font-mono">Dashboard ESP32 Target IP</label>
                  <input
                    type="text"
                    name="esp32_ip"
                    value={formData.esp32_ip || '192.168.4.1'}
                    onChange={handleChange}
                    placeholder="192.168.4.1"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    This changes the dashboard target. To change the ESP32 address, edit WIFI_MODE_AP, USE_STATIC_IP, and local_IP in the ESP32 sketch, then reflash it.
                  </p>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-slate-400 font-mono">COM Port</label>
                    <button
                      type="button"
                      onClick={scanPorts}
                      disabled={isScanningPorts}
                      className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 cursor-pointer"
                    >
                      <RefreshCw className={`w-3 h-3 ${isScanningPorts ? 'animate-spin' : ''}`} />
                      <span>Scan</span>
                    </button>
                  </div>
                  <input
                    type="text"
                    name="com_port"
                    value={formData.com_port}
                    onChange={handleChange}
                    list="port-options"
                    placeholder="e.g. COM7"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                  />
                  <datalist id="port-options">
                    {availablePorts.map(p => (
                      <option key={p.device} value={p.device}>
                        {p.device} - {p.description}
                      </option>
                    ))}
                    <option value="COM3" />
                    <option value="COM7" />
                    <option value="COM8" />
                  </datalist>
                </div>
              )}

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">Baud Rate</label>
                <select
                  name="baud_rate"
                  value={formData.baud_rate}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                >
                  <option value={9600}>9600 (HC-05 Default)</option>
                  <option value={115200}>115200 (USB High Speed)</option>
                  <option value={38400}>38400</option>
                  <option value={57600}>57600</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">
                  Watchdog Timeout: <strong className="text-purple-400">{formData.command_timeout_ms} ms</strong>
                </label>
                <input
                  type="range"
                  name="command_timeout_ms"
                  min="200"
                  max="1500"
                  step="50"
                  value={formData.command_timeout_ms}
                  onChange={handleChange}
                  className="w-full accent-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">
                  Command Refresh: <strong className="text-cyan-400">{formData.command_refresh_interval_ms} ms</strong>
                </label>
                <input
                  type="range"
                  name="command_refresh_interval_ms"
                  min="50"
                  max="400"
                  step="10"
                  value={formData.command_refresh_interval_ms}
                  onChange={handleChange}
                  className="w-full accent-cyan-500"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Gesture Classifier Tuning */}
          <div className="space-y-3 pt-3 border-t border-slate-800">
            <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-2">
              <Shield className="w-4 h-4" />
              <span>GESTURE RECOGNITION & SAFETY GATES</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-slate-400 font-mono">Confidence Threshold</label>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    {Math.round(formData.confidence_threshold * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  name="confidence_threshold"
                  min="0.50"
                  max="0.95"
                  step="0.05"
                  value={formData.confidence_threshold}
                  onChange={handleChange}
                  className="w-full accent-emerald-500"
                />
                <span className="text-[11px] text-slate-500">
                  Ignores gestures below this threshold to avoid false positives.
                </span>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-slate-400 font-mono">Confirmation Window</label>
                  <span className="text-xs font-mono font-bold text-cyan-400">
                    {formData.confirmation_frames} frames
                  </span>
                </div>
                <input
                  type="range"
                  name="confirmation_frames"
                  min="1"
                  max="8"
                  step="1"
                  value={formData.confirmation_frames}
                  onChange={handleChange}
                  className="w-full accent-cyan-500"
                />
                <span className="text-[11px] text-slate-500">
                  Consecutive identical frames before command is accepted.
                </span>
              </div>
            </div>
          </div>

          {/* Section 3: Camera & ESP32-CAM Video URLs */}
          <div className="space-y-3 pt-3 border-t border-slate-800">
            <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-2">
              <Camera className="w-4 h-4" />
              <span>CAMERAS & STREAMING</span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">Laptop Webcam Index</label>
                <select
                  name="camera_index"
                  value={formData.camera_index}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                >
                  <option value={0}>Camera 0 (Default Integrated Webcam)</option>
                  <option value={1}>Camera 1 (External USB Camera)</option>
                  <option value={2}>Camera 2</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">ESP32-CAM MJPEG Stream URL</label>
                <input
                  type="text"
                  name="esp32_cam_url"
                  value={formData.esp32_cam_url}
                  onChange={handleChange}
                  placeholder="http://192.168.1.100:81/stream"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Enter the IP address printed on your ESP32-CAM Serial Monitor (e.g. http://192.168.x.x/stream).
                </p>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end space-x-3">
            {saveError && <p className="mr-auto text-xs text-rose-300 font-mono">{saveError}</p>}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-mono font-bold text-xs flex items-center space-x-1.5 transition-all shadow-lg shadow-cyan-600/30 cursor-pointer disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{isSaving ? 'Saving...' : 'Apply Settings'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
