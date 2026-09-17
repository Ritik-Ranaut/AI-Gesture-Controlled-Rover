/**
 * WebSocket client manager for live telemetry streaming with auto-reconnection.
 */

export class RoverWebSocketClient {
  constructor(url) {
    const configuredPort = (typeof window !== 'undefined' && window.__ROVER_BACKEND_PORT__) || 8001;
    const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const developmentUrl = `${protocol}//${host}:${configuredPort}/ws/telemetry`;
    this.usesDashboardProxy = !url && typeof window !== 'undefined' && window.location.port === '5173';
    this.url = url || (this.usesDashboardProxy
      ? `${protocol}//${window.location.host}/ws/telemetry`
      : developmentUrl);
    this.socket = null;
    this.reconnectTimer = null;
    this.reconnectInterval = 2000;
    this.listeners = new Set();
    this.stateListeners = new Set();
    this.isConnected = false;
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this._notifyState('connecting');

    const openSocket = () => {
      try {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
          this.isConnected = true;
          this._notifyState('connected');
          console.log('[WS] Connected to rover telemetry stream.');
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.listeners.forEach(callback => callback(data));
          } catch (err) {
            console.error('[WS] Failed to parse telemetry:', err);
          }
        };

        this.socket.onerror = (err) => {
          console.warn('[WS] Socket error:', err);
        };

        this.socket.onclose = () => {
          this.isConnected = false;
          this._notifyState('disconnected');
          this.socket = null;
          this._scheduleReconnect();
        };
      } catch (err) {
        this.isConnected = false;
        this._notifyState('disconnected');
        this._scheduleReconnect();
      }
    };

    if (this.usesDashboardProxy) {
      fetch('/api/health', { cache: 'no-store' })
        .then(response => {
          if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
          return response.json();
        })
        .then(data => {
          if (!data.ready) throw new Error('Backend is still initializing');
          openSocket();
        })
        .catch(() => this._scheduleReconnect());
      return;
    }

    openSocket();
  }

  _scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectInterval);
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  onStateChange(callback) {
    this.stateListeners.add(callback);
    callback(this.isConnected ? 'connected' : 'disconnected');
    return () => this.stateListeners.delete(callback);
  }

  _notifyState(state) {
    this.stateListeners.forEach(cb => cb(state));
  }

  send(payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  sendArm() {
    return this.send({ action: 'arm' });
  }

  sendDisarm() {
    return this.send({ action: 'disarm' });
  }

  sendEstop() {
    return this.send({ action: 'estop' });
  }

  sendMode(mode) {
    return this.send({ action: 'set_mode', mode });
  }

  sendManualCommand(command) {
    return this.send({ action: 'manual_cmd', command });
  }

  sendSettings(settings) {
    return this.send({ action: 'update_settings', settings });
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

// Global client singleton
export const wsClient = new RoverWebSocketClient();
