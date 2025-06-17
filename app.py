import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SMA Screener", layout="wide")
st.title("📊 SMA Crossover Screener with % Return")

# Load symbols
try:
    symbols_df = pd.read_csv("nse_symbols1.csv")
    symbols = symbols_df["Symbol"].dropna().tolist()
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    symbols = []

# Parameters
short_window = st.number_input("Short SMA Window", value=10, min_value=1)
long_window = st.number_input("Long SMA Window", value=50, min_value=2)
lookback_days = st.number_input("Lookback Days (for crossover)", value=5, min_value=1)

start_date = datetime.now() - timedelta(days=90)
end_date = datetime.now()

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

            recent = df.tail(lookback_days)
            buy_cross = recent[recent["Position"] == 1]
            sell_cross = recent[recent["Position"] == -1]

            if not buy_cross.empty:
                latest = buy_cross.iloc[-1]
                close = latest["Close"]
                long_sma = latest["Long_SMA"]
                ret_pct = ((close - long_sma) / long_sma) * 100

                buy_signals.append({
                    "Symbol": symbol,
                    "Close Price": round(close, 2),
                    f"Long SMA ({long_window})": round(long_sma, 2),
                    "Return %": round(ret_pct, 2),
                    "Crossover Date": latest.name.strftime("%Y-%m-%d")
                })

            if not sell_cross.empty:
                sell_signals.append(symbol)

        except Exception:
            continue
        progress.progress((i + 1) / len(symbols))

    st.success("Screener complete ✅")

    if buy_signals:
        st.subheader("📈 Buy Signals (Recent Crossovers)")
        df_buy = pd.DataFrame(buy_signals).sort_values("Return %", ascending=False)
        st.dataframe(df_buy, use_container_width=True)
    else:
        st.info("No Buy Signals in last few days")

    if sell_signals:
        st.subheader("📉 Sell Signals (Recent Crossovers)")
        st.write(sell_signals)
    else:
        st.info("No Sell Signals in last few days")
