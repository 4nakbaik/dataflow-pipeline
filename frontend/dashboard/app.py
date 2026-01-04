import streamlit as st
import pandas as pd
import requests
import os
import time
import plotly.graph_objects as go
from PIL import Image
from typing import List, Dict, Any

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
SUMMARY_API = f"{BACKEND_URL}/api/summary"
ICON_PATH = "frontend/assets/WoWoSaw1t.png"

try:
    icon_image = Image.open(ICON_PATH)
except:
    icon_image = "📊"

st.set_page_config(
    page_title="Sawiet Maniac",
    page_icon=icon_image,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
st.markdown("""
    <style>
        /* Global Background */
        .stApp {
            background-color: #f4f6f8; /* Abu-abu sangat muda (Professional Gray) */
            font-family: 'Roboto', sans-serif;
        }

        /* 1. METRIC CARDS (Kotak Data) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 6px; /* Sudut sedikit membulat */
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 20px;
            font-weight: 700;
            color: #333;
        }

        /* 2. CHART CONTAINERS (Kotak Grafik) */
        .stPlotlyChart {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            padding: 10px;
        }

        /* 3. SIDEBAR CLEANUP */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #ddd;
        }
        
        /* Judul Section di Sidebar */
        .sidebar-header {
            font-size: 14px;
            font-weight: bold;
            color: #444;
            margin-bottom: 10px;
        }

        /* Header Utama */
        h3 {
            padding-bottom: 10px;
        }
        
        /* Hapus margin atas default agar lebih rapat */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def fetch_data(endpoint: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(endpoint, timeout=3)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception:
        return []

def process_data(df: pd.DataFrame):
    if df.empty: return df
    df['MA_5'] = df['price_usd'].rolling(window=5).mean()
    df['pct_change'] = df['price_usd'].pct_change() * 100
    df['latency'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    return df

# --- CHART PLOTTING ---
def plot_main_chart(df: pd.DataFrame, coin: str):
    fig = go.Figure()
    
    # Dynamic Scale
    y_min, y_max = df['price_usd'].min(), df['price_usd'].max()
    padding = (y_max - y_min) * 0.1 if y_max != y_min else y_max * 0.01
    
    # Price Area
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['price_usd'],
        mode='lines', name='Price',
        line=dict(color='#2962FF', width=2),
        fill='tozeroy', fillcolor='rgba(41, 98, 255, 0.05)'
    ))
    
    # MA Line
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['MA_5'],
        mode='lines', name='MA(5)',
        line=dict(color='#FFAB00', width=1.5)
    ))

    fig.update_layout(
        title=dict(text=f"<b>{coin.upper()} / USD</b>", font=dict(size=14)),
        template="plotly_white",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10), # Padding dalam grafik
        hovermode="x unified",
        yaxis=dict(range=[y_min - padding, y_max + padding], side='right', tickprefix="$", showgrid=True, gridcolor='#f0f0f0'),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=1.02, x=0)
    )
    return fig

def plot_mini_charts(df: pd.DataFrame):
    # Volatility Bar
    fig1 = go.Figure(go.Bar(
        x=df['timestamp'], y=df['pct_change'],
        marker_color=['#00C853' if v >= 0 else '#D50000' for v in df['pct_change']]
    ))
    fig1.update_layout(title="Volatility %", template="plotly_white", height=200, margin=dict(l=0, r=0, t=30, b=0))

    # Distribution Hist
    fig2 = go.Figure(go.Histogram(
        x=df['price_usd'], nbinsx=10, marker_color='#2962FF', opacity=0.7
    ))
    fig2.update_layout(title="Price Dist.", template="plotly_white", height=200, margin=dict(l=0, r=0, t=30, b=0))

    # Latency Line
    fig3 = go.Figure(go.Scatter(
        x=df['timestamp'], y=df['latency'],
        mode='lines', line=dict(color='#90A4AE', width=1), fill='tozeroy'
    ))
    fig3.update_layout(title="Latency (ms)", template="plotly_white", height=200, margin=dict(l=0, r=0, t=30, b=0))
    
    return fig1, fig2, fig3

# --- MAIN APP ---
def main():
    with st.sidebar:
        st.markdown("<div class='sidebar-header'>INSTRUMENT SELECTOR</div>", unsafe_allow_html=True)
        
        summary_data = fetch_data(SUMMARY_API)
        df_summary = pd.DataFrame(summary_data)
        
        selected_coin = None
        if not df_summary.empty:
            options = {f"{r['coin_id'].upper()}": r['coin_id'] for _, r in df_summary.iterrows()}
            label = st.selectbox("Select Asset", list(options.keys()), label_visibility="collapsed")
            selected_coin = options[label]
            st.caption(f"Status: Connected ●")
        else:
            st.error("Connection Failed")
            st.caption("Check Backend")

        st.markdown("---")
        st.markdown("<div class='sidebar-header'>SYSTEM</div>", unsafe_allow_html=True)
        if st.button("Force Refresh", use_container_width=True):
            st.rerun()
        auto_refresh = st.checkbox("Live Feed", value=True)

    if not selected_coin:
        st.info("Waiting for data stream...")
        if auto_refresh: time.sleep(3); st.rerun()
        return

    # Fetch History
    history_url = f"{BACKEND_URL}/api/history/{selected_coin}"
    raw_hist = fetch_data(history_url)
    
    if not raw_hist:
        st.warning(f"Initializing feed for {selected_coin}...")
        if auto_refresh: time.sleep(3); st.rerun()
        return

    # Process
    df = pd.DataFrame(raw_hist)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = process_data(df)

    curr = df.iloc[-1]['price_usd']
    start = df.iloc[0]['price_usd']
    diff = curr - start
    vol = df.iloc[-1]['volume_24h']
    
    st.markdown(f"### {selected_coin.upper()} OVERVIEW")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1: st.metric("Current Price", f"${curr:,.2f}")
    with c2: st.metric("Session Change", f"{diff:+.2f}", f"{(diff/start)*100:.2f}%")
    with c3: st.metric("24h High", f"${df['price_usd'].max():,.2f}")
    with c4: st.metric("24h Low", f"${df['price_usd'].min():,.2f}")
    with c5: st.metric("Volume", f"${vol:,.0f}")

    st.markdown("---")
    
    fig_main = plot_main_chart(df, selected_coin)
    st.plotly_chart(fig_main, use_container_width=True)
    c_left, c_mid, c_right = st.columns(3)
    f1, f2, f3 = plot_mini_charts(df)
    
    with c_left: st.plotly_chart(f1, use_container_width=True)
    with c_mid: st.plotly_chart(f2, use_container_width=True)
    with c_right: st.plotly_chart(f3, use_container_width=True)

    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()