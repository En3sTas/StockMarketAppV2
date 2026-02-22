import pandas as pd
import numpy as np

def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_vwma(close, volume, length=20):
    cv = close * volume
    return cv.rolling(window=length).sum() / volume.rolling(window=length).sum()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_mfi(high, low, close, volume, period=14):
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    
    positive_flow = []
    negative_flow = []
    
    # Identify positive and negative money flow
    tp_shift = typical_price.shift(1)
    
    pos_flow = pd.Series(0.0, index=typical_price.index)
    neg_flow = pd.Series(0.0, index=typical_price.index)
    
    pos_mask = typical_price > tp_shift
    neg_mask = typical_price < tp_shift
    
    pos_flow[pos_mask] = raw_money_flow[pos_mask]
    neg_flow[neg_mask] = raw_money_flow[neg_mask]
    
    # Calculate Money Flow Ratio and Index
    positive_mf = pos_flow.rolling(window=period).sum()
    negative_mf = neg_flow.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
    return mfi

def calculate_bollinger_width(close, period=20, std_dev=2):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    # Calculate Bollinger Band Width
    bandwidth = (upper - lower) / sma
    return bandwidth, upper, lower

def calculate_pivots(high, low, close):
    # Calculate Standard Pivot Points based on previous day
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)
    
    pivot = (prev_high + prev_low + prev_close) / 3
    r1 = (2 * pivot) - prev_low
    s1 = (2 * pivot) - prev_high
    s2 = pivot - (prev_high - prev_low)
    
    return pivot, r1, s1, s2

def get_market_regime(index_df):
    """
    Determines Market Regime based on XU100 Index.
    """
    if index_df is None or index_df.empty:
        return "SIDEWAYS", 1.0 
        
    # Compare current price to SMA200
    close = index_df['Close']
    sma200 = close.rolling(window=200).mean().iloc[-1]
    current_price = close.iloc[-1]
    
    if current_price < sma200:
        return "BEAR", 0.8 
    elif current_price > sma200 * 1.05: 
        return "BULL", 1.0
    else:
        return "SIDEWAYS", 0.9

def evaluate_stock(df, index_df=None):
    """
    Institutional Grade Analysis
    """
    if df is None or len(df) < 200:
        return None
        
    current = df.iloc[-1]
    
    # Determine Market Regime
    regime, regime_multiplier = get_market_regime(index_df)
    
    # Calculate moving averages
    ema20 = calculate_ema(df['Close'], 20).iloc[-1]
    ema50 = calculate_ema(df['Close'], 50).iloc[-1]
    ema100 = calculate_ema(df['Close'], 100).iloc[-1]
    ema200 = calculate_ema(df['Close'], 200).iloc[-1]
    
    # Calculate MFI (once, reuse series later)
    mfi_series = calculate_mfi(df['High'], df['Low'], df['Close'], df['Volume'])
    mfi = mfi_series.iloc[-1]
    
    # Calculate Bollinger Bands
    bb_width, bb_upper, bb_lower = calculate_bollinger_width(df['Close'])
    bb_width = bb_width.iloc[-1]
    
    # Calculate Pivots
    pivot, r1, s1, s2 = calculate_pivots(df['High'], df['Low'], df['Close'])
    pivot = pivot.iloc[-1]
    s2 = s2.iloc[-1]
    
    # Helper to retrieve values safely
    def get_val(row, candidates, default):
        for key in candidates:
            if key in row.index:
                return row[key]
        return default

    # Retrieve ADX and RSI
    adx = get_val(current, ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)
    rsi = get_val(current, ['RSI_14', 'rsi_14', 'RSI', 'rsi'], 50) 
    
    # Initialize Scoring
    tags = []
    main_strategy = "NEUTRAL"
    score = 0 
    
    price = current['Close']
    
    # Strategy: Trend Following
    is_trend = False
    if price > ema20 and ema20 > ema50:
        is_trend = True
        if adx > 25:
            # Fix 5: Check if ADX is declining (trend losing energy)
            adx_prev = get_val(df.iloc[-2], ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)
            if adx_prev > adx:  # ADX falling
                tags.append("Tiring Trend")
                score += 5
            else:
                tags.append("Strong Trend")
                score += 15
            main_strategy = "TREND"
        else:
            tags.append("Weak Trend")
            score += 5
            
    if ema50 > ema200: 
        tags.append("Long-Term Bull")
        score += 10 
        
    # Strategy: VWMA Check
    vwma20 = calculate_vwma(df['Close'], df['Volume'], 20).iloc[-1]
    
    if price > vwma20:
        tags.append("Above VWMA")
        score += 10 
    
    # Fix 3: True Volume Divergence — price making highs but volume/MFI declining
    high_5 = df['Close'].rolling(5).max()
    if len(high_5) >= 2:
        price_making_highs = current['Close'] >= high_5.iloc[-2]
        vol_declining = current['Volume'] < df['Volume'].rolling(5).mean().iloc[-2]
        mfi_declining = mfi_series.iloc[-1] < mfi_series.iloc[-2]
        if price_making_highs and (vol_declining or mfi_declining):
            tags.append("Vol Divergence")
            score -= 5
    
    # Fix 1: Whale Volume — check candle color
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    if current['Volume'] > avg_vol * 2.0:
        if current['Close'] > current['Open']:  # Green candle
            tags.append("Whale Volume")
            score += 10
        else:  # Red candle — high sell volume
            tags.append("High Sell Vol")
            score -= 10
        if main_strategy == "NEUTRAL": main_strategy = "BREAKOUT"
        
    if bb_width < 0.10:
        tags.append("BB Squeeze")
        score += 10 
    
    if mfi > 60:
        tags.append("Smart Money In")
        score += 5 
    
    # Fix 4: Overbought warning tags
    if rsi > 75:
        tags.append("Overbought")  # Warning only, no score change
    
    if mfi > 80:
        tags.append("MFI Overbought")  # Smart money saturated, selling may come
        
    # Fix 2: Mean Reversion / Reversal — RSI Hook AND Support required
    rsi_prev = calculate_rsi(df['Close']).iloc[-2]
    rsi_hooked = rsi < 30 and rsi > rsi_prev  # RSI turning upward
    near_support = price < s2  # Below Pivot S2
    
    if rsi_hooked and near_support:  # Both conditions required
        if regime != "BEAR": 
            tags.append("Oversold")
            tags.append("Support Area")
            main_strategy = "REVERSAL"
            score += 15 
            
            if is_trend:
                tags.append("Trend Pullback")
                score += 5 
        else:
            tags.append("Falling Knife")
            score -= 20
    elif rsi_hooked:  # RSI hook alone — weaker signal
        tags.append("RSI Reversal")
        score += 5
    elif near_support and regime == "BEAR":
        tags.append("Falling Knife")
        score -= 20
            
    # Apply Market Regime Penalty
    if regime == "BEAR":
        score = score * 0.6 
        tags.append("Bear Regime Risk")
        
    score = max(0, min(100, int(score)))
    
    return {
        "score": score,
        "main_strategy": main_strategy,
        "market_regime": regime,
        "tags": tags,
        "confidence_score": score 
    }


