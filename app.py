import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(page_title="Live Indian Market Dashboard", layout="wide")

# Define tickers
TICKERS = {
    "Indices": ["^NSEI"],
    "Stocks": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS"],
    "Macro": ["INR=X", "BZ=F", "^TNX"]
}

NAMES = {
    "^NSEI": "Nifty 50",
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "BHARTIARTL.NS": "Bharti Airtel",
    "SBIN.NS": "SBI",
    "INFY.NS": "Infosys",
    "LICI.NS": "LIC",
    "ITC.NS": "ITC",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "INR=X": "INR/USD",
    "BZ=F": "Brent Crude",
    "^TNX": "US 10Y Yield"
}

@st.cache_data(ttl=300)
def get_data(ticker):
    """Fetch data with retry logic and error handling."""
    try:
        # Fetch data with a longer period to ensure enough points for MAs
        data = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        
        if data.empty:
            return None
            
        # Standardize column names (handle multi-index or varying cases)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.columns = [c.capitalize() for c in data.columns]
        
        # Ensure 'Close' exists
        if 'Close' not in data.columns:
            return None
            
        # Calculate Moving Averages
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        
        return data
    except Exception as e:
        # Log error to console (visible in Streamlit logs)
        print(f"Error fetching {ticker}: {e}")
        return None

def get_signal(data):
    """Determine bullish/bearish signal based on moving averages."""
    if data is None or len(data) < 50:
        return "Insufficient Data", "gray"
    
    last_close = float(data['Close'].iloc[-1])
    last_ma20 = float(data['MA20'].iloc[-1])
    last_ma50 = float(data['MA50'].iloc[-1])
    
    if pd.isna(last_ma20) or pd.isna(last_ma50):
        return "Calculating...", "gray"
    
    if last_close > last_ma20 and last_close > last_ma50:
        return "Bullish (Above MAs)", "green"
    elif last_close < last_ma20 and last_close < last_ma50:
        return "Bearish (Below MAs)", "red"
    else:
        return "Neutral / Crossover", "orange"

# App UI
st.title("📊 Live Indian Market Dashboard")
st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar
st.sidebar.header("Navigation")
selected_category = st.sidebar.radio("Select View", ["All", "Indices", "Stocks", "Macro"])

# Layout logic
categories_to_show = ["Indices", "Macro", "Stocks"] if selected_category == "All" else [selected_category]

for cat in categories_to_show:
    st.header(f"📈 {cat}")
    tickers = TICKERS[cat]
    
    # Grid layout for metrics
    cols = st.columns(4)
    for i, ticker in enumerate(tickers):
        with cols[i % 4]:
            data = get_data(ticker)
            if data is not None and len(data) >= 2:
                last_close = float(data['Close'].iloc[-1])
                prev_close = float(data['Close'].iloc[-2])
                pct_change = ((last_close - prev_close) / prev_close) * 100
                
                signal, color = get_signal(data)
                
                st.metric(
                    label=NAMES.get(ticker, ticker),
                    value=f"{last_close:,.2f}",
                    delta=f"{pct_change:.2f}%"
                )
                st.markdown(f"**Signal:** :{color}[{signal}]")
                if not pd.isna(data['MA20'].iloc[-1]):
                    st.caption(f"MA20: {data['MA20'].iloc[-1]:.2f} | MA50: {data['MA50'].iloc[-1]:.2f}")
            else:
                st.warning(f"Data unavailable for {NAMES.get(ticker, ticker)}")

# Detailed Chart Section
st.divider()
st.header("🔍 Detailed Technical View")
all_tickers = TICKERS["Indices"] + TICKERS["Macro"] + TICKERS["Stocks"]
selected_ticker = st.selectbox("Select Asset for Analysis", all_tickers, format_func=lambda x: NAMES.get(x, x))

chart_data = get_data(selected_ticker)
if chart_data is not None:
    fig = go.Figure()
    # Price Line
    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'], name='Price', line=dict(color='#00CC96', width=2)))
    # Moving Averages
    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['MA20'], name='20-Day MA', line=dict(color='#636EFA', width=1.5, dash='dot')))
    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['MA50'], name='50-Day MA', line=dict(color='#EF553B', width=1.5, dash='dash')))
    
    fig.update_layout(
        title=f"{NAMES.get(selected_ticker, selected_ticker)} Historical Performance",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Could not generate chart for the selected asset.")

st.markdown("---")
st.caption("Real-time data via yfinance. Indicators calculated on daily closing prices.")
