"""
ESP32 Bridge — polls the ESP32 AP and writes live data to esp32_live.csv
Run this while connected to the ESP32 WiFi hotspot (ssid: gandu).
Streamlit will auto-reload from that CSV.
"""

import requests
import csv
import time
import os
from datetime import datetime

ESP32_URL = "http://192.168.4.1/api/data"
OUTPUT_CSV = "esp32_live.csv"
POLL_INTERVAL = 2  # seconds

FIELDNAMES = ["timestamp", "v1", "rs1", "v2", "rs2"]

# The ESP32 exposes ratio1 and ratio2.
# ratio = v_sensor / v_baseline, so we back-calculate approximate voltages.
# Baseline voltage assumed ~1.0V, load resistor ~10kOhm (adjust to match your circuit).
V_BASELINE = 1.0
RL_KOHM = 10.0

def ratio_to_voltage_and_rs(ratio):
    """Convert a sensor ratio back to approximate voltage and resistance."""
    v = ratio * V_BASELINE
    # Rs = RL * (Vc - V) / V  where Vc = 5V supply
    v = max(v, 0.001)  # avoid div by zero
    rs = RL_KOHM * (5.0 - v) / v
    return round(v, 3), round(rs, 2)

def main():
    # Write CSV header if file doesn't exist
    write_header = not os.path.exists(OUTPUT_CSV)
    
    print(f"Bridge started. Writing to {OUTPUT_CSV}")
    print(f"Polling {ESP32_URL} every {POLL_INTERVAL}s")
    print("Press Ctrl+C to stop.\n")

    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        while True:
            try:
                resp = requests.get(ESP32_URL, timeout=3)
                data = resp.json()

                ratio1 = data["ratio1"]
                ratio2 = data["ratio2"]

                v1, rs1 = ratio_to_voltage_and_rs(ratio1)
                v2, rs2 = ratio_to_voltage_and_rs(ratio2)

                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                row = {
                    "timestamp": timestamp,
                    "v1": v1,
                    "rs1": rs1,
                    "v2": v2,
                    "rs2": rs2,
                }
                writer.writerow(row)
                f.flush()  # write immediately so Streamlit sees it

                print(f"{timestamp}  ratio1={ratio1:.3f}  v1={v1}V  rs1={rs1}kΩ  |  ratio2={ratio2:.3f}  v2={v2}V  rs2={rs2}kΩ")

            except requests.exceptions.ConnectionError:
                print("Connection failed — is your laptop connected to the ESP32 WiFi?")
            except Exception as e:
                print(f"Error: {e}")

            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
