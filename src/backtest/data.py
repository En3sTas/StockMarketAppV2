
import sys
import os

# Configure path to access core modules
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

def fetch_historical_data():
    tv = TvDatafeed()
    all_data = []

    print(f"🚀 Starting Historical Data Fetch for {len(SYMBOLS)} stocks...")

    for symbol in SYMBOLS:
        try:
            print(f"📥 Fetching {symbol}...")
            # Fetch last 5000 daily bars
            df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_daily, n_bars=5000)
            
            if df is None or df.empty:
                print(f"⚠️ No data for {symbol}")
                continue

            # Standardize Columns
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            df['Symbol'] = symbol

            # Pre-calculate Indicators for Engine
            
            # Trend
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            
            # Momentum
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            
            # Volatility
            df.ta.adx(length=14, append=True)
            df.ta.atr(length=14, append=True)
            
            # Previous Step Values (T-1) for Engine Input
            df['fiyat_onceki'] = df['Close'].shift(1)
            df['rsi_onceki'] = df['RSI_14'].shift(1)
            df['adx_onceki'] = df['ADX_14'].shift(1)
            df['hacim_onceki'] = df['Volume'].shift(1)
            df['macd_hist_onceki'] = df['MACDh_12_26_9'].shift(1)
            df['sma50_onceki'] = df['SMA_50'].shift(1)
            
            # Volume Ratio
            df['vol_avg_20'] = df['Volume'].rolling(20).mean()
            df['hacim_orani'] = df['Volume'] / df['vol_avg_20']

            # Swing Points
            df['swing_low'] = df['Low'].rolling(20).min()
            df['swing_high'] = df['High'].rolling(20).max()
            
            all_data.append(df)
            time.sleep(0.5) 

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")

    if all_data:
        full_df = pd.concat(all_data)
        # Save to Cache
        try:
            full_df.to_parquet(CACHE_FILE)
            print(f"✅ Data saved to {CACHE_FILE} ({len(full_df)} rows)")
        except Exception as e:
            print(f"⚠️ Parquet save failed ({e}), falling back to CSV")
            full_df.to_csv(CSV_FILE)
    else:
        print("❌ No data fetched.")

if __name__ == "__main__":
    fetch_historical_data()

