import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

st.set_page_config(page_title="📈 Multi-Symbol Strategy Dashboard", layout="wide")
st.title("📊 All NSE Symbols Strategy Signal Dashboard")

@st.cache_data
def load_nse_symbols():
    return pd.read_csv("nse_symbols1.csv")

symbols_df = load_nse_symbols()
symbols = symbols_df["Symbol"].tolist()
start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))

col1, col2 = st.columns(2)
with col1:
    short_sma = st.slider("Short SMA", 5, 50, 10)
with col2:
    long_sma = st.slider("Long SMA", 20, 200, 50)

if st.button("📊 Run All Strategies for All Symbols"):
    all_results = []

    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start_date)
            time.sleep(1)
            if df.empty:
                st.warning(f"No data found for {symbol}")
                continue
        except Exception as e:
            st.error(f"Failed to fetch data for {symbol}:{e}")
            continue

        df["SMA_Signal"] = "HOLD"
        df["RSI_Signal"] = "HOLD"
        df["MACD_Signal"] = "HOLD"

        # SMA
        df["Short_SMA"] = df["Close"].rolling(window=short_sma).mean()
        df["Long_SMA"] = df["Close"].rolling(window=long_sma).mean()
        for i in range(1, len(df)):
            if df["Short_SMA"][i] > df["Long_SMA"][i] and df["Short_SMA"][i-1] <= df["Long_SMA"][i-1]:
                df.at[i, "SMA_Signal"] = "BUY"
            elif df["Short_SMA"][i] < df["Long_SMA"][i] and df["Short_SMA"][i-1] >= df["Long_SMA"][i-1]:
                df.at[i, "SMA_Signal"] = "SELL"

        # RSI
        delta = df["Close"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
        for i in range(1, len(df)):
            if df["RSI"][i] < 30 and df["RSI"][i-1] >= 30:
                df.at[i, "RSI_Signal"] = "BUY"
            elif df["RSI"][i] > 70 and df["RSI"][i-1] <= 70:
                df.at[i, "RSI_Signal"] = "SELL"

        # MACD
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["SignalLine"] = df["MACD"].ewm(span=9, adjust=False).mean()
        for i in range(1, len(df)):
            if df["MACD"][i] > df["SignalLine"][i] and df["MACD"][i-1] <= df["SignalLine"][i-1]:
                df.at[i, "MACD_Signal"] = "BUY"
            elif df["MACD"][i] < df["SignalLine"][i] and df["MACD"][i-1] >= df["SignalLine"][i-1]:
                df.at[i, "MACD_Signal"] = "SELL"

        def extract_signals(df, signal_col, label):
            signals = df[df[signal_col] != "HOLD"][["Close", signal_col]].copy()
            signals = signals.rename(columns={"Close": "Price", signal_col: "Action"})
            signals["Date"] = df.index[df[signal_col] != "HOLD"]
            signals["Strategy"] = label
            return signals[["Date", "Price", "Action", "Strategy"]]

        all_signals = pd.concat([
            extract_signals(df, "SMA_Signal", "SMA"),
            extract_signals(df, "RSI_Signal", "RSI"),
            extract_signals(df, "MACD_Signal", "MACD")
        ])

        if not all_signals.empty:
            all_signals["Symbol"] = symbol
            all_results.append(all_signals)

    final_df = pd.concat(all_results).sort_values(["Date", "Symbol"])
    st.subheader("📋 All Symbol Signals")
    st.dataframe(final_df, use_container_width=True)
