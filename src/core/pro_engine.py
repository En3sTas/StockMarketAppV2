import pandas as pd
import numpy as np


def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def calculate_vwma(close, volume, length=20):
    cv = close * volume
    return cv.rolling(window=length).sum() / volume.rolling(window=length).sum()


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain  = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_mfi(high, low, close, volume, period=14):
    typical_price   = (high + low + close) / 3
    raw_money_flow  = typical_price * volume

    tp_shift = typical_price.shift(1)

    pos_flow = pd.Series(0.0, index=typical_price.index)
    neg_flow = pd.Series(0.0, index=typical_price.index)

    pos_mask = typical_price > tp_shift
    neg_mask = typical_price < tp_shift

    pos_flow[pos_mask] = raw_money_flow[pos_mask]
    neg_flow[neg_mask] = raw_money_flow[neg_mask]

    # Money Flow Ratio and Index
    positive_mf = pos_flow.rolling(window=period).sum()
    negative_mf = neg_flow.rolling(window=period).sum()

    mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
    return mfi


def calculate_bollinger_width(close, period=20, std_dev=2):
    sma       = close.rolling(window=period).mean()
    std       = close.rolling(window=period).std()
    upper     = sma + (std * std_dev)
    lower     = sma - (std * std_dev)
    bandwidth = (upper - lower) / sma
    return bandwidth, upper, lower


def calculate_pivots(high, low, close):
    """Standard Pivot Points based on previous day."""
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)
    prev_close = close.shift(1)

    pivot = (prev_high + prev_low + prev_close) / 3
    r1    = (2 * pivot) - prev_low
    s1    = (2 * pivot) - prev_high
    s2    = pivot - (prev_high - prev_low)

    return pivot, r1, s1, s2


def get_market_regime(index_df):
    """Determines Market Regime based on XU100 Index."""
    if index_df is None or index_df.empty:
        return "SIDEWAYS", 1.0

    close         = index_df['Close']
    sma200        = close.rolling(window=200).mean().iloc[-1]
    current_price = close.iloc[-1]

    if current_price < sma200:
        return "BEAR", 0.8
    elif current_price > sma200 * 1.05:
        return "BULL", 1.0
    else:
        return "SIDEWAYS", 0.9


