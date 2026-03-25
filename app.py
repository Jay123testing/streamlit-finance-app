import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Live Stock Quotes", page_icon="📈", layout="wide")

st.title("Live Stock Prices (ASX + Nasdaq/NYSE)")
st.write("Auto-refreshes every 30 seconds. Tap refresh if needed.")

tickers = {
    "MONKA KA Wisetech (ASX)": "WTC.AX",
    "MONKA KA Woodside (ASX)": "WDS.AX",
    "Audinate AD8 (ASX)": "AD8.AX",
    "MONKA KA GOODMEN": "GMG.AX",
    "MONKA KA CAR": "CAR.AX",
}

interval_sec = st.sidebar.selectbox("Refresh interval (seconds)", [15, 30, 60, 120], index=1)
rows_to_show = st.sidebar.slider("History rows", min_value=5, max_value=60, value=20, step=5)
st.sidebar.markdown("Data source: Yahoo Finance via yfinance")

@st.cache_data(ttl=30)
def get_data(symbol):
    now = datetime.utcnow()
    past = now - timedelta(days=5)
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval="1m", start=past, end=now, actions=False, prepost=True)
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df = df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["time", "open", "high", "low", "close", "volume"]
    df["time"] = df["time"].dt.tz_convert(None)
    return df

def display_quote(name, symbol):
    df = get_data(symbol)
    if df.empty:
        st.warning(f"No data for {name} ({symbol})")
        return

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest.close - prev.close
    change_pct = (change / prev.close) * 100 if prev.close != 0 else 0
    delta = f"{change:+.2f} ({change_pct:+.2f}%)"

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.subheader(f"{name}  {symbol}")
    with col2:
        st.metric("Latest Price", f"${latest.close:,.2f}", delta)
    with col3:
        st.metric("Volume", f"{int(latest.volume):,}")

    st.line_chart(df.set_index("time")["close"].tail(rows_to_show))
    st.dataframe(df.tail(rows_to_show).style.format({
        "open": "{:,.2f}", "high": "{:,.2f}", "low": "{:,.2f}", "close": "{:,.2f}", "volume": "{:,.0f}"
    }), use_container_width=True)

st.markdown("---")
for name, symbol in tickers.items():
    display_quote(name, symbol)
    st.markdown("---")

st.sidebar.write("Last updated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
st_autorefresh = st.experimental_set_query_params  # for Streamlit internal refresh path
if st.sidebar.button("Force refresh now"):
    st.experimental_rerun()

# auto-refresh via st.experimental_rerun timers:
st.write(f"Refreshing every {interval_sec} sec.")
st.experimental_rerun()
