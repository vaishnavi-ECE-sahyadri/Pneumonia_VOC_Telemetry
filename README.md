# IoT-Enabled Multi-Parameter Pneumonia Screening System

A real-time **Volatile Organic Compound (VOC) monitoring system** for early pneumonia risk screening. The project pairs an **ESP32** edge device (hosting a live web dashboard over WiFi AP) with a **Python ML pipeline** that classifies breath VOC compounds and visualizes risk on a **Streamlit** dashboard.

> **Sensors of interest:** TGS2620 (Alcohols), and paired channels for **Ketones** and **Aldehydes** — the canonical pneumonia-related VOCs.

---

## Repository Layout

```
phase-1/
├── app.py                    # Streamlit telemetry & risk dashboard
├── data_processor.py         # CSV / log loader + Savitzky-Golay filter
├── train_model.py            # Random Forest classifier trainer
├── esp32_bridge.py           # ESP32 → CSV bridge (HTTP poller)
├── synthetic_data_gen.py     # Synthetic calibration data generator
├── esp32_firmware/           # PlatformIO project for the ESP32
│   └── src/main.cpp          # AP server, simulated sensor, /api/data, /api/csv
├── voc_calibration_data.csv  # Generated training set
├── patient_log.txt           # Generated telemetry log (`timestamp -> raw,...` format)
└── esp32_live.csv            # Live output of esp32_bridge.py
```

---

## Architecture

```
┌─────────────────┐  HTTP/JSON   ┌──────────────────┐   CSV append   ┌────────────────┐
│  ESP32 (TGS2620)│ ───────────▶ │  esp32_bridge.py │ ─────────────▶ │ esp32_live.csv │
│  AP: gandu      │              │  (PC client)     │                └────────────────┘
└─────────────────┘              └──────────────────┘                       │
       │ WiFi AP                                                          │ auto-poll
       ▼                                                          ┌────────▼────────┐
   /web dashboard                                                 │   app.py (UI)   │
   ratio1 / ratio2                                                │   Streamlit     │
                                                                  └────────▲────────┘
                                                                           │
                                              ┌──────────────────┐         │
                                              │ pneumonia_voc_   │  predict│
                                              │ model.pkl (RF)   │ ────────┘
                                              └──────────────────┘
                                                       ▲
                                                       │ train
                                              ┌────────┴────────┐
                                              │  train_model.py │
                                              └─────────────────┘
```

---

## Quick Start

### 1. Generate synthetic calibration data
```bash
python synthetic_data_gen.py
```
Writes `voc_calibration_data.csv` (with `compound` labels: `Baseline`, `Alcohol`, `Ketone`, `Aldehyde`) and `patient_log.txt` in the same `timestamp -> raw,v1,rs1,...` log format produced by the ESP32.

### 2. Train the VOC compound classifier
```bash
python train_model.py
```
Produces `pneumonia_voc_model.pkl` — a `RandomForestClassifier(n_estimators=100)` over the four filtered sensor channels (`v1_filtered`, `rs1_filtered`, `v2_filtered`, `rs2_filtered`).

### 3. Flash the ESP32 (optional — synthetic path is sufficient)
```bash
cd esp32_firmware
pio run -t upload
```
The firmware brings up a **WiFi AP** (`ssid: gandu`, `password: gandu123`) and exposes:
- `GET /`           — live HTML/JS dashboard
- `GET /api/data`   — JSON `{"ratio1": ..., "ratio2": ...}`
- `GET /api/csv`    — full buffered log download
- `GET /api/clear`  — wipe the in-memory log

### 4. Bridge ESP32 → CSV (when using live firmware)
Connect your laptop to the `gandu` AP, then:
```bash
python esp32_bridge.py
```
Polls `http://192.168.4.1/api/data` every 2 s and appends to `esp32_live.csv`. It back-calculates `v` and `Rs` from the published sensor ratios.

### 5. Launch the dashboard
```bash
streamlit run app.py
```
The app auto-picks the data source in this order: **uploaded file → `esp32_live.csv` (auto-refresh every 3 s) → `patient_log.txt`**.

---

## Risk Model

The Streamlit app classifies the **most recent 20 readings** by:

1. **ML classification** — predicts the dominant VOC compound (Baseline / Alcohol / Ketone / Aldehyde).
2. **Voltage-threshold risk** — compares the running mean of `v1_filtered` against two user-tunable thresholds in the sidebar:

| Risk       | Default threshold (V) | Color  |
|------------|----------------------:|--------|
| Low        | < 2.0                 | green  |
| Moderate   | ≥ 2.0                 | amber  |
| High       | ≥ 3.0                 | red    |

Both thresholds are exposed as sliders in the sidebar so a clinician can recalibrate per-patient without editing code.

---

## Signal Processing

`data_processor.load_and_preprocess_data()` accepts either:
- A CSV with columns `timestamp, v1, rs1, v2, rs2` (and optional `compound` / `true_risk` labels), or
- A `.txt` log line of the form `HH:MM:SS.mmm -> ms,raw1,v1,rs1,raw2,v2,rs2`.

It applies a **Savitzky-Golay filter** (`window_length=51`, `polyorder=3`) to all four sensor channels, gracefully degrading the window size for short series. Filtered channels are suffixed `_filtered` and form the model's input feature set.

---

## Data Contracts

**ESP32 → bridge JSON**
```json
{ "ratio1": 1.937, "ratio2": 2.042 }
```

**Bridge CSV row** (`esp32_live.csv`)
```
timestamp,v1,rs1,v2,rs2
22:15:10.610,1.936,14.19,2.035,16.08
```

**Calibration CSV row** (`voc_calibration_data.csv`)
```
timestamp,v1,rs1,v2,rs2,compound
22:15:10.610,1.21,22.04,1.30,23.11,Baseline
```

---

## Tech Stack

- **Edge:** ESP32 (Arduino framework, PlatformIO), C++ `WebServer`, simulated TGS2620-style voltage divider
- **ML:** Python, scikit-learn `RandomForestClassifier`, joblib serialization
- **Signal:** `scipy.signal.savgol_filter`
- **UI:** Streamlit + Plotly (dark theme, glassmorphism cards)
- **Bridge:** `requests` polling loop

---

## Phase 1 Scope

This is **Phase 1** — the synthetic data and end-to-end pipeline. Real breath-sample acquisition, patient validation, and a calibrated parts-per-million model are deferred to later phases. All threshold values are configurable defaults intended for demonstration, not clinical use.

---

## License

Internal research project — no license specified.
