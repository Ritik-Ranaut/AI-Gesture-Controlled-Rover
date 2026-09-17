// src/services/esp32.js

const STORAGE_KEY = 'esp32_ip';
const CONFIDENCE_THRESHOLD_KEY = 'esp32_gesture_confidence_threshold';

const DEFAULT_IP =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    import.meta.env.VITE_ESP32_IP)
    ? import.meta.env.VITE_ESP32_IP
    : '192.168.4.1';

const DEFAULT_PORT =
  Number(
    (typeof import.meta !== 'undefined' &&
      import.meta.env &&
      import.meta.env.VITE_ESP32_PORT)
      ? import.meta.env.VITE_ESP32_PORT
      : 80
  );

const REQUEST_TIMEOUT_MS = 4000;

const DEFAULT_GESTURE_CONFIDENCE_THRESHOLD =
  Number(
    (typeof import.meta !== 'undefined' &&
      import.meta.env &&
      import.meta.env.VITE_ESP32_GESTURE_CONFIDENCE_THRESHOLD)
      ? import.meta.env.VITE_ESP32_GESTURE_CONFIDENCE_THRESHOLD
      : 0.7
  );

const DEFAULT_GESTURE_COOLDOWN_MS =
  Number(
    (typeof import.meta !== 'undefined' &&
      import.meta.env &&
      import.meta.env.VITE_ESP32_GESTURE_COOLDOWN_MS)
      ? import.meta.env.VITE_ESP32_GESTURE_COOLDOWN_MS
      : 400
  );

// --------------------------------------------------
// Safe Local Storage
// --------------------------------------------------

function safeLocalStorage() {
  try {
    if (
      typeof window !== 'undefined' &&
      window.localStorage
    ) {
      return window.localStorage;
    }
  } catch (error) {
    console.warn(
      '[ESP32] Local storage unavailable:',
      error
    );
  }

  return null;
}

// --------------------------------------------------
// ESP32 IP
// --------------------------------------------------

export function getEsp32Ip() {
  const storage = safeLocalStorage();

  return storage
    ? storage.getItem(STORAGE_KEY) || DEFAULT_IP
    : DEFAULT_IP;
}

export function setEsp32Ip(ip) {
  const trimmedIp = String(ip || '').trim();

  if (!trimmedIp) {
    throw new Error('ESP32 IP address is required.');
  }

  const storage = safeLocalStorage();

  if (storage) {
    storage.setItem(STORAGE_KEY, trimmedIp);
  }

  return trimmedIp;
}

// --------------------------------------------------
// ESP32 Base URL
// --------------------------------------------------

export function getEsp32BaseUrl(
  ip = getEsp32Ip()
) {
  return `http://${ip}:${DEFAULT_PORT}`;
}

// --------------------------------------------------
// Proxy URL
// --------------------------------------------------

function getEsp32ProxyUrl(
  path,
  query = {}
) {
  const params = new URLSearchParams({
    ip: getEsp32Ip(),
    port: String(DEFAULT_PORT),
    ...query
  });

  return `/api/esp32/proxy${path}?${params.toString()}`;
}

// --------------------------------------------------
// Gesture Normalization
// --------------------------------------------------

export function normalizeGesture(
  rawGesture
) {
  const value = String(
    rawGesture ?? ''
  )
    .trim()
    .toUpperCase();

  if (!value) {
    return 'NONE';
  }

  const normalizedMap = {

    // -------------------------
    // Forward
    // -------------------------

    UP: 'FORWARD',
    UPWARD: 'FORWARD',
    FORWARD: 'FORWARD',
    FRONT: 'FORWARD',
    F: 'FORWARD',

    // -------------------------
    // Backward
    // -------------------------

    DOWN: 'BACKWARD',
    DOWNWARD: 'BACKWARD',
    BACKWARD: 'BACKWARD',
    BACK: 'BACKWARD',
    REVERSE: 'BACKWARD',
    B: 'BACKWARD',

    // -------------------------
    // Left
    // -------------------------

    LEFT: 'LEFT',
    L: 'LEFT',

    // -------------------------
    // Right
    // -------------------------

    RIGHT: 'RIGHT',
    R: 'RIGHT',

    CENTER: 'CENTER',

    // -------------------------
    // Stop
    // -------------------------

    STOP: 'STOP',
    S: 'STOP',
    HALT: 'STOP',
    PAUSE: 'STOP',

    // Open palm variations
    OPEN_PALM: 'STOP',
    OPENPALM: 'STOP',
    PALM: 'STOP',

    // -------------------------
    // Nothing detected
    // -------------------------

    NONE: 'NONE',
    NO_HAND: 'NONE',
    NO_GESTURE: 'NONE'
  };

  return normalizedMap[value] || value;
}

