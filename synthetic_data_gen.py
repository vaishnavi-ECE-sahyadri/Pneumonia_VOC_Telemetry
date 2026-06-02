import pandas as pd
import numpy as np
import datetime
import os

def generate_data():
    num_samples = 1500
    start_time = datetime.datetime.now()
    
    # 3 distinct VOC types for calibration
    # Alcohol: High Voltage (~3.5V), Low Rs (~8 kOhm)
    # Ketone: Moderate Voltage (~2.5V), Med Rs (~14 kOhm)
    # Aldehyde: Mod-High Voltage (~2.9V), Med-Low Rs (~11 kOhm)
    # Baseline: Low Voltage (~1.2V), High Rs (~22 kOhm)
    
    compounds = ['Baseline'] * 400 + ['Alcohol'] * 400 + ['Ketone'] * 350 + ['Aldehyde'] * 350
    
    data = []
    log_lines = []
    
    ms_counter = 258000
    
    for i in range(num_samples):
        compound = compounds[i]
        
        if compound == 'Baseline':
            v1_base, rs1_base = 1.2, 22.0
            v2_base, rs2_base = 1.3, 23.0
        elif compound == 'Alcohol':
            v1_base, rs1_base = 3.5, 8.0
            v2_base, rs2_base = 3.4, 8.5
        elif compound == 'Ketone':
            v1_base, rs1_base = 2.5, 14.0
            v2_base, rs2_base = 2.4, 15.0
        elif compound == 'Aldehyde':
            v1_base, rs1_base = 2.9, 11.0
            v2_base, rs2_base = 2.8, 12.0
            
        v1 = v1_base + np.random.normal(0, 0.1)
        rs1 = rs1_base + np.random.normal(0, 0.5)
        v2 = v2_base + np.random.normal(0, 0.1)
        rs2 = rs2_base + np.random.normal(0, 0.5)
        
        raw1 = int((v1 / 5.0) * 1023)
        raw2 = int((v2 / 5.0) * 1023)
        
        timestamp = (start_time + datetime.timedelta(seconds=i)).strftime("%H:%M:%S.%f")[:-3]
        
        # CSV Training Row
        data.append({
            "timestamp": timestamp,
            "v1": round(v1, 3), "rs1": round(rs1, 2),
            "v2": round(v2, 3), "rs2": round(rs2, 2),
            "compound": compound
        })
        
        # User's Log Format: 22:15:10.610 -> 258021,2402,1.936,14.19,2525,2.035,16.08
        ms_counter += np.random.randint(900, 1100)
        log_line = f"{timestamp} -> {ms_counter},{raw1},{v1:.3f},{rs1:.2f},{raw2},{v2:.3f},{rs2:.2f}"
        log_lines.append(log_line)
        
    df = pd.DataFrame(data)
    df.to_csv("voc_calibration_data.csv", index=False)
    
    with open("patient_log.txt", "w") as f:
        f.write("\n".join(log_lines))
        
    print("Generated voc_calibration_data.csv and patient_log.txt")

if __name__ == "__main__":
    np.random.seed(42)
    generate_data()
