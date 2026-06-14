import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Your specific Render backend URL
BACKEND_API_URL = "https://finance-backend-jdfd.onrender.com" 

st.set_page_config(layout="wide", page_title="India Market Dashboard")

# --- FETCH BACKEND DATA ---
@st.cache_data(ttl=600)
def fetch_api_data(endpoint: str, params: dict = None):
    try:
        # STRIP out any accidental spaces or slashes from your URL string
        clean_base_url = BACKEND_API_URL.strip().rstrip('/')
        clean_endpoint = endpoint.strip()
        
        res = requests.get(f"{clean_base_url}{clean_endpoint}", params=params, timeout=90)
        
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Backend Error {res.status_code}: {res.text}")
    except requests.exceptions.Timeout:
        st.error("Request Timed Out. The backend is calculating, please refresh in 30 seconds.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return None

# --- TOP MACRO SECTION ---
st.title("🇮🇳 Institutional Market Engine")
macro_data = fetch_api_data("/api/macro")

if macro_data:
    m1, m2 = st.columns(2)
    m1.metric("RBI Repo Rate", macro_data.get("repo_rate", "N/A"))
    m2.metric("RBI CRR", macro_data.get("crr", "N/A"))
else:
    st.warning("Could not connect to backend for Macro Data.")

# --- MAIN DASHBOARD TABS ---
tab1, tab2 = st.tabs(["📊 Market Screener & Heatmap", "🔬 Deep Dive Valuation"])

# --- TAB 1: SCREENER & TREEMAP ---
with tab1:
    st.sidebar.header("Screener Filters")
    min_roe = st.sidebar.slider("Minimum ROE (%)", 0, 40, 10)
    max_rsi = st.sidebar.slider("Maximum RSI", 30, 90, 70)
    
    with st.spinner("Fetching market telemetry (this may take 45-60s on the first load)..."):
        market_raw = fetch_api_data("/api/market-data")
    
    if market_raw:
        df = pd.DataFrame(market_raw)
        if not df.empty:
            # 1. Heatmap
            st.subheader("Market Capitalization vs. Performance")
            fig = px.treemap(
                df[df['Market_Cap_Cr'] > 0], 
                path=['Sector', 'Ticker'], 
                values='Market_Cap_Cr',
                color='Change_Pct', 
                color_continuous_scale='RdYlGn', 
                color_continuous_midpoint=0
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 2. Screener
            st.divider()
            st.subheader("Filtered Screen Execution Matrix")
            filtered_df = df[(df['ROE_Pct'] >= min_roe) & (df['RSI_14'] <= max_rsi)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.style.background_gradient(subset=['Change_Pct', 'ROE_Pct'], cmap='RdYlGn'), use_container_width=True)
            else:
                st.info("No stocks match the current ROE and RSI filters.")
        else:
            st.warning("Backend connected, but returned an empty stock list.")
    else:
        st.error("Market data pipeline failed to return data.")

# --- TAB 2: VALUATION ENGINES ---
with tab2:
    st.subheader("Institutional Equity Analysis & Valuation Matrix")
    selected_ticker = st.text_input("Enter NSE Ticker (e.g., RELIANCE, TCS):", value="RELIANCE")
    
    if st.button("Execute Deep Audit"):
        with st.spinner(f"Running CFA valuation models for {selected_ticker}..."):
            audit_data = fetch_api_data(f"/api/valuation/{selected_ticker}")
            
            if audit_data and "valuation_metrics" in audit_data:
                v_metrics = audit_data["valuation_metrics"]
                dupont = audit_data["dupont_decomposition"]
                
                st.header(f"{audit_data.get('company_name', selected_ticker)} ({audit_data.get('sector', 'N/A')})")
                
                st.subheader("1. Corporate Capital Structure & Cash Flow Generation")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Calculated WACC", f"{v_metrics['wacc_pct']}%")
                c2.metric("Cost of Equity (Ke)", f"{v_metrics['cost_of_equity_pct']}%")
                c3.metric("Cost of Debt (Kd)", f"{v_metrics['cost_of_debt_pct']}%")
                c4.metric("FCFF (Cr)", f"₹ {v_metrics['fcff_cr']}")
                c5.metric("FCFE (Cr)", f"₹ {v_metrics['fcfe_cr']}")

                st.divider()
                st.subheader("2. CFA Level 2 Five-Stage DuPont Breakdown")
                dp_cols = st.columns(5)
                dp_cols[0].metric("Tax Burden", f"{dupont['tax_burden']}")
                dp_cols[1].metric("Interest Burden", f"{dupont['interest_burden']}")
                dp_cols[2].metric("Operating Profit Margin", f"{dupont['ebit_margin_pct']}%")
                dp_cols[3].metric("Asset Turnover Ratio", f"{dupont['asset_turnover']}x")
                dp_cols[4].metric("Financial Leverage", f"{dupont['financial_leverage']}x")
                
                st.info(f"**Decomposed Target ROE:** {dupont['dupont_roe_pct']}%")
            else:
                st.error("Failed to compile metrics. The ticker may be invalid or Yahoo Finance is blocking the request.")
