#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// Set AP credentials as requested
const char* ssid = "gandu";
const char* password = "gandu123";

WebServer server(80);

// HTML & JS CSS for the dashboard
// Kept as a raw string literal to easily serve from ESP32
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pneumonia VOC Real-Time ML Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-color: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.7);
      --glass-border: rgba(255, 255, 255, 0.1);
      --primary: #38bdf8;
      --normal: #10b981;
      --warning: #f59e0b;
      --critical: #ef4444;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    
    body {
      margin: 0;
      padding: 0;
      font-family: 'Outfit', sans-serif;
      background: var(--bg-color);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      background-image: radial-gradient(circle at top right, #1e293b, #0f172a);
    }

    h1 {
      margin-top: 40px;
      font-weight: 600;
      font-size: 2.5rem;
      text-align: center;
      background: -webkit-linear-gradient(#38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 1px;
    }

    .container {
      width: 90%;
      max-width: 1000px;
      margin: 20px auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }

    .glass-card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      transition: transform 0.3s ease;
    }

    .glass-card:hover {
      transform: translateY(-5px);
    }

    .card-title {
      font-size: 1.2rem;
      color: var(--text-muted);
      margin-bottom: 20px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
    }

    .value-display {
      font-size: 3rem;
      font-weight: 600;
      margin: 10px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .unit {
      font-size: 1rem;
      color: var(--text-muted);
      font-weight: 300;
    }

    .status-badge {
      padding: 8px 16px;
      border-radius: 50px;
      font-size: 0.9rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .status-normal { background: rgba(16, 185, 129, 0.2); color: var(--normal); border: 1px solid var(--normal); }
    .status-warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); }
    .status-critical { background: rgba(239, 68, 68, 0.2); color: var(--critical); border: 1px solid var(--critical); }

    .prediction-card {
      grid-column: 1 / -1;
      text-align: center;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.1) 0%, rgba(129, 140, 248, 0.1) 100%);
    }

    #ml-result {
      font-size: 2.5rem;
      font-weight: 600;
      margin-top: 15px;
    }

    .ml-explanation {
      margin-top: 15px;
      font-size: 0.95rem;
      color: var(--text-muted);
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
      line-height: 1.6;
    }

    .progress-bar-container {
      width: 100%;
      height: 8px;
      background: #334155;
      border-radius: 10px;
      margin-top: 15px;
      overflow: hidden;
    }

    .progress-bar {
      height: 100%;
      width: 0%;
      transition: width 0.5s ease-in-out, background-color 0.5s ease;
    }

    .btn-row {
      display: flex;
      gap: 12px;
      justify-content: center;
      margin: 10px 0 30px 0;
    }

    .btn {
      padding: 10px 24px;
      border-radius: 8px;
      font-family: 'Outfit', sans-serif;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.85; }
    .btn-download { background: #38bdf8; color: #0f172a; }
    .btn-clear    { background: #334155; color: #f8fafc; }

  </style>
</head>
<body>

  <h1>Patient VOC Risk Analysis</h1>

  <div class="btn-row">
    <a href="/api/csv" download="esp32_voc_log.csv">
      <button class="btn btn-download">⬇ Download CSV</button>
    </a>
    <button class="btn btn-clear" onclick="clearLog()">🗑 Clear Log</button>
  </div>

  <div class="container">
    <div class="glass-card">
      <div class="card-title">Sensor Ratio 1</div>
      <div class="value-display">
        <span id="ratio1-val">--</span>
      </div>
      <div class="progress-bar-container">
        <div id="ratio1-bar" class="progress-bar"></div>
      </div>
      <div style="margin-top:20px; display:flex; justify-content: space-between; align-items:center;">
        <span class="unit">Critical Threshold: > 2.00</span>
        <span id="ratio1-status" class="status-badge status-normal">NORMAL</span>
      </div>
    </div>

    <div class="glass-card">
      <div class="card-title">Sensor Ratio 2</div>
      <div class="value-display">
        <span id="ratio2-val">--</span>
      </div>
      <div class="progress-bar-container">
        <div id="ratio2-bar" class="progress-bar"></div>
      </div>
      <div style="margin-top:20px; display:flex; justify-content: space-between; align-items:center;">
        <span class="unit">Critical Threshold: > 2.10</span>
        <span id="ratio2-status" class="status-badge status-normal">NORMAL</span>
      </div>
    </div>

    <div class="glass-card prediction-card">
      <div class="card-title">ML Aggregation Engine</div>
      <div id="ml-result" class="status-critical" style="padding:20px; border-radius: 15px; border:none; background:transparent;">Waiting for Data...</div>
      <div class="ml-explanation">
        Algorithm applies non-linear thresholds on derived VOC ratios dynamically to evaluate biomarker concentrations directly without strict ppm dependencies.
      </div>
    </div>
  </div>

  <script>
    function updateDashboard() {
      // Fetch latest values from the ESP32 server
      fetch('/api/data')
        .then(response => response.json())
        .then(data => {
          const r1 = data.ratio1;
          const r2 = data.ratio2;

          document.getElementById('ratio1-val').innerText = r1.toFixed(3);
          document.getElementById('ratio2-val').innerText = r2.toFixed(3);

          // Machine Learning Logic / Thresholds Application
          // RATIO 1 Rules
          let r1State = "normal";
          let r1Color = "#10b981";
          if(r1 > 2.00) { r1State = "critical"; r1Color = "#ef4444"; }
          else if(r1 >= 1.94) { r1State = "warning"; r1Color = "#f59e0b"; }

          // RATIO 2 Rules
          let r2State = "normal";
          let r2Color = "#10b981";
          if(r2 > 2.10) { r2State = "critical"; r2Color = "#ef4444"; }
          else if(r2 >= 2.04) { r2State = "warning"; r2Color = "#f59e0b"; }
          
          // UI Updates for Ratio 1
          const r1StatusEl = document.getElementById('ratio1-status');
          r1StatusEl.className = 'status-badge status-' + r1State;
          r1StatusEl.innerText = r1State.toUpperCase();
          const r1Bar = document.getElementById('ratio1-bar');
          r1Bar.style.width = Math.min((r1 / 2.5) * 100, 100) + '%';
          r1Bar.style.backgroundColor = r1Color;

          // UI Updates for Ratio 2
          const r2StatusEl = document.getElementById('ratio2-status');
          r2StatusEl.className = 'status-badge status-' + r2State;
          r2StatusEl.innerText = r2State.toUpperCase();
          const r2Bar = document.getElementById('ratio2-bar');
          r2Bar.style.width = Math.min((r2 / 2.5) * 100, 100) + '%';
          r2Bar.style.backgroundColor = r2Color;

          // Overall Prediction Logic
          const resultEl = document.getElementById('ml-result');
          if (r1State === "critical" || r2State === "critical") {
            resultEl.innerText = "CRITICAL PNEUMONIA RISK DETECTED";
            resultEl.style.color = "var(--critical)";
            resultEl.style.textShadow = "0 0 10px rgba(239, 68, 68, 0.5)";
          } else if (r1State === "warning" || r2State === "warning") {
            resultEl.innerText = "ELEVATED BIOMARKERS - WARNING";
            resultEl.style.color = "var(--warning)";
            resultEl.style.textShadow = "0 0 10px rgba(245, 158, 11, 0.5)";
          } else {
            resultEl.innerText = "PATIENT VOC PATTERN NORMAL";
            resultEl.style.color = "var(--normal)";
            resultEl.style.textShadow = "0 0 10px rgba(16, 185, 129, 0.5)";
          }
        })
        .catch(err => console.log("Error fetching data: ", err));
    }

    // Refresh every 2 seconds
    setInterval(updateDashboard, 2000);
    // Initial fetch
    updateDashboard();

    function clearLog() {
      fetch('/api/clear').then(() => alert('Log cleared.'));
    }
  </script>
</body>
</html>
)rawliteral";

// Variables to simulate sensor readings
float ratio1 = 1.93;
float ratio2 = 2.03;

// CSV log buffer — stores up to 500 rows in memory
#define MAX_LOG_ROWS 500
struct LogRow {
  unsigned long ms;
  float ratio1;
  float ratio2;
};
LogRow logBuffer[MAX_LOG_ROWS];
int logCount = 0;

void updateSensorValues() {
  ratio1 += (random(100) / 1000.0) - 0.05;
  if (ratio1 < 1.90) ratio1 = 1.90;
  if (ratio1 > 2.05) ratio1 = 2.05;

  ratio2 += (random(100) / 1000.0) - 0.05;
  if (ratio2 < 2.00) ratio2 = 2.00;
  if (ratio2 > 2.15) ratio2 = 2.15;

  // Append to log buffer (circular — overwrite oldest when full)
  int idx = logCount % MAX_LOG_ROWS;
  logBuffer[idx] = { millis(), ratio1, ratio2 };
  logCount++;
}

void handleRoot() {
  server.send(200, "text/html", index_html);
}

void handleData() {
  updateSensorValues();

  String json = "{";
  json += "\"ratio1\": " + String(ratio1, 3) + ",";
  json += "\"ratio2\": " + String(ratio2, 3);
  json += "}";
  server.send(200, "application/json", json);
}

void handleCSV() {
  // Build CSV in chunks to avoid large String allocations
  server.setContentLength(CONTENT_LENGTH_UNKNOWN);
  server.sendHeader("Content-Type", "text/csv");
  server.sendHeader("Content-Disposition", "attachment; filename=esp32_voc_log.csv");
  server.send(200);

  // Header row
  server.sendContent("timestamp_ms,ratio1,ratio2\n");

  int total = min(logCount, MAX_LOG_ROWS);
  // If buffer has wrapped, start from the oldest entry
  int start = (logCount > MAX_LOG_ROWS) ? (logCount % MAX_LOG_ROWS) : 0;

  for (int i = 0; i < total; i++) {
    int idx = (start + i) % MAX_LOG_ROWS;
    String row = String(logBuffer[idx].ms) + "," +
                 String(logBuffer[idx].ratio1, 3) + "," +
                 String(logBuffer[idx].ratio2, 3) + "\n";
    server.sendContent(row);
  }
  server.sendContent("");  // signal end
}

void handleClearLog() {
  logCount = 0;
  server.send(200, "text/plain", "Log cleared.");
}

void setup() {
  Serial.begin(115200);

  // Setup Access Point
  Serial.println("Setting up Access Point...");
  WiFi.softAP(ssid, password);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);

  // Define HTTP routes
  server.on("/", handleRoot);
  server.on("/api/data", handleData);
  server.on("/api/csv", handleCSV);
  server.on("/api/clear", handleClearLog);

  // Start Server
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  delay(2);
}
