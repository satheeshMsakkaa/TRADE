import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SMA Screener", layout="wide")
st.title("📊 SMA Crossover Screener with % Return")

# Load symbols from CSV
try:
    symbols_df = pd.read_csv("nse_symbols1.csv")
    symbols = symbols_df["Symbol"].dropna().tolist()
except Exception as e:
    st.error(f"Error loading symbols.csv: {e}")
    symbols = []

# UI Parameters
short_window = st.number_input("Short SMA Window", value=10, min_value=1)
long_window = st.number_input("Long SMA Window", value=50, min_value=2)
lookback_days = st.number_input("Lookback Days for Crossovers", value=5, min_value=1)

start_date = datetime.now() - timedelta(days=90)
end_date = datetime.now()

if st.button("🔍 Run Screener") and symbols:
    buy_signals = []
    sell_signals = []

    progress = st.progress(0)
    for idx, symbol in enumerate(symbols):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            df["Short_SMA"] = df["Close"].rolling(window=short_window).mean()
            df["Long_SMA"] = df["Close"].rolling(window=long_window).mean()
            df.dropna(inplace=True)

            df["Signal"] = (df["Short_SMA"] > df["Long_SMA"]).astype(int)
            df["Position"] = df["Signal"].diff()

            recent = df[df.index >= (df.index[-1] - pd.Timedelta(days=lookback_days))]

            # BUY
            buy_cross = recent[recent["Position"] == 1]
            if not buy_cross.empty:
                last_buy = buy_cross.iloc[-1]
                close = last_buy.get("Close")
                long_sma_val = last_buy.get("Long_SMA")

                if pd.notnull(close) and pd.notnull(long_sma_val) and long_sma_val != 0:
                    ret_pct = ((close - long_sma_val) / long_sma_val) * 100
                    buy_signals.append({
                        "Symbol": symbol,
                        "Crossover Date": last_buy.name.strftime("%Y-%m-%d"),
                        "Close Price": round(close, 2),
                        f"Long SMA ({long_window})": round(long_sma_val, 2),
                        "Return %": round(ret_pct, 2)
                    })

            # SELL
            sell_cross = recent[recent["Position"] == -1]
            if not sell_cross.empty:
                sell_signals.append({
                    "Symbol": symbol,
                    "Crossover Date": sell_cross.index[-1].strftime("%Y-%m-%d")
                })

        except Exception as e:
            st.warning(f"Error processing {symbol}: {e}")
            continue

        progress.progress((idx + 1) / len(symbols))

    st.success("✅ Screening complete!")

    # Display Buy
    if buy_signals:
        st.subheader("📈 Buy Signals")
        df_buy = pd.DataFrame(buy_signals)
        df_buy = df_buy.sort_values("Return %", ascending=False)
        st.dataframe(df_buy, use_container_width=True)
    else:
        st.info("No Buy Signals found.")

    # Display Sell
    if sell_signals:
        st.subheader("📉 Sell Signals")
        st.dataframe(pd.DataFrame(sell_signals), use_container_width=True)
    else:
        st.info("No Sell Signals found.")
