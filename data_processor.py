import pandas as pd
from scipy.signal import savgol_filter

def load_and_preprocess_data(file_path):
    """
    Loads raw CSV data or text logs and applies a Savitzky-Golay filter to reduce noise 
    on the voltage and resistance readings.
    """
    if str(file_path).endswith('.txt'):
        data = []
        with open(file_path, 'r') as file:
            for line in file:
                if '->' in line:
                    timestamp_part, values_part = line.split('->')
                    timestamp = timestamp_part.strip()
                    values = values_part.strip().split(',')
                    if len(values) >= 7:
                        # expected: ms, raw1, v1, rs1, raw2, v2, rs2
                        ms, raw1, v1, rs1, raw2, v2, rs2 = values[:7]
                        data.append({
                            "timestamp": timestamp,
                            "v1": float(v1),
                            "rs1": float(rs1),
                            "v2": float(v2),
                            "rs2": float(rs2)
                        })
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(file_path)
    
    # Apply filter to sensor 1 and 2 readings
    # window_length = 51 (must be odd), polyorder = 3
    for col in ['v1', 'rs1', 'v2', 'rs2']:
        if col in df.columns:
            window = min(51, len(df) - (1 if len(df) % 2 == 0 else 0))
            if window >= 3:
                df[f'{col}_filtered'] = savgol_filter(df[col], window_length=window, polyorder=3)
            else:
                df[f'{col}_filtered'] = df[col]
                
    return df

def extract_features(df):
    """
    Extracts features for the machine learning model.
    """
    feature_cols = ['v1_filtered', 'rs1_filtered', 'v2_filtered', 'rs2_filtered']
    if 'compound' in df.columns:
        return df[feature_cols], df['compound']
    elif 'true_risk' in df.columns: # fallback
        return df[feature_cols], df['true_risk']
    return df[feature_cols], None

