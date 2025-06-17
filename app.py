import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.title("🔍 SMA Crossover Debug Mode")

try:
    symbols_df = pd.read_csv("nse_symbols1.csv")
    symbols = symbols_df["Symbol"].dropna().tolist()
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    symbols = []

short_window = st.number_input("Short SMA Window", value=10, min_value=1)
long_window = st.number_input("Long SMA Window", value=50, min_value=2)
lookback_days = st.number_input("Lookback Days for Crossovers", value=5, min_value=1)
start_date = datetime.now() - timedelta(days=90)
end_date = datetime.now()

if st.button("Run Debug Screener"):
    buy_signals = []
    sell_signals = []

    for symbol in symbols:
        st.write(f"Checking: {symbol}")
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty:
                st.warning(f"No data for {symbol}")
                continue

            df["Short_SMA"] = df["Close"].rolling(window=short_window).mean()
            df["Long_SMA"] = df["Close"].rolling(window=long_window).mean()
            df.dropna(inplace=True)

            df["Signal"] = (df["Short_SMA"] > df["Long_SMA"]).astype(int)
            df["Position"] = df["Signal"].diff()

            st.dataframe(df.tail(90))

            last_pos = df["Position"].iloc[-1]
            if last_pos == 1:
                st.success(f"✅ BUY signal for {symbol}")
                buy_signals.append(symbol)
            elif last_pos == -1:
                st.error(f"❌ SELL signal for {symbol}")
                sell_signals.append(symbol)
            else:
                st.info(f"No recent crossover for {symbol}")

        except Exception as e:
            st.error(f"Error processing {symbol}: {e}")

    st.write("Done.")
