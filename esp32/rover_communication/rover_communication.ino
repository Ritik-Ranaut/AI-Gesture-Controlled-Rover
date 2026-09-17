/*
 * ESP32 Rover Controller
 *
 * The ESP32 serves HTTP over Wi-Fi, forwards rover commands to the Arduino
 * Nano over UART2, and retains a GPIO 18 servo endpoint for bench testing.
 */

#include <WiFi.h>
#include <WebServer.h>

// UART2 bridge to the Arduino Nano: ESP32 TX2/GPIO17 -> Nano RX,
// Nano TX -> ESP32 RX2/GPIO16 through a 5V-to-3.3V level shifter.
HardwareSerial roverSerial(2);

// -------------------------- User configuration ---------------------------
#define WIFI_MODE_AP true
#define USE_STATIC_IP false

const char* WIFI_SSID = "ZERO_BOOK_13 7356";
const char* WIFI_PASSWORD = "69696969";

const char* AP_SSID = "ESP32-Rover";
const char* AP_PASSWORD = "rover12345";

IPAddress local_IP(192, 168, 1, 105);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);
IPAddress secondaryDNS(8, 8, 4, 4);

const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_GATEWAY(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);

const uint8_t SERVO_PIN = 18;
const uint8_t SERVO_CHANNEL = 0;
const uint16_t SERVO_MIN_US = 500;
const uint16_t SERVO_MAX_US = 2400;
const uint8_t START_ANGLE = 90;
const uint32_t ROVER_BAUD_RATE = 9600;
// --------------------------------------------------------------------------

WebServer server(80);
uint8_t servoAngle = START_ANGLE;
unsigned long bootTime = 0;
String wifiMode = WIFI_MODE_AP ? "AP" : "STA";
char lastCommand = 'S';
String lastArduinoResponse = "";

char commandToProtocol(String command) {
  command.trim();
  command.toUpperCase();

  if (command == "FORWARD" || command == "F") return 'F';
  if (command == "BACKWARD" || command == "B") return 'B';
  if (command == "LEFT" || command == "L") return 'L';
  if (command == "RIGHT" || command == "R") return 'R';
  if (command == "CENTER" || command == "STOP" || command == "S") return 'S';
  if (command == "CRAB_WALK" || command == "C") return 'C';
  if (command == "TURN_360" || command == "T") return 'T';
  if (command == "ARM" || command == "A") return 'A';
  if (command == "DISARM" || command == "D") return 'D';
  if (command == "ESTOP" || command == "E") return 'E';
  if (command == "PING" || command == "P") return 'P';
  return '\0';
}

bool forwardCommand(String command) {
  const char protocolCommand = commandToProtocol(command);
  if (protocolCommand == '\0') return false;

  roverSerial.println(protocolCommand);
  lastCommand = protocolCommand;
  return true;
}

int mapGestureToAngle(const String& commandKey) {
  String command = commandKey;
  command.trim();
  command.toUpperCase();

  if (command == "LEFT" || command == "L") return 0;
  if (command == "CENTER" || command == "C" || command == "STOP" || command == "S") return 90;
  if (command == "RIGHT" || command == "R") return 180;
  if (command == "TURN_360" || command == "CRAB_WALK" || command == "FORWARD" || command == "BACKWARD") return 90;
  return 90;
}

void addCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

void sendJsonResponse(int code, const String& payload) {
  addCorsHeaders();
  server.send(code, "application/json", payload);
}

void handleOptions() {
  addCorsHeaders();
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  server.send(204);
}

