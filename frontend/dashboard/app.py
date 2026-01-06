import streamlit as st
import pandas as pd
import requests
import os
import time
import plotly.graph_objects as go
from PIL import Image
from typing import List, Dict, Any, Tuple

# --- KONFIGURASI ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
SUMMARY_API = f"{BACKEND_URL}/api/summary"
ICON_PATH = "frontend/assets/WoWoSaw1t.png"

try:
    icon_image = Image.open(ICON_PATH)
except Exception:
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
        /* Latar Belakang Global */
        .stApp {
            background-color: #f4f6f8;
            font-family: 'Roboto', sans-serif;
        }

        /* 1. Gaya Kartu Metrik */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 6px;
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

        /* 2. Kontainer Grafik */
        .stPlotlyChart {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            padding: 10px;
        }

        /* 3. Penyesuaian Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #ddd;
        }
        
        .sidebar-header {
            font-size: 14px;
            font-weight: bold;
            color: #444;
            margin-bottom: 10px;
        }

        h3 {
            padding-bottom: 10px;
        }
        
        /* Penyesuaian padding kontainer utama */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI KALKULASI INDIKATOR TEKNIKAL ---

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

# --- FUNGSI PENGOLAHAN DATA ---

def fetch_data(endpoint: str) -> List[Dict[str, Any]]:
    """Mengambil data mentah dari API backend."""
    try:
        response = requests.get(endpoint, timeout=3)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception:
        return []

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Memproses dataframe dan menambahkan indikator teknikal."""
    if df.empty: return df
    
    # Metrik Dasar
    df['MA_5'] = df['price_usd'].rolling(window=5).mean()
    df['pct_change'] = df['price_usd'].pct_change() * 100
    df['latency'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # Indikator Lanjutan
    df['RSI'] = calculate_rsi(df['price_usd'])
    df['MACD'], df['MACD_Signal'] = calculate_macd(df['price_usd'])
    
    return df

# --- FUNGSI VISUALISASI GRAFIK ---

def plot_main_chart(df: pd.DataFrame, coin: str) -> go.Figure:
    """Membuat grafik utama (Harga dan Moving Average)."""
    fig = go.Figure()
    
    # Skala Dinamis untuk Sumbu Y
    y_min, y_max = df['price_usd'].min(), df['price_usd'].max()
    padding = (y_max - y_min) * 0.1 if y_max != y_min else y_max * 0.01
    
    # Area Harga
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['price_usd'],
        mode='lines', name='Price',
        line=dict(color='#2962FF', width=2),
        fill='tozeroy', fillcolor='rgba(41, 98, 255, 0.05)'
    ))
    
    # Garis MA
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['MA_5'],
        mode='lines', name='MA(5)',
        line=dict(color='#FFAB00', width=1.5)
    ))

    fig.update_layout(
        title=dict(text=f"<b>{coin.upper()} / USD</b>", font=dict(size=14)),
        template="plotly_white",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        yaxis=dict(
            range=[y_min - padding, y_max + padding], 
            side='right', 
            tickprefix="$", 
            showgrid=True, 
            gridcolor='#f0f0f0'
        ),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=1.02, x=0)
    )
    return fig

def plot_mini_charts(df: pd.DataFrame) -> Tuple[go.Figure, go.Figure, go.Figure]:
    """Membuat grafik analitik tambahan (Volatilitas, RSI, MACD)."""
    
    # Grafik 1: Volatilitas (%)
    fig1 = go.Figure()
    colors = ['#00C853' if v >= 0 else '#D50000' for v in df['pct_change']]
    fig1.add_trace(go.Bar(
        x=df['timestamp'], y=df['pct_change'],
        marker_color=colors
    ))
    fig1.update_layout(
        title="<b>Volatility %</b>", 
        template="plotly_white", 
        height=200, 
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(showgrid=True, gridcolor='#f3f4f6')
    )

    # Grafik 2: RSI (Momentum)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df['timestamp'], y=df['RSI'],
        mode='lines', line=dict(color='#7C4DFF', width=2)
    ))
    # Garis batas Overbought/Oversold
    fig2.add_shape(type="line", x0=df['timestamp'].min(), x1=df['timestamp'].max(), y0=70, y1=70, line=dict(color="red", width=1, dash="dot"))
    fig2.add_shape(type="line", x0=df['timestamp'].min(), x1=df['timestamp'].max(), y0=30, y1=30, line=dict(color="green", width=1, dash="dot"))
    
    fig2.update_layout(
        title="<b>RSI (14)</b>", 
        template="plotly_white", 
        height=200, 
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor='#f3f4f6')
    )

    # Grafik 3: MACD (Tren)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['timestamp'], y=df['MACD'],
        mode='lines', name='MACD', line=dict(color='#2962FF', width=1.5)
    ))
    fig3.add_trace(go.Scatter(
        x=df['timestamp'], y=df['MACD_Signal'],
        mode='lines', name='Signal', line=dict(color='#FFAB00', width=1.5)
    ))
    fig3.update_layout(
        title="<b>MACD</b>", 
        template="plotly_white", 
        height=200, 
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor='#f3f4f6')
    )
    
    return fig1, fig2, fig3

# --- LOGIKA UTAMA APLIKASI ---

def main():
    # Render Sidebar
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

    # Validasi Data Awal
    if not selected_coin:
        st.info("Waiting for data stream...")
        if auto_refresh: time.sleep(3); st.rerun()
        return

    # Pengambilan Data Historis
    history_url = f"{BACKEND_URL}/api/history/{selected_coin}"
    raw_hist = fetch_data(history_url)
    
    if not raw_hist:
        st.warning(f"Initializing feed for {selected_coin}...")
        if auto_refresh: time.sleep(3); st.rerun()
        return

    # Pemrosesan Data
    df = pd.DataFrame(raw_hist)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = process_data(df)

    # Kalkulasi Metrik Sesi
    curr = df.iloc[-1]['price_usd']
    start = df.iloc[0]['price_usd']
    diff = curr - start
    vol = df.iloc[-1]['volume_24h']
    
    # Judul Halaman
    st.markdown(f"### {selected_coin.upper()} OVERVIEW")
    
    # Tampilan Kartu Metrik
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Current Price", f"${curr:,.2f}")
    with c2: st.metric("Session Change", f"{diff:+.2f}", f"{(diff/start)*100:.2f}%")
    with c3: st.metric("24h High", f"${df['price_usd'].max():,.2f}")
    with c4: st.metric("24h Low", f"${df['price_usd'].min():,.2f}")
    with c5: st.metric("Volume", f"${vol:,.0f}")

    st.markdown("---")
    
    # Grafik Utama
    fig_main = plot_main_chart(df, selected_coin)
    st.plotly_chart(fig_main, use_container_width=True)
    
    # Grafik Analitik Tambahan
    c_left, c_mid, c_right = st.columns(3)
    f1, f2, f3 = plot_mini_charts(df)
    
    with c_left: st.plotly_chart(f1, use_container_width=True)
    with c_mid: st.plotly_chart(f2, use_container_width=True)
    with c_right: st.plotly_chart(f3, use_container_width=True)

    # Mekanisme Penyegaran Otomatis
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()