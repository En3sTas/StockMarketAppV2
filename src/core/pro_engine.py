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
    Institutional Grade Analysis - Advanced Scoring Engine V4
    Max Score: 100 | Base Score: 50
    """
    if df is None or len(df) < 200:
        return None
        
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- 1. VERİ HAZIRLIĞI & İNDİKATÖRLER ---
    
    # Helper to retrieve values safely
    def get_val(row, candidates, default):
        for key in candidates:
            if key in row.index:
                return row[key]
        return default

    # Fiyat ve Değişimler
    price = current['Close']
    close_prev = prev['Close']
    
    # Piyasa Rejimi (XU100)
    regime, regime_multiplier = get_market_regime(index_df) # BULL, BEAR, SIDEWAYS
    
    # Hareketli Ortalamalar
    ema20 = calculate_ema(df['Close'], 20).iloc[-1]
    ema50 = calculate_ema(df['Close'], 50).iloc[-1]
    ema200 = calculate_ema(df['Close'], 200).iloc[-1]
    vwma20 = calculate_vwma(df['Close'], df['Volume'], 20).iloc[-1]
    
    # İndikatörler
    adx = get_val(current, ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)
    adx_prev = get_val(prev, ['ADX_14', 'adx_14', 'ADX', 'adx'], 0)
    
    rsi = get_val(current, ['RSI_14', 'rsi_14', 'RSI', 'rsi'], 50)
    rsi_prev = get_val(prev, ['RSI_14', 'rsi_14', 'RSI', 'rsi'], 50)
    
    mfi_series = calculate_mfi(df['High'], df['Low'], df['Close'], df['Volume'])
    mfi = mfi_series.iloc[-1]
    
    # Pivotlar & Bollinger
    pivot, r1, s1, s2 = calculate_pivots(df['High'], df['Low'], df['Close'])
    pivot, s2 = pivot.iloc[-1], s2.iloc[-1]
    
    bb_width, bb_upper, bb_lower = calculate_bollinger_width(df['Close'])
    bb_width = bb_width.iloc[-1]

    # --- 2. PUANLAMA MOTORU BAŞLANGICI ---
    
    tags = []
    main_strategy = "NEUTRAL"
    score = 50  # BASE SCORE (Nötr Başlangıç)

    # --- A) CRASH SHIELD (Çöküş Kalkanı) - ÖNCELİKLİ KONTROL ---
    # Eğer hisse çakılıyorsa analiz yapma, puanı ez ve çık.
    
    daily_change = (price - close_prev) / close_prev
    try:
        price_3d_ago = df['Close'].iloc[-4]
        three_day_change = (price - price_3d_ago) / price_3d_ago
    except:
        three_day_change = 0

    is_crashing = False
    if daily_change < -0.035 or three_day_change < -0.05:
        is_crashing = True
        tags.append("Correction ⚠️")
        score = 20 # Direkt düşük puan
        # Crash varsa diğer puanları hesaplama, sadece riskleri ekle
        if regime == "BEAR":
            tags.append("Bear Regime Risk")
            score -= 10
        return {
            "score": int(score),
            "main_strategy": "NEUTRAL",
            "market_regime": regime,
            "tags": tags,
            "confidence_score": int(score)
        }

    # --- B) TREND ANALİZİ (Max +30 Puan) ---
    is_trend = False
    
    # 1. Kısa Vadeli Trend (EMA20 > EMA50)
    if price > ema20 and ema20 > ema50:
        is_trend = True
        tags.append("Strong Trend")
        score += 10
    elif price > ema50: # Trend zayıf ama bozulmamış
        tags.append("Weak Trend")
        score += 5
        
    # 2. Uzun Vadeli Trend (Golden Zone)
    if ema50 > ema200:
        tags.append("Long-Term Bull")
        score += 10
        
    # 3. Trend Gücü (ADX)
    if adx > 25:
        if adx > adx_prev: # ADX Artıyor
            # Trend puanına ekleme yapmıyoruz, zaten Strong Trend aldı.
            # Ama stratejiyi belirliyoruz.
            if main_strategy == "NEUTRAL": main_strategy = "TREND"
        else: # ADX Düşüyor (Yorgunluk)
            tags.append("Tiring Trend")
            score -= 5 # Trend olsa bile yorulduğu için ceza

    # --- C) HACİM & YAKIT (Max +20 Puan) ---
    
    # 1. VWMA Kontrolü
    if price > vwma20:
        tags.append("Above VWMA")
        score += 5
        
    # 2. Akıllı Para (MFI)
    if mfi > 60:
        tags.append("Smart Money In")
        score += 5
        
    # 3. Balina Hacmi (RENK KONTROLLÜ)
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    if current['Volume'] > avg_vol * 2.0:
        if price > current['Open']: # Yeşil Mum
            tags.append("Whale Volume")
            score += 10
            if main_strategy == "NEUTRAL": main_strategy = "BREAKOUT"
        else: # Kırmızı Mum (Dökme)
            tags.append("High Sell Vol")
            score -= 15 # Ciddi ceza

    # --- D) SETUP / TETİKLEYİCİLER (Max +25 Puan) ---
    
    # Senaryo 1: DİP DÖNÜŞÜ (Reversal)
    rsi_hook = rsi < 35 and rsi > rsi_prev # RSI 35 altı ve dönüyor
    near_support = price < s2 * 1.02 # Destek bölgesinde (+%2 tolerans)
    
    if rsi_hook and near_support:
        tags.append("Oversold Hook 🎣")
        tags.append("Support Area")
        score += 20 # Altın vuruş puanı
        main_strategy = "REVERSAL"
        if is_trend: 
            tags.append("Trend Pullback") # Trend içi düzeltme (En değerlisi)
            score += 5 
            
    # Senaryo 2: PATLAMA (Breakout)
    elif bb_width < 0.10:
        tags.append("BB Squeeze")
        score += 10
        if price > calculate_bollinger_width(df['Close'])[1].iloc[-1]: # Üst bandı kırdıysa
            tags.append("Bollinger Breakout")
            score += 10
            main_strategy = "BREAKOUT"

    # --- E) RİSK & CEZALAR ---
    
    # 1. Uyumsuzluk (Divergence)
    # Fiyat tepeleri yükselirken Hacim veya MFI düşüyorsa
    high_5 = df['Close'].rolling(5).max()
    if len(high_5) > 5:
        making_new_highs = price >= high_5.iloc[-2]
        vol_dropping = current['Volume'] < avg_vol
        if making_new_highs and vol_dropping:
            tags.append("Vol Divergence")
            score -= 10

    # 2. Aşırı Isınma (Kâr Alma Sinyali)
    if rsi > 75:
        tags.append("Overbought ⚠️")
        score -= 5 # Alım için riskli bölge
        
    if mfi > 85:
        tags.append("MFI Overbought")
        
    # 3. Piyasa Rejimi Cezası
    if regime == "BEAR":
        tags.append("Bear Regime Risk")
        score -= 15 # Sabit ceza (Çarpan yerine)
        
    # --- F) FİNAL KONTROLLER ---
    
    # Skor Limitleme (Clamp)
    score = max(0, min(100, int(score)))
    
    return {
        "score": score,
        "main_strategy": main_strategy,
        "market_regime": regime,
        "tags": tags,
        "confidence_score": score
    }