void writeServoAngle(uint8_t angle) {
  servoAngle = constrain(angle, 0, 180);
  const uint32_t pulseUs = map(servoAngle, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
  const uint32_t duty = (pulseUs * 65535UL) / 20000UL;
  ledcWrite(SERVO_CHANNEL, duty);
}

String currentIp() {
  return WIFI_MODE_AP ? WiFi.softAPIP().toString() : WiFi.localIP().toString();
}

String currentGateway() {
  return WIFI_MODE_AP ? AP_GATEWAY.toString() : WiFi.gatewayIP().toString();
}

String currentSubnet() {
  return WIFI_MODE_AP ? AP_SUBNET.toString() : WiFi.subnetMask().toString();
}

String ipSource() {
  if (WIFI_MODE_AP) return "AP_FIXED";
  return USE_STATIC_IP ? "STATIC" : "DHCP";
}

void handleStatus() {
  String json = "{";
  json += "\"connected\":true,";
  json += "\"device\":\"ESP32-Rover-Servo\",";
  json += "\"wifiMode\":\"" + wifiMode + "\",";
  json += "\"ipSource\":\"" + ipSource() + "\",";
  json += "\"ip\":\"" + currentIp() + "\",";
  json += "\"gateway\":\"" + currentGateway() + "\",";
  json += "\"subnet\":\"" + currentSubnet() + "\",";
  json += "\"rssi\":" + String(WIFI_MODE_AP ? 0 : WiFi.RSSI()) + ",";
  json += "\"servoPin\":18,";
  json += "\"servoAngle\":" + String(servoAngle) + ",";
  json += "\"lastCommand\":\"" + String(lastCommand) + "\",";
  json += "\"arduinoResponse\":\"" + lastArduinoResponse + "\",";
  json += "\"arduinoConnected\":" + String(lastArduinoResponse.length() > 0 ? "true" : "false") + ",";
  json += "\"uptime\":" + String((millis() - bootTime) / 1000);
  json += "}";
  sendJsonResponse(200, json);
}

void handleWifi() {
  String json = "{";
  json += "\"mode\":\"" + wifiMode + "\",";
  json += "\"ipSource\":\"" + ipSource() + "\",";
  json += "\"ssid\":\"" + String(WIFI_MODE_AP ? AP_SSID : WIFI_SSID) + "\",";
  json += "\"ip\":\"" + currentIp() + "\",";
  json += "\"gateway\":\"" + currentGateway() + "\",";
  json += "\"subnet\":\"" + currentSubnet() + "\",";
  json += "\"rssi\":" + String(WIFI_MODE_AP ? 0 : WiFi.RSSI());
  json += "}";
  sendJsonResponse(200, json);
}

void handleServo() {
  if (!server.hasArg("angle")) {
    sendJsonResponse(400, "{\"status\":\"error\",\"message\":\"angle is required (0-180)\"}");
    return;
  }

  const int requestedAngle = server.arg("angle").toInt();
  if (requestedAngle < 0 || requestedAngle > 180) {
    sendJsonResponse(400, "{\"status\":\"error\",\"message\":\"angle must be between 0 and 180\"}");
    return;
  }

  writeServoAngle(static_cast<uint8_t>(requestedAngle));
  String json = "{\"status\":\"ok\",\"angle\":" + String(servoAngle) + ",\"pin\":18}";
  sendJsonResponse(200, json);
}

// Kept for compatibility with the existing rover dashboard protocol.
void handleCommand() {
  String commandValue = "STOP";
  if (server.hasArg("cmd")) {
    commandValue = server.arg("cmd");
  } else if (server.hasArg("command")) {
    commandValue = server.arg("command");
  } else if (server.hasArg("plain")) {
    String body = server.arg("plain");
    int commandIndex = body.indexOf("\"command\"");
    if (commandIndex >= 0) {
      int separator = body.indexOf(':', commandIndex);
      if (separator >= 0) {
        int quoteStart = body.indexOf('"', separator + 1);
        int quoteEnd = body.indexOf('"', quoteStart + 1);
        if (quoteStart >= 0 && quoteEnd > quoteStart) {
          commandValue = body.substring(quoteStart + 1, quoteEnd);
        }
      }
    }
  }

  String command = commandValue;
  command.trim();
  command.toUpperCase();

  const char protocolCommand = commandToProtocol(command);
  bool supported = protocolCommand != '\0';

  if (!supported) {
    Serial.print("Received command: ");
    Serial.println(commandValue);
    Serial.println("Ignoring unsupported command.");
    sendJsonResponse(200, "{\"status\":\"ignored\",\"command\":\"" + commandValue + "\",\"servoAngle\":" + String(servoAngle) + "}");
    return;
  }

  forwardCommand(command);

  // Keep the servo endpoint useful for bench testing without making it the
  // rover command path.
  int targetAngle = mapGestureToAngle(command);
  if (command == "LEFT" || command == "L" || command == "RIGHT" || command == "R" ||
      command == "CENTER" || command == "STOP" || command == "S") {
    writeServoAngle(static_cast<uint8_t>(targetAngle));
  }

  Serial.print("Received command: ");
  Serial.println(command);
  Serial.print("Servo moved to: ");
  Serial.println(targetAngle);

  sendJsonResponse(200, "{\"status\":\"ok\",\"command\":\"" + command + "\",\"servoAngle\":" + String(targetAngle) + "}");
}

void handleRoot() {
  addCorsHeaders();
  const String ip = currentIp();
  String html = R"rawliteral(<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>ESP32 Rover Controller</title><style>
body{font-family:system-ui,sans-serif;max-width:560px;margin:0 auto;padding:24px;background:#101820;color:#f4f7f9}h1{font-size:1.5rem}section{border:1px solid #30414d;padding:16px;margin:16px 0;border-radius:8px}button,input{font:inherit;padding:10px;margin:4px;border-radius:6px;border:1px solid #50616d}button{background:#1c91a5;color:white;cursor:pointer}input{width:80px;background:#19252d;color:white}.info{line-height:1.7;font-family:monospace}.ok{color:#65d69a}#message{min-height:1.5em}
</style></head><body><h1>ESP32 Rover Controller</h1><section class="info"><div>Wi-Fi mode: <b>)rawliteral";
  html += wifiMode;
  html += R"rawliteral(</b></div><div>IP address: <b>)rawliteral";
  html += ip;
  html += R"rawliteral(</b></div><div>Gateway: <b>)rawliteral";
  html += currentGateway();
  html += R"rawliteral(</b></div><div>RSSI: <b>)rawliteral";
  html += String(WIFI_MODE_AP ? 0 : WiFi.RSSI());
  html += R"rawliteral( dBm</b></div><div class="ok">Connection status: OK</div></section><section><h2>Servo Test, GPIO 18</h2><div>)rawliteral";
  const uint8_t presets[] = {0, 45, 90, 135, 180};
  for (uint8_t preset : presets) {
    html += "<button onclick=\"move(" + String(preset) + ")\">" + String(preset) + "&deg;</button>";
  }
  html += R"rawliteral(</div><label>Custom angle: <input id="angle" type="number" min="0" max="180" value="90"><button onclick="move(document.getElementById('angle').value)">MOVE</button><p id="message"></p></section><script>function move(a){fetch('/servo?angle='+encodeURIComponent(a)).then(r=>r.json()).then(d=>document.getElementById('message').textContent=d.status==='ok'?'Servo moved to '+d.angle+' degrees':d.message).catch(e=>document.getElementById('message').textContent='Request failed: '+e)}</script></body></html>)rawliteral";
  server.send(200, "text/html", html);
}

bool connectStation() {
  WiFi.mode(WIFI_STA);
  if (USE_STATIC_IP && !WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("Static IP configuration failed");
  }

  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  return WiFi.status() == WL_CONNECTED;
}

void setupWifi() {
  if (WIFI_MODE_AP) {
    wifiMode = "AP";
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("AP SSID: ");
    Serial.println(AP_SSID);
    return;
  }

  wifiMode = "STA";
  if (!connectStation()) {
    Serial.println("Wi-Fi connection failed. Check WIFI_SSID and WIFI_PASSWORD.");
    Serial.print("Wi-Fi status code: ");
    Serial.println(WiFi.status());
    return;
  }
}

void setup() {
  bootTime = millis();
  Serial.begin(115200);
  roverSerial.begin(ROVER_BAUD_RATE, SERIAL_8N1, 16, 17);
  delay(100);
  Serial.println("\n================================");
  Serial.println("ESP32 Rover Controller");
  Serial.println("================================");

  // Apply CORS to every WebServer response, including routes added later.
  server.enableCORS(true);

  ledcSetup(SERVO_CHANNEL, 50, 16);
  ledcAttachPin(SERVO_PIN, SERVO_CHANNEL);
  writeServoAngle(START_ANGLE);
  setupWifi();

  Serial.print("Wi-Fi Mode: ");
  Serial.println(wifiMode);
  Serial.print("IP source: ");
  Serial.println(ipSource());
  if (!WIFI_MODE_AP && USE_STATIC_IP) {
    Serial.print("Configured static IP: ");
    Serial.println(local_IP);
    Serial.print("Configured gateway: ");
    Serial.println(gateway);
  }
  Serial.print("ESP32 IP: ");
  Serial.println(currentIp());
  Serial.print("Gateway: ");
  Serial.println(currentGateway());
  Serial.print("Subnet: ");
  Serial.println(currentSubnet());
  Serial.print("RSSI: ");
  Serial.println(WIFI_MODE_AP ? 0 : WiFi.RSSI());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/wifi", HTTP_GET, handleWifi);
  server.on("/servo", HTTP_GET, handleServo);
  server.on("/command", HTTP_GET, handleCommand);
  server.on("/command", HTTP_POST, handleCommand);
  server.on("/status", HTTP_OPTIONS, handleOptions);
  server.on("/wifi", HTTP_OPTIONS, handleOptions);
  server.on("/servo", HTTP_OPTIONS, handleOptions);
  server.on("/command", HTTP_OPTIONS, handleOptions);
  server.begin();
  Serial.println("HTTP Server Started on port 80");
  Serial.println("Ready!");
}

void loop() {
  server.handleClient();
  while (roverSerial.available() > 0) {
    lastArduinoResponse = roverSerial.readStringUntil('\n');
    lastArduinoResponse.trim();
  }
  if (!WIFI_MODE_AP && WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi disconnected; attempting reconnect...");
    WiFi.reconnect();
    delay(1000);
  }
}
