import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Base URL pointing to your live backend engine API
BACKEND_API_URL = "https://finance-backend-jdfd.onrender.com" # Update this after deploying to Render

st.set_page_config(layout="wide", page_title="India Market Dashboard")

# --- FETCH BACKEND DATA ---
@st.cache_data(ttl=600)
def fetch_api_data(endpoint: str, params: dict = None):
    try:
        response = requests.get(f"{BACKEND_API_URL}{endpoint}", params=params, timeout=90)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to connect to core backend API engine: {e}")
    return None

# Top Section Header: Pull Macro Variables
macro_data = fetch_api_data("/api/macro")
st.title("Indian Market Analytics Engine")

if macro_data:
    m1, m2, m3 = st.columns(3)
    m1.metric("RBI Repo Rate", macro_data.get("repo_rate", "N/A"))
    m2.metric("RBI Cash Reserve Ratio (CRR)", macro_data.get("crr", "N/A"))
    m3.metric("Architecture Status", "Decoupled Backend Engine")

# Sidebar Configuration Layout
st.sidebar.header("Screener Filters")
min_roe = st.sidebar.slider("Minimum ROE (%) Target", 0, 40, 12)
max_rsi = st.sidebar.slider("Maximum RSI Threshold", 30, 90, 70)

# Pull Primary Market Matrix from Backend API
with st.spinner("Streaming market telemetry from backend..."):
    market_raw = fetch_api_data("/api/market-data")

if market_raw:
    df = pd.DataFrame(market_raw)
    
    # 1. Market Visualization Treemap
    st.subheader("Market capitalization Weight vs. Trailing Performance")
    fig = px.treemap(
        df[df['Market_Cap_Cr'] > 0], 
        path=['Sector', 'Ticker'], 
        values='Market_Cap_Cr',
        color='Change_Pct', 
        color_continuous_scale='RdYlGn', 
        color_continuous_midpoint=0
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Dynamic Filtration Array
    st.divider()
    st.subheader("Filtered Screen Execution Matrix")
    filtered_df = df[(df['ROE_Pct'] >= min_roe) & (df['RSI_14'] <= max_rsi)]
    
    if not filtered_df.empty:
        st.dataframe(
            filtered_df.style.background_gradient(subset=['Change_Pct', 'ROE_Pct'], cmap='RdYlGn'),
            use_container_width=True
        )
    else:
        st.info("No corporate entities met the current performance execution parameters.")