// --------------------------------------------------
// Supported Rover Commands
// --------------------------------------------------

export const SUPPORTED_ROVER_COMMANDS = [
  'FORWARD',
  'BACKWARD',
  'LEFT',
  'RIGHT',
  'CENTER',
  'STOP'
];

// --------------------------------------------------
// Gesture Validation
// --------------------------------------------------

export function isSupportedRoverGesture(
  gesture
) {
  const normalized =
    normalizeGesture(gesture);

  return SUPPORTED_ROVER_COMMANDS.includes(
    normalized
  );
}

// --------------------------------------------------
// Confidence Threshold
// --------------------------------------------------

export function getGestureConfidenceThreshold() {
  const storage = safeLocalStorage();

  if (storage) {
    const saved = Number(
      storage.getItem(
        CONFIDENCE_THRESHOLD_KEY
      )
    );

    if (
      Number.isFinite(saved) &&
      saved > 0 &&
      saved <= 1
    ) {
      return saved;
    }
  }

  return DEFAULT_GESTURE_CONFIDENCE_THRESHOLD;
}

export function setGestureConfidenceThreshold(
  value
) {
  const threshold = Number(value);

  if (
    !Number.isFinite(threshold) ||
    threshold <= 0 ||
    threshold > 1
  ) {
    throw new Error(
      'Gesture confidence threshold must be between 0 and 1.'
    );
  }

  const storage = safeLocalStorage();

  if (storage) {
    storage.setItem(
      CONFIDENCE_THRESHOLD_KEY,
      String(threshold)
    );
  }

  return threshold;
}

// --------------------------------------------------
// Gesture Cooldown
// --------------------------------------------------

export function getGestureCooldownMs() {
  return DEFAULT_GESTURE_COOLDOWN_MS;
}

// --------------------------------------------------
// Request Helper
// --------------------------------------------------

async function request(
  path,
  options = {}
) {
  const controller =
    new AbortController();

  const timerSource =
    typeof window !== 'undefined'
      ? window
      : globalThis;

  const timeoutHandle =
    timerSource.setTimeout(
      () => controller.abort(),
      REQUEST_TIMEOUT_MS
    );

  try {
    const proxyUrl =
      getEsp32ProxyUrl(
        path,
        options.proxyQuery || {}
      );

    console.log(
      '[ESP32] Request:',
      proxyUrl
    );

    const response = await fetch(
      proxyUrl,
      {
        ...options,
        signal: controller.signal,

        headers: {
          Accept: 'application/json',
          ...(options.headers || {})
        }
      }
    );

    const bodyText =
      await response.text();

    let data = {};

    if (bodyText) {
      try {
        data = JSON.parse(
          bodyText
        );
      } catch {
        data = {
          raw: bodyText
        };
      }
    }

    if (!response.ok) {
      throw new Error(
        data.message ||
        data.error ||
        `ESP32 returned HTTP ${response.status}.`
      );
    }

    return data;

  } catch (error) {

    if (
      error?.name === 'AbortError'
    ) {
      throw new Error(
        'ESP32 connection timeout.'
      );
    }

    if (
      error instanceof TypeError &&
      /fetch|network|failed/i.test(
        error.message || ''
      )
    ) {
      throw new Error(
        `ESP32 request blocked or unreachable. Verify the ESP32 IP: ${getEsp32Ip()}`
      );
    }

    throw error;

  } finally {

    timerSource.clearTimeout(
      timeoutHandle
    );
  }
}

// --------------------------------------------------
// ESP32 Status
// --------------------------------------------------

export function getEsp32Status() {
  return request('/status');
}

// --------------------------------------------------
// ESP32 Wi-Fi Information
// --------------------------------------------------

export function getEsp32Wifi() {
  return request('/wifi');
}

export function gestureToServoAngle(gesture) {
  const normalized = normalizeGesture(gesture);
  const angleMap = {
    LEFT: 0,
    CENTER: 90,
    STOP: 90,
    RIGHT: 180
  };
  return angleMap[normalized] ?? 90;
}

