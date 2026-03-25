from tvDatafeed import TvDatafeed, Interval
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

# Initialize Data Providers
print("🔗 Connecting to data providers...")

try:
    tv = TvDatafeed()
    print("✅ Connection successful.")
except Exception as e:
    print(f"⚠️ Initial connection error ({e}), retrying...")
    time.sleep(3)
    tv = TvDatafeed()


def analyze_volume(df):
    """Returns the current bar's volume ratio vs the 20-period average."""
    try:
        vol_sma = df['Volume'].rolling(window=20).mean()
        current_vol = df['Volume'].iloc[-1]
        avg_vol = vol_sma.iloc[-1]
        if avg_vol == 0 or pd.isna(avg_vol):
            return 0.0
        return float(current_vol / avg_vol)
    except Exception as e:
        print(f"⚠️ Volume analysis error: {e}")
        return 0.0


def safe_float(val):
    """Safely converts a value to float, returning 0.0 on NaN or None."""
    if pd.isna(val) or val is None:
        return 0.0
    return float(val)


def fetch_tv_with_retry(symbol, retries=3):
    """Fetches daily OHLCV data from TradingView with retry logic."""
    for i in range(retries):
        try:
            df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_daily, n_bars=5000)
            return df
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                wait_time = (i + 1) * 5
                print(f"⚠️ Rate limit (429) — waiting {wait_time}s for {symbol}...")
                time.sleep(wait_time)
            else:
                print(f"❌ Data fetch error ({symbol}): {e}")
                return None
    return None


def fetch_and_calculate(symbol):
    """
    Fetches OHLCV data and calculates all technical indicators for a given stock symbol.
    Returns a tuple of (price, sma50, sma200, pe_ratio, pb_ratio, rsi, macd_line,
    macd_signal, macd_hist, adx, dmp, dmn, volume_ratio, swing_high, swing_low,
    macd_hist_prev, volume_prev, sma50_prev, rsi_prev, price_prev, adx_prev, atr, df)
    or None on failure.
    """
    try:
        symbol = symbol.upper().strip()
        tv_symbol = symbol.replace(".IS", "")

        yf_symbol = symbol if ".IS" in symbol else symbol + ".IS"

        df = fetch_tv_with_retry(tv_symbol)
        if df is None or df.empty:
            return None

        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low',
                            'close': 'Close', 'volume': 'Volume'}, inplace=True)

        if len(df) < 200:
            return None

        current_price = df['Close'].iloc[-1]

        pe_ratio = 0.0
        pb_ratio = 0.0

        # Fetch fundamental data from Yahoo Finance with retry
        for _ in range(3):
            try:
                info = yf.Ticker(yf_symbol).info
                if info:
                    pe_ratio = safe_float(info.get('trailingPE', 0))
                    pb_ratio = safe_float(info.get('priceToBook', 0))
                    break
            except Exception as e:
                print(f"⚠️ Yahoo Finance retry ({e})")
                time.sleep(1)
                continue

        # Calculate Technical Indicators
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.atr(length=14, append=True)

        vol_sma_20 = df['Volume'].rolling(window=20).mean()

        return (
            safe_float(current_price),
            safe_float(df['SMA_50'].iloc[-1]),
            safe_float(df['SMA_200'].iloc[-1]),
            pe_ratio,
            pb_ratio,
            safe_float(df['RSI_14'].iloc[-1]),
            safe_float(df['MACD_12_26_9'].iloc[-1]),
            safe_float(df['MACDs_12_26_9'].iloc[-1]),
            safe_float(df['MACDh_12_26_9'].iloc[-1]),
            safe_float(df['ADX_14'].iloc[-1]),
            safe_float(df['DMP_14'].iloc[-1]),
            safe_float(df['DMN_14'].iloc[-1]),
            analyze_volume(df),
            safe_float(df['High'].rolling(20).max().iloc[-1]),   # swing high
            safe_float(df['Low'].rolling(20).min().iloc[-1]),    # swing low
            safe_float(df['MACDh_12_26_9'].iloc[-2]),            # macd_hist_prev
            safe_float(df['Volume'].iloc[-2] / vol_sma_20.iloc[-2]) if vol_sma_20.iloc[-2] > 0 else 0.0,  # volume_prev ratio
            safe_float(df['SMA_50'].iloc[-2]),                   # sma50_prev
            safe_float(df['RSI_14'].iloc[-2]),                   # rsi_prev
            safe_float(df['Close'].iloc[-2]),                    # price_prev
            safe_float(df['ADX_14'].iloc[-2]),                   # adx_prev
            safe_float(df['ATRr_14'].iloc[-1]),                  # atr
            df
        )

    except Exception as e:
        print(f"❌ General error ({symbol}): {e}")
        return None


def get_market_index():
    """
    Fetches XU100 (BIST 100) data for Market Regime Analysis.
    Returns a DataFrame or None if unavailable.
    """
    try:
        for sym in ["XU100", "BIST100", "BIS100"]:
            df = tv.get_hist(symbol=sym, exchange='BIST', interval=Interval.in_daily, n_bars=300)
            if df is not None and not df.empty:
                df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low',
                                   'close': 'Close', 'volume': 'Volume'}, inplace=True)
                return df
        print("⚠️ Could not fetch Market Index (XU100). Defaulting to Sideways regime.")
        return None
    except Exception as e:
        print(f"❌ Error fetching Market Index: {e}")
        return None


if __name__ == "__main__":
    print(fetch_and_calculate("HEKTS"))