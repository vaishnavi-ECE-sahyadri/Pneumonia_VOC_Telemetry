import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import time

from data_processor import load_and_preprocess_data, extract_features

st.set_page_config(page_title="Pneumonia VOC Telemetry", layout="wide", page_icon="🧬", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* Apply Inter font generally but protect Streamlit's internal icons (which use ligatures) */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp { background-color: #0d1117; }
    
    h1, h2, h3 { color: #e6edf3 !important; font-weight: 600 !important; letter-spacing: -0.5px; }
    .stMarkdown p { color: #8b949e; font-size: 1.05rem; }

    .risk-card {
        background-color: #161b22; border-radius: 12px; padding: 30px 40px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2); border: 1px solid #30363d;
        text-align: center; flex: 1; transition: transform 0.2s ease-in-out;
    }
    .risk-title { font-size: 1.1rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
    .risk-status { font-size: 48px; font-weight: 600; margin-bottom: 10px; text-shadow: 0 0 20px rgba(255,255,255,0.1); }
    .status-High { color: #ff7b72; text-shadow: 0 0 15px rgba(255, 123, 114, 0.4); }
    .status-Moderate { color: #f2cc60; text-shadow: 0 0 15px rgba(242, 204, 96, 0.4); }
    .status-Low { color: #3fb950; text-shadow: 0 0 15px rgba(63, 185, 80, 0.4); }
    .risk-desc { color: #8b949e; font-size: 0.9rem; }
    [data-testid="stDataFrame"] { background-color: #161b22; border-radius: 12px; padding: 10px; border: 1px solid #30363d; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stat-container { background-color: #21262d; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #30363d; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("🧬 Pneumonia VOC Telemetry")
st.markdown("Configurable real-time monitoring of Alcohols, Ketones, and Aldehydes via TGS2620 Voltage Standards.")
st.markdown("---")

@st.cache_resource
def load_voc_model():
    if os.path.exists("pneumonia_voc_model.pkl"):
        return joblib.load("pneumonia_voc_model.pkl")
    return None

model = load_voc_model()
if model is None:
    st.error("⚠️ Inference model unavailable. Please initialize sequence models before proceeding.")
    st.stop()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063206.png", width=60)
    st.header("Pneumonia Risk Thresholds")
    st.markdown("Set your clinical voltage standards for VOC levels.")
    
    # Adjustable thresholds
    moderate_threshold = st.slider("Moderate Risk Voltage Threshold", min_value=1.5, max_value=3.0, value=2.0, step=0.1)
    high_threshold = st.slider("High Risk Voltage Threshold", min_value=2.0, max_value=4.5, value=3.0, step=0.1)
    
    st.markdown("---")
    st.header("Data Upload")
    st.markdown("Upload raw text logs (`->` format) or CSVs.")
    data_source = st.file_uploader("Select Telemetry Log", type=["txt", "csv"])

def process_and_display(df_source):
    df_processed = load_and_preprocess_data(df_source)
    
    # 1. Identify Compounds via ML
    features, _ = extract_features(df_processed)
    with st.spinner("Classifying VOC Compounds..."):
        time.sleep(0.3)
        compound_predictions = model.predict(features)
        
    df_processed['Predicted_Compound'] = compound_predictions
    
    if df_processed.empty:
        st.error("⚠️ The provided telemetry log is empty or could not be parsed. Please check the file format.")
        return
        
    # Analyze the most recent window of data (last 20 readings)
    recent_data = df_processed.tail(20)
    avg_voltage = recent_data['v1_filtered'].mean()
    if pd.isna(avg_voltage):
        avg_voltage = 0.0
        
    compounds_mode = recent_data['Predicted_Compound'].mode()
    most_common_compound = compounds_mode[0] if not compounds_mode.empty else "Unknown"
    
    # 2. Risk Calculation via Thresholds
    if avg_voltage >= high_threshold:
        risk_status = "High"
    elif avg_voltage >= moderate_threshold:
        risk_status = "Moderate"
    else:
        risk_status = "Low"

    col_status, col_metrics, col_info = st.columns([1.2, 0.8, 1])
    
    with col_status:
        st.markdown(f"""
            <div class="risk-card">
                <div class="risk-title">Pneumonia Risk Status</div>
                <div class="risk-status status-{risk_status}">{risk_status.upper()}</div>
                <div class="risk-desc">Based on configurable patient voltage standards.</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_metrics:
        st.markdown(f"""
            <div class="stat-container">
                <div style="font-size: 0.85rem; color: #8b949e;">Detected Compound</div>
                <div style="font-size: 1.5rem; color: #e6edf3; font-weight: bold;">{most_common_compound}</div>
            </div>
            <div class="stat-container">
                <div style="font-size: 0.85rem; color: #8b949e;">Current Avg Voltage</div>
                <div style="font-size: 1.5rem; color: #e6edf3; font-weight: bold;">{avg_voltage:.2f} V</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_info:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"**Threshold Logic Execution:**\nCurrent baseline is `{avg_voltage:.2f} V`.")
        if risk_status == "High":
            st.error(f"Value > High Threshold (`{high_threshold} V`). **Critical Warning**.")
        elif risk_status == "Moderate":
            st.warning(f"Value > Moderate Threshold (`{moderate_threshold} V`). Monitoring required.")
        else:
            st.success("Value is below risk thresholds. Nominal.")
            
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Sensor Output Traces")
    chart_col1, chart_col2 = st.columns(2)
    
    chart_layout = dict(
        template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20), height=320, hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False)
    )
    
    with chart_col1:
        fig_v1 = go.Figure()
        fig_v1.add_trace(go.Scatter(x=df_processed['timestamp'], y=df_processed['v1'], mode='lines', name='Raw V1', line=dict(color='rgba(88, 166, 255, 0.2)', width=1)))
        fig_v1.add_trace(go.Scatter(x=df_processed['timestamp'], y=df_processed['v1_filtered'], mode='lines', name='Filtered V1', line=dict(color='#58a6ff', width=2.5)))
        
        # Add Threshold Lines
        fig_v1.add_hline(y=high_threshold, line_dash="dash", line_color="#ff7b72", annotation_text="High Risk")
        fig_v1.add_hline(y=moderate_threshold, line_dash="dot", line_color="#f2cc60", annotation_text="Moderate Risk")
        
        fig_v1.update_layout(**chart_layout, title="Voltage Response vs Thresholds")
        st.plotly_chart(fig_v1, use_container_width=True)

    with chart_col2:
        fig_rs1 = go.Figure()
        fig_rs1.add_trace(go.Scatter(x=df_processed['timestamp'], y=df_processed['rs1'], mode='lines', name='Raw Rs1', line=dict(color='rgba(210, 168, 255, 0.2)', width=1)))
        fig_rs1.add_trace(go.Scatter(x=df_processed['timestamp'], y=df_processed['rs1_filtered'], mode='lines', name='Filtered Rs', line=dict(color='#d2a8ff', width=2.5)))
        fig_rs1.update_layout(**chart_layout, title="Internal Resistance (Baseline Integrity)")
        st.plotly_chart(fig_rs1, use_container_width=True)

    with st.expander("View Raw Log Output & Compound Classifications", expanded=False):
        st.dataframe(df_processed[['timestamp', 'v1', 'v1_filtered', 'rs1_filtered', 'Predicted_Compound']].tail(20), use_container_width=True)


if data_source:
    # Save uploaded file temporarily to process path
    with open("temp_upload", "wb") as f:
        f.write(data_source.getbuffer())
    file_name = "temp_upload.txt" if data_source.name.endswith(".txt") else "temp_upload.csv"
    os.rename("temp_upload", file_name)
    process_and_display(file_name)

elif os.path.exists("esp32_live.csv"):
    # Live feed from ESP32 bridge — auto-refresh every 3 seconds
    st.info("📡 Live ESP32 feed detected. Auto-refreshing every 3 seconds.")
    process_and_display("esp32_live.csv")
    time.sleep(3)
    st.rerun()

elif os.path.exists("patient_log.txt"):
    process_and_display("patient_log.txt")

else:
    st.warning("No data found. Please run the data generation script or start the ESP32 bridge.")