export function moveEsp32Servo(angle) {
  const normalizedAngle = Number(angle);
  if (!Number.isInteger(normalizedAngle) || normalizedAngle < 0 || normalizedAngle > 180) {
    return Promise.reject(new Error('Servo angle must be an integer from 0 to 180.'));
  }
  return request('/servo', { proxyQuery: { angle: String(normalizedAngle) } });
}

// --------------------------------------------------
// Manual Rover Command
// --------------------------------------------------

export function sendEsp32Command(
  command
) {
  const normalizedCommand =
    normalizeGesture(command);

  if (
    !SUPPORTED_ROVER_COMMANDS.includes(
      normalizedCommand
    )
  ) {
    return Promise.reject(
      new Error(
        `Unsupported rover command: ${command}`
      )
    );
  }

  console.log(
    '[ROVER] Sending command:',
    normalizedCommand
  );

  return request(
    '/command',
    {
      proxyQuery: {
        command: normalizedCommand
      }
    }
  ).then((data) => {

    console.log(
      '[ROVER] ESP32 response:',
      data
    );

    return {
      ...data,
      status:
        data?.status || 'success',
      command:
        normalizedCommand
    };
  });
}

// --------------------------------------------------
// Gesture -> Rover Command
// --------------------------------------------------

export function sendEsp32Gesture(
  gesture,
  options = {}
) {
  const normalizedGesture =
    normalizeGesture(gesture);

  console.log(
    '[GESTURE] Raw:',
    gesture
  );

  console.log(
    '[GESTURE] Normalized:',
    normalizedGesture
  );

  // No hand / no gesture
  if (
    !normalizedGesture ||
    normalizedGesture === 'NONE'
  ) {
    return Promise.resolve({
      status: 'skipped',
      gesture: 'NONE',
      reason: 'No hand detected.'
    });
  }

  // Unsupported gesture
  if (
    !SUPPORTED_ROVER_COMMANDS.includes(
      normalizedGesture
    )
  ) {
    console.warn(
      '[GESTURE] Unsupported gesture:',
      normalizedGesture
    );

    return Promise.resolve({
      status: 'skipped',
      gesture: normalizedGesture,
      reason:
        'Unsupported rover gesture.'
    });
  }

  // -------------------------
  // Confidence
  // -------------------------

  const confidence =
    Number(
      options.confidence ?? 1
    );

  const threshold =
    Number(
      options.threshold ??
      getGestureConfidenceThreshold()
    );

  if (
    confidence < threshold
  ) {
    console.log(
      '[GESTURE] Rejected because confidence is low:',
      confidence
    );

    return Promise.resolve({
      status: 'skipped',
      gesture: normalizedGesture,
      reason: 'Low confidence',
      confidence,
      threshold
    });
  }

  // -------------------------
  // Send command
  // -------------------------

  return sendEsp32Command(
    normalizedGesture
  ).then((data) => {

    return {
      ...data,

      status:
        data?.status || 'success',

      gesture:
        normalizedGesture,

      command:
        normalizedGesture,

      confidence,

      threshold
    };
  });
}

// --------------------------------------------------
// Alias
// --------------------------------------------------

export function sendGestureToServo(
  gesture,
  options = {}
) {
  // Kept for compatibility with
  // existing components.
  //
  // IMPORTANT:
  // This now controls the rover,
  // not a servo.

  return sendEsp32Gesture(
    gesture,
    options
  );
}

// --------------------------------------------------
// STOP
// --------------------------------------------------

export function sendStop() {
  console.log(
    '[ROVER] EMERGENCY STOP'
  );

  return sendEsp32Command(
    'STOP'
  );
}

// --------------------------------------------------
// Connection Test
// --------------------------------------------------

export async function testEsp32Connection() {
  try {

    const data =
      await getEsp32Status();

    return {
      ok: true,
      data,

      url:
        getEsp32BaseUrl()
    };

  } catch (error) {

    return {
      ok: false,

      error:
        error?.message ||
        'ESP32 disconnected',

      url:
        getEsp32BaseUrl()
    };
  }
}

// --------------------------------------------------
// Convenience Commands
// --------------------------------------------------

export function moveForward() {
  return sendEsp32Command(
    'FORWARD'
  );
}

export function moveBackward() {
  return sendEsp32Command(
    'BACKWARD'
  );
}

export function moveLeft() {
  return sendEsp32Command(
    'LEFT'
  );
}

export function moveRight() {
  return sendEsp32Command(
    'RIGHT'
  );
}

export function stopRover() {
  return sendEsp32Command(
    'STOP'
  );
}