import sys
import os

# Add parent directory to path to find config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pandas_ta as ta
import config
from tvDatafeed import TvDatafeed, Interval
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_FILE = os.path.join(BASE_DIR, "data", "backtest_data.parquet")
CSV_FILE = os.path.join(BASE_DIR, "data", "backtest_data.csv")

SYMBOLS = config.HISSELER
# Note: For full BIST100, we would expand this list. Keeping it manageable for dev.

def fetch_historical_data():
    tv = TvDatafeed()
    all_data = []

    print(f"🚀 Starting Historical Data Fetch for {len(SYMBOLS)} stocks...")

    for symbol in SYMBOLS:
        try:
            print(f"📥 Fetching {symbol}...")
            # Fetch last 5000 daily bars (approx 15-20 years or max available)
            df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_daily, n_bars=5000)
            
            if df is None or df.empty:
                print(f"⚠️ No data for {symbol}")
                continue

            # Standardize Columns
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            df['Symbol'] = symbol

            # --- PRE-CALCULATE INDICATORS ---
            # This ensures we have them for every single historical day
            
            # Trend
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            
            # Momentum
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            
            # Volatility / Trend Strength
            df.ta.adx(length=14, append=True)
            df.ta.atr(length=14, append=True)
            
            # Helper Columns for Engine (Shifted/Previous Values)
            # engine expects 'fiyat_onceki', 'adx_onceki', etc. which are T-1 values relative to the decision row
            df['fiyat_onceki'] = df['Close'].shift(1)
            df['rsi_onceki'] = df['RSI_14'].shift(1)
            df['adx_onceki'] = df['ADX_14'].shift(1)
            df['hacim_onceki'] = df['Volume'].shift(1)
            df['macd_hist_onceki'] = df['MACDh_12_26_9'].shift(1)
            df['sma50_onceki'] = df['SMA_50'].shift(1)
            
            # Volume Ratio (Relative to 20-day avg)
            df['vol_avg_20'] = df['Volume'].rolling(20).mean()
            df['hacim_orani'] = df['Volume'] / df['vol_avg_20']

            # Swing High/Low (20 day lookback)
            df['swing_low'] = df['Low'].rolling(20).min()
            df['swing_high'] = df['High'].rolling(20).max()
            
            all_data.append(df)
            time.sleep(0.5) # Courtesy delay

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")

    if all_data:
        full_df = pd.concat(all_data)
        # Save to HDF5 or Parquet for speed (CSV is slow for massive data)
        # Using CSV for compatibility if HDF5 libs missing, but Parquet is better.
        # Let's use Parquet if available, else CSV.
        try:
            full_df.to_parquet(CACHE_FILE)
            print(f"✅ Data saved to {CACHE_FILE} ({len(full_df)} rows)")
        except:
            full_df.to_csv(CSV_FILE)
            print(f"✅ Data saved to {CSV_FILE} ({len(full_df)} rows)")
    else:
        print("❌ No data fetched.")

if __name__ == "__main__":
    fetch_historical_data()