def evaluate_stock(df, index_df=None):
    """
    Institutional Grade Analysis — Advanced Scoring Engine V4
    Max Score: 100 | Base Score: 50
    """
    if df is None or len(df) < 200:
        return None

    current = df.iloc[-1]
    prev    = df.iloc[-2]

    # --- 1. DATA PREPARATION & INDICATORS ---

    def get_val(row, candidates, default):
        """Safely retrieves a value by trying multiple column name candidates."""
        for key in candidates:
            if key in row.index:
                return row[key]
        return default

    # Price & Changes
    price      = current['Close']
    close_prev = prev['Close']

    # Market Regime (XU100)
    regime, regime_multiplier = get_market_regime(index_df)  # BULL, BEAR, SIDEWAYS

    # Moving Averages
    ema20  = calculate_ema(df['Close'], 20).iloc[-1]
    ema50  = calculate_ema(df['Close'], 50).iloc[-1]
    ema200 = calculate_ema(df['Close'], 200).iloc[-1]
    vwma20 = calculate_vwma(df['Close'], df['Volume'], 20).iloc[-1]

    # Indicators
    adx      = get_val(current, ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)
    adx_prev = get_val(prev,    ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)

    rsi      = get_val(current, ['RSI_14', 'rsi_14', 'RSI', 'rsi'], 50)
    rsi_prev = get_val(prev,    ['RSI_14', 'rsi_14', 'RSI', 'rsi'], 50)

    mfi_series = calculate_mfi(df['High'], df['Low'], df['Close'], df['Volume'])
    mfi        = mfi_series.iloc[-1]

    # Pivots & Bollinger
    pivot, r1, s1, s2 = calculate_pivots(df['High'], df['Low'], df['Close'])
    pivot, s2 = pivot.iloc[-1], s2.iloc[-1]

    bb_width, bb_upper, bb_lower = calculate_bollinger_width(df['Close'])
    bb_width = bb_width.iloc[-1]

    # --- 2. SCORING ENGINE ---

    tags          = []
    main_strategy = "NEUTRAL"
    score         = 50   # Base score (neutral starting point)

    # --- A) CRASH SHIELD — Priority Check ---
    # If the stock is crashing, skip full analysis, drop score and exit quickly.

    daily_change = (price - close_prev) / close_prev
    try:
        price_3d_ago    = df['Close'].iloc[-4]
        three_day_change = (price - price_3d_ago) / price_3d_ago
    except Exception:
        three_day_change = 0

    if daily_change < -0.035 or three_day_change < -0.05:
        tags.append("Correction ⚠️")
        score = 20
        if regime == "BEAR":
            tags.append("Bear Regime Risk")
            score -= 10
        return {
            "score":            int(score),
            "main_strategy":    "NEUTRAL",
            "market_regime":    regime,
            "tags":             tags,
            "confidence_score": int(score)
        }

    # --- B) TREND ANALYSIS (Max +30 pts) ---
    is_trend = False

    # 1. Short-term trend (EMA20 > EMA50)
    if price > ema20 and ema20 > ema50:
        is_trend = True
        tags.append("Strong Trend")
        score += 10
    elif price > ema50:   # Weak but intact trend
        tags.append("Weak Trend")
        score += 5

    # 2. Long-term trend (Golden Zone)
    if ema50 > ema200:
        tags.append("Long-Term Bull")
        score += 10

    # 3. Trend Strength (ADX)
    if adx > 25:
        if adx > adx_prev:   # ADX rising → strengthening trend
            if main_strategy == "NEUTRAL": main_strategy = "TREND"
        else:                 # ADX falling → tiring trend
            tags.append("Tiring Trend")
            score -= 5

    # --- C) VOLUME & FUEL (Max +20 pts) ---

    # 1. VWMA Check
    if price > vwma20:
        tags.append("Above VWMA")
        score += 5

    # 2. Smart Money (MFI)
    if mfi > 60:
        tags.append("Smart Money In")
        score += 5

    # 3. Whale Volume (color-controlled)
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    if current['Volume'] > avg_vol * 2.0:
        if price > current['Open']:   # Green candle
            tags.append("Whale Volume")
            score += 10
            if main_strategy == "NEUTRAL": main_strategy = "BREAKOUT"
        else:                          # Red candle (distribution)
            tags.append("High Sell Vol")
            score -= 15

    # --- D) SETUPS / TRIGGERS (Max +25 pts) ---

    # Scenario 1: REVERSAL (Bottom Bounce)
    rsi_hook    = rsi < 35 and rsi > rsi_prev   # RSI below 35 and turning up
    near_support = price < s2 * 1.02             # Near support zone (+2% tolerance)

    if rsi_hook and near_support:
        tags.append("Oversold Hook 🎣")
        tags.append("Support Area")
        score += 20
        main_strategy = "REVERSAL"
        if is_trend:
            tags.append("Trend Pullback")   # Pullback within a trend (most valuable)
            score += 5

    # Scenario 2: BREAKOUT (BB Squeeze)
    elif bb_width < 0.10:
        tags.append("BB Squeeze")
        score += 10
        if price > calculate_bollinger_width(df['Close'])[1].iloc[-1]:   # Upper band break
            tags.append("Bollinger Breakout")
            score += 10
            main_strategy = "BREAKOUT"

    # --- E) RISKS & PENALTIES ---

    # 1. Divergence (price at highs, volume/MFI declining)
    high_5 = df['Close'].rolling(5).max()
    if len(high_5) > 5:
        making_new_highs = price >= high_5.iloc[-2]
        vol_dropping     = current['Volume'] < avg_vol
        if making_new_highs and vol_dropping:
            tags.append("Vol Divergence")
            score -= 10

    # 2. Overheating (Profit-taking signal)
    if rsi > 75:
        tags.append("Overbought ⚠️")
        score -= 5

    if mfi > 85:
        tags.append("MFI Overbought")

    # 3. Bear Market Penalty
    if regime == "BEAR":
        tags.append("Bear Regime Risk")
        score -= 15

    # --- F) FINAL CHECKS ---

    # Clamp score to [0, 100]
    score = max(0, min(100, int(score)))

    return {
        "score":            score,
        "main_strategy":    main_strategy,
        "market_regime":    regime,
        "tags":             tags,
        "confidence_score": score
    }
