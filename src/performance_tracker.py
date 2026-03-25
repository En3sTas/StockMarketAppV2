"""
performance_tracker.py
---------------------------------------------------------
Tracks and backfills the future performance (T+1, T+5, T+21) 
of historical recommendations. Designed to run automatically 
so that missing days are filled in even if the bot is paused.
Returns all values and strings in English.
---------------------------------------------------------
"""

import os
import sys
from datetime import datetime
import pandas as pd
import yfinance as yf

# Load environment configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

try:
    import psycopg2
except ImportError:
    print("psycopg2 is required but not installed.")
    sys.exit(1)

SELECT_PENDING_QUERY = """
    SELECT id, symbol, signal_date, price, 
           price_1day, price_1week, price_1month
    FROM signal_history
    WHERE price_1day IS NULL 
       OR price_1week IS NULL 
       OR price_1month IS NULL
"""

UPDATE_QUERY = """
    UPDATE signal_history
    SET price_1day = %s, perf_1day = %s,
        price_1week = %s, perf_1week = %s,
        price_1month = %s, perf_1month = %s
    WHERE id = %s
"""

def fetch_historical_prices(symbol):
    """Fetches the last 6 months of daily data using yfinance."""
    yf_symbol = symbol + ".IS" if not symbol.endswith(".IS") else symbol
    try:
        df = yf.download(yf_symbol, period="6mo", interval="1d", progress=False)
        if df is None or df.empty:
            return None
        
        # Safely extract 'Close' depending on yfinance pandas structure
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df['Close'][yf_symbol]
        else:
            close_series = df['Close']
            
        return close_series.dropna()
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return None

def find_price_after_days(close_series, signal_date, trading_days):
    """Finds the closing price exactly `trading_days` after `signal_date`."""
    if close_series is None or close_series.empty:
        return None
        
    # Get all dates occurring strictly after the signal
    future_dates = close_series[close_series.index.date > signal_date.date()]
    
    # If we have enough trading days elapsed, grab the (trading_days - 1) index
    if len(future_dates) >= trading_days:
        return float(future_dates.iloc[trading_days - 1])
    return None

def calc_perf(entry_price, exit_price):
    if entry_price and exit_price and float(entry_price) > 0:
        return round(((float(exit_price) - float(entry_price)) / float(entry_price)) * 100, 2)
    return None

def run_performance_tracker():
    print("📈 Starting Performance Tracking module...")
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
    except Exception as e:
        print(f"Database connection blocked: {e}")
        return

    cur.execute(SELECT_PENDING_QUERY)
    rows = cur.fetchall()
    
    if not rows:
        print("✅ No pending signals require performance updates.")
        conn.close()
        return
        
    print(f"🔎 Found {len(rows)} signals to verify.")
    
    # Group by symbol to minimize HTTP requests
    symbols = set(row[1] for row in rows)
    price_cache = {}
    
    print(f"⬇️ Downloading missing historical data for {len(symbols)} unique symbols...")
    for sym in symbols:
        series = fetch_historical_prices(sym)
        if series is not None:
            price_cache[sym] = series
            
    updates_made = 0
    
    for row in rows:
        req_id, symbol, sig_date, entry_price, p1d, p1w, p1m = row
        
        if symbol not in price_cache:
            continue
            
        series = price_cache[symbol]
        
        # Re-calculate missing values
        new_p1d = float(p1d) if p1d is not None else find_price_after_days(series, sig_date, 1)
        new_p1w = float(p1w) if p1w is not None else find_price_after_days(series, sig_date, 5)
        new_p1m = float(p1m) if p1m is not None else find_price_after_days(series, sig_date, 21)
        
        perf1d = calc_perf(entry_price, new_p1d) if new_p1d else None
        perf1w = calc_perf(entry_price, new_p1w) if new_p1w else None
        perf1m = calc_perf(entry_price, new_p1m) if new_p1m else None
        
        # Only issue an update if we successfully derived new prices
        if new_p1d != p1d or new_p1w != p1w or new_p1m != p1m:
            cur.execute(UPDATE_QUERY, (
                new_p1d, perf1d,
                new_p1w, perf1w,
                new_p1m, perf1m,
                req_id
            ))
            updates_made += 1

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"🏁 Performance Tracking completed. Updated {updates_made} records.")

if __name__ == "__main__":
    run_performance_tracker()
