import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SMA Screener", layout="wide")
st.title("📊 SMA Crossover Screener with % Return")

# Load symbols.csv
try:
    symbols_df = pd.read_csv("nse_symbols1.csv")
    symbols = symbols_df["Symbol"].dropna().tolist()
except Exception as e:
    st.error(f"Error loading symbols.csv: {e}")
    symbols = []

# UI Controls
short_window = st.number_input("Short SMA Window", value=10, min_value=1)
long_window = st.number_input("Long SMA Window", value=50, min_value=2)
lookback_days = st.number_input("Lookback Days (to detect crossover)", value=5, min_value=1)

# Date range (fixed range to avoid user confusion)
start_date = datetime.now() - timedelta(days=1008)
end_date = datetime.now()

if st.button("🔍 Run Screener") and symbols:
    buy_signals = []
    sell_signals = []

    progress = st.progress(0)
    for idx, symbol in enumerate(symbols):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty or "Close" not in df:
                continue

            df["Short_SMA"] = df["Close"].rolling(window=short_window).mean()
            df["Long_SMA"] = df["Close"].rolling(window=long_window).mean()
            df.dropna(inplace=True)

            df["Signal"] = (df["Short_SMA"] > df["Long_SMA"]).astype(int)
            df["Position"] = df["Signal"].diff()

            # Check last N days for crossover
            recent = df[df.index >= (df.index[-1] - pd.Timedelta(days=lookback_days))]

            # BUY
            buy_cross = recent[recent["Position"] == 1]
            if not buy_cross.empty:
                last_buy = buy_cross.iloc[-1]
                close = last_buy["Close"]
                long_sma = last_buy["Long_SMA"]
                ret_pct = ((close - long_sma) / long_sma) * 100

                buy_signals.append({
                    "Symbol": symbol,
                    "Crossover Date": last_buy.name.strftime("%Y-%m-%d"),
                    "Close Price": round(close, 2),
                    f"Long SMA ({long_window})": round(long_sma, 2),
                    "Return %": round(ret_pct, 2)
                })

            # SELL
            sell_cross = recent[recent["Position"] == -1]
            if not sell_cross.empty:
                sell_signals.append({
                    "Symbol": symbol,
                    "Crossover Date": sell_cross.index[-1].strftime("%Y-%m-%d")
                })

        except Exception:
            continue
        progress.progress((idx + 1) / len(symbols))

    st.success("✅ Screening complete!")

    if buy_signals:
        st.subheader("📈 Buy Signals")
        df_buy = pd.DataFrame(buy_signals).sort_values("Return %", ascending=False)
        st.dataframe(df_buy, use_container_width=True)
    else:
        st.info("No Buy Signals in last few days.")

    if sell_signals:
        st.subheader("📉 Sell Signals")
        st.dataframe(pd.DataFrame(sell_signals))
    else:
        st.info("No Sell Signals in last few days.")

    # Optional chart for visualization
    st.subheader("📊 SMA Chart Viewer (Optional)")
    selected = st.selectbox("Choose a symbol to visualize:", symbols)
    if selected:
        df_chart = yf.download(selected, start=start_date, end=end_date, progress=False)
        df_chart["Short_SMA"] = df_chart["Close"].rolling(window=short_window).mean()
        df_chart["Long_SMA"] = df_chart["Close"].rolling(window=long_window).mean()
        st.line_chart(df_chart[["Close", "Short_SMA", "Long_SMA"]].dropna().tail(100))
