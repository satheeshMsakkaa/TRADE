import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.title("📊 SMA Crossover Screener with % Return")

# Load symbols.csv
try:
    symbol_df = pd.read_csv("nse_symbols1.csv")
    symbol_list = symbol_df["Symbol"].dropna().unique().tolist()
except Exception as e:
    st.error(f"CSV Load Error: {e}")
    symbol_list = []

short_window = st.number_input("Short SMA", value=10, min_value=1)
long_window = st.number_input("Long SMA", value=50, min_value=2)
start_date = st.date_input("Start Date", datetime.now() - timedelta(days=60))
end_date = st.date_input("End Date", datetime.now())

if st.button("Run Screener") and symbol_list:
    buy_data = []
    sell_list = []

    progress = st.progress(0)
    for idx, symbol in enumerate(symbol_list):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            df["Short_SMA"] = df["Close"].rolling(window=short_window).mean()
            df["Long_SMA"] = df["Close"].rolling(window=long_window).mean()
            df.dropna(inplace=True)

            df["Signal"] = (df["Short_SMA"] > df["Long_SMA"]).astype(int)
            df["Position"] = df["Signal"].diff()

            # Check for crossover today
            if df["Position"].iloc[-1] == 1:
                close_price = df["Close"].iloc[-1]
                long_sma = df["Long_SMA"].iloc[-1]
                return_pct = ((close_price - long_sma) / long_sma) * 100
                buy_data.append({
                    "Symbol": symbol,
                    "Close Price": round(close_price, 2),
                    "Long SMA": round(long_sma, 2),
                    "Return %": round(return_pct, 2)
                })
            if df["Position"].iloc[-1] == -1:
                sell_list.append(symbol)

        except Exception:
            continue
        progress.progress((idx + 1) / len(symbol_list))

    st.success("Screening Complete ✅")

    if buy_data:
        st.subheader("📈 Buy Signal Today (with % Return)")
        st.dataframe(pd.DataFrame(buy_data).sort_values(by="Return %", ascending=False))
    else:
        st.info("No Buy Signals Today")

    if sell_list:
        st.subheader("📉 Sell Signal Today")
        st.write(sell_list)
    else:
        st.info("No Sell Signals Today")
