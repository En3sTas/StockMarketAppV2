
def hard_filters(data):
    """
    Layer 1: Hard Filters (Must Pass)
    Returns True if stock is tradeable
    
    SCOUT STRATEGY:
    - SMA50 < SMA200 (Bear Market / Recovery Phase)
    - Price > SMA50 (Breakout from medium-term average)
    - Volume > 1.2 (Strong buying interest)
    - MACD > 0 (Momentum shifted positive)
    - RSI [40-65] (Not overbought, room to run)
    """
    try:
        # 1. Trend Condition: SMA50 < SMA200 (Counter-Trend / Reversal)
        if not (data['sma50'] < data['sma200']):
            return False
            
        # 2. Breakout Condition: Price must be above SMA50
        if not (data['fiyat'] > data['sma50']):
            return False

        # 3. Minimum Liquidity / Volume Confirmation
        # "Hacimsiz yükselişler elenmeli"
        if data['hacim_orani'] <= 1.2:
            return False
            
        # 4. Momentum Base Requirements
        if data['macd_hist'] <= 0: return False # MACD Positive
        if not (40 <= data['rsi'] <= 65): return False # RSI Range [40-65]

        return True
    except Exception as e:
        print(f"Error in hard_filters: {e}")
        return False

# --- SCORING FUNCTIONS ---

def calculate_category_scores(data):
    """
    Returns individual category scores for SCOUT strategy.
    
    Weights:
    - Trend: 0% (Not focused on trend strength)
    - Volume: 40%
    - Momentum: 40%
    - Breakout Quality: 20%
    """
    scores = {
        'volume': 0,
        'momentum': 0,
        'breakout': 0
    }
    
    # Helper for safe access
    def get(key, default=0):
        return data.get(key, default)

    # 1. VOLUME (40 Points Max)
    hacim_orani = data['hacim_orani']
    
    if hacim_orani > 2.0:
        scores['volume'] += 40 # Perfect
    elif hacim_orani > 1.5:
        scores['volume'] += 30 # Great
    elif hacim_orani > 1.2:
        scores['volume'] += 20 # Good
        
    # Bonus for volume increase
    if hacim_orani > get('hacim_onceki'):
        if scores['volume'] < 40:
            scores['volume'] = min(40, scores['volume'] + 5)

    # 2. MOMENTUM (40 Points Max)
    # MACD/RSI Increase vs Previous Day
    rsi = data['rsi']
    macd_hist = data['macd_hist']
    
    if rsi > get('rsi_onceki'):
        scores['momentum'] += 15
        
    if macd_hist > get('macd_hist_onceki'):
        scores['momentum'] += 15
        
    # MACD Line is positive (Already checked in hard filter, but reward magnitude)
    if data['macd_line'] > 0.1:
        scores['momentum'] += 10
        
    # 3. BREAKOUT QUALITY (20 Points Max)
    fiyat = data['fiyat']
    sma50 = data['sma50']
    
    # Distance from SMA50 (Close is better, usually. But we want clear breakout)
    # If price is > 1% above SMA50 but less than 5% (Healthy breakout, not extended)
    pct_above = (fiyat - sma50) / sma50
    if 0.01 <= pct_above <= 0.05:
        scores['breakout'] += 20
    elif pct_above > 0.05:
        scores['breakout'] += 10 # A bit extended
    else:
        scores['breakout'] += 10 # Just barely above
        
    return scores

def calculate_total_score(data):
    """
    Calculates total score.
    Returns: (total_score, category_scores_dict)
    """
    category_scores = calculate_category_scores(data)
    total_score = sum(category_scores.values())
    
    # Cap at 100 purely theoretical
    total_score = min(100, total_score)
    
    return total_score, category_scores

# --- DECISION ENGINE ---

def generate_signal(total_score):
    if total_score >= 80:
        return 'STRONG_BUY'
    elif total_score >= 60:
        return 'BUY'
    elif total_score >= 50:
        return 'WATCH'
    else:
        return 'NO_TRADE'

def calculate_stop_and_target(fiyat, atr):
    """
    Scout Strategy Risk Management:
    Stop: 2.0 * ATR (Tighter stop for reversals)
    Target: Risk * 3.0 (Wider target for catching the bottom)
    """
    if atr <= 0:
        atr = fiyat * 0.03 
        
    stop_distance = 2.0 * atr
    stop_price = fiyat - stop_distance
    stop_price = max(0.01, stop_price)
            
    risk = fiyat - stop_price
    multiplier = 3.0
    
    target_price = fiyat + (risk * multiplier)
    
    return round(stop_price, 2), round(target_price, 2)

def evaluate_stock(data):
    """
    Main entry point for scout engine
    Returns: (signal, score, stop_price, target_price)
    """
    # 1. Hard Filters
    if not hard_filters(data):
        return 'NO_TRADE', 0, 0, 0
        
    # 2. Scoring
    total_score, category_scores = calculate_total_score(data)
    
    # 3. Decision
    signal = generate_signal(total_score)
    
    # 4. Stop/Target
    stop_price, target_price = calculate_stop_and_target(
        data['fiyat'], 
        data.get('atr', 0)
    )
    
    # DO NOT RESET TARGETS on NO_TRADE
    pass
        
    return signal, total_score, stop_price, target_price
