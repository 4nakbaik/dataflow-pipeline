import streamlit as st
import pandas as pd
import requests
import os
import time
from typing import List, Dict

# Config
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
API_ENDPOINT = f"{BACKEND_URL}/api/summary"

st.set_page_config(
    page_title="Executive Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def fetch_analytics_data() -> List[Dict]:
    try:
        response = requests.get(API_ENDPOINT, timeout=5)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Connection to backend failed: {e}")
        return []

def calculate_metrics(df: pd.DataFrame) -> Dict:
    total_rev = df['total_revenue'].sum()
    total_tx = df['transaction_count'].sum()
    avg_order_value = (total_rev / total_tx) if total_tx > 0 else 0
    
    return {
        "revenue": total_rev,
        "transactions": total_tx,
        "aov": avg_order_value
    }

def render_sidebar():
    st.sidebar.header("Dashboard Controls")
    
    if st.sidebar.button("Refresh Data Now"):
        st.rerun()
        
    st.sidebar.markdown("---")
    
    enable_auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
    
    return enable_auto_refresh, refresh_interval

def render_dashboard():
    st.title("Sales Performance Dashboard")
    st.markdown("Real-time monitoring of sales pipeline performance.")
    st.markdown("---")

    # Fetch Data
    raw_data = fetch_analytics_data()

    if not raw_data:
        st.warning("No analytics data available. Please ensure the ETL pipeline has run.")
        return None, None 

    df = pd.DataFrame(raw_data)
    metrics = calculate_metrics(df)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric("Total Revenue", f"${metrics['revenue']:,.2f}")
    with kpi2:
        st.metric("Total Transactions", f"{metrics['transactions']:,}")
    with kpi3:
        st.metric("Avg. Order Value", f"${metrics['aov']:,.2f}")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Revenue by Category")
        st.bar_chart(df.set_index("category")['total_revenue'])

    with chart_col2:
        st.subheader("Transaction Volume by Category")
        st.bar_chart(df.set_index("category")['transaction_count'])
        
    with st.expander("View Detailed Raw Data"):
        st.dataframe(
            df.sort_values(by="total_revenue", ascending=False),
            use_container_width=True
        )

    return True 

if __name__ == "__main__":
    auto_refresh, interval = render_sidebar()
    data_loaded = render_dashboard()

    if auto_refresh and data_loaded:
        time.sleep(interval)
        st.rerun()