import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SMA Screener", layout="wide")
st.title("📊 SMA Crossover Screener with % Return")

# Load CSV file
try:
    symbols_df = pd.read_csv("symbols.csv")
    symbols = symbols_df["symbol"].dropna().tolist()
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    symbols = []

# UI controls
short_window = st.number_input("Short SMA Window", value=10, min_value=1)
long_window = st.number_input("Long SMA Window", value=50, min_value=2)
start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90))
end_date = st.date_input("End Date", datetime.now())

# Run button
if st.button("Run Screener") and symbols:
    buy_signals = []
    sell_signals = []

    progress = st.progress(0)
    for i, symbol in enumerate(symbols):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty or "Close" not in df:
                continue

            df["Short_SMA"] = df["Close"].rolling(window=short_window).mean()
            df["Long_SMA"] = df["Close"].rolling(window=long_window).mean()
            df.dropna(inplace=True)

            df["Signal"] = (df["Short_SMA"] > df["Long_SMA"]).astype(int)
            df["Position"] = df["Signal"].diff()

            if len(df) >= 1:
                last = df.iloc[-1]
                if last["Position"] == 1:
                    ret = ((last["Close"] - last["Long_SMA"]) / last["Long_SMA"]) * 100
                    buy_signals.append({
                        "Symbol": symbol,
                        "Close Price": round(last["Close"], 2),
                        f"Long SMA ({long_window})": round(last["Long_SMA"], 2),
                        "Return %": round(ret, 2)
                    })
                elif last["Position"] == -1:
                    sell_signals.append(symbol)
        except Exception as e:
            continue
        progress.progress((i + 1) / len(symbols))

    st.success("Screening completed!")

    if buy_signals:
        st.subheader("📈 Buy Signals")
        df_buy = pd.DataFrame(buy_signals).sort_values("Return %", ascending=False)
        st.dataframe(df_buy, use_container_width=True)
    else:
        st.info("No Buy Signals Today.")

    if sell_signals:
        st.subheader("📉 Sell Signals")
        st.write(sell_signals)
    else:
        st.info("No Sell Signals Today.")
