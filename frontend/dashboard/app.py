import streamlit as st
import pandas as pd
import requests
import os
from typing import List, Dict

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
API_ENDPOINT = f"{BACKEND_URL}/api/summary"

st.set_page_config(page_title="Executive Dashboard", layout="wide")

def fetch_analytics_data() -> List[Dict]:
    """Fetches data from the backend API with error handling."""
    try:
        response = requests.get(API_ENDPOINT, timeout=5)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Connection to backend failed: {e}")
        return []

def render_dashboard():
    """Renders the main dashboard UI."""
    st.title("Sales Performance Dashboard")
    st.markdown("---")

    raw_data = fetch_analytics_data()

    if not raw_data:
        st.warning("No analytics data available. Please ensure the ETL pipeline has run.")
        return

    df = pd.DataFrame(raw_data)

    # Key Performance Indicators (KPIs)
    col1, col2 = st.columns(2)
    with col1:
        total_revenue = df['total_revenue'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with col2:
        total_tx = df['transaction_count'].sum()
        st.metric("Total Transactions", f"{total_tx:,}")

    # Visualizations
    st.subheader("Revenue Distribution")
    
    # Simple bar chart using Streamlit's native charting
    chart_data = df.set_index("category")['total_revenue']
    st.bar_chart(chart_data)

    # Detailed Data View
    with st.expander("View Raw Analytics Data"):
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    if st.button("Refresh Data"):
        st.rerun()
        
    render_dashboard()