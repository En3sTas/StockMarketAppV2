
def hard_filters(data):
    """
    Applies strict filtering criteria to potential candidates for Trend Strategy.
    Returns True if the stock meets all tradeability requirements.
    """
    try:
        # Trend Condition: Golden Cross zone (Price > SMA200 and SMA50 > SMA200)
        if not (data['fiyat'] > data['sma200'] and data['sma50'] > data['sma200']):
            return False
            
        # Liquidity Filter: Volume Ratio
        if data['hacim_orani'] < 0.5: 
            return False
            
        # Momentum Base Requirements
        if data['rsi'] <= 35: return False
        if data['macd_hist'] < 0: return False
        if data['adx'] <= 25: return False 

        # Directional Filter: Buyers must dominate sellers
        if data['dmp'] < data['dmn']:
            return False
        
        return True
    except Exception as e:
        print(f"Error in hard_filters: {e}")
        return False

# --- PENALTY FUNCTIONS ---

def check_rsi_penalty(rsi):
    # Penalty for overbought conditions
    if rsi > 80:
        return -20  
    elif rsi > 70:
        return -10  
    return 0

def check_volume_divergence(fiyat, fiyat_onceki, hacim_orani, hacim_onceki):
    # Detects bearish volume divergence (price up, volume down)
    price_rising = fiyat > fiyat_onceki
    volume_declining = hacim_orani < hacim_onceki
    
    if price_rising and volume_declining:
        return -10  
    return 0

def check_macd_momentum_loss(macd_hist, macd_hist_onceki):
    # Detects weakening momentum
    if macd_hist < macd_hist_onceki:
        return -8  
    return 0

def check_adx_weakness(adx, adx_onceki, fiyat, fiyat_onceki):
    # Detects weak or weakening trends
    penalty = 0
    
    # Choppy range
    if adx < 20 and abs(fiyat - fiyat_onceki) / (fiyat_onceki if fiyat_onceki else 1) < 0.01:
        penalty -= 5
    
    # Trend weakening
    if adx < adx_onceki and abs(fiyat - fiyat_onceki) / (fiyat_onceki if fiyat_onceki else 1) > 0.01:
        penalty -= 5
    
    return penalty

def check_sma50_divergence(fiyat, sma50, sma50_onceki):
    # Detects potential false breakouts (price > decreasing SMA50)
    if sma50_onceki == 0:
        return 0
    
    sma50_slope = (sma50 - sma50_onceki) / sma50_onceki
    price_above_sma50 = fiyat > sma50
    
    if price_above_sma50 and sma50_slope < -0.005:  
        return -10  
    return 0

def check_volume_spike_trap(hacim_orani, hacim_onceki):
    # Detects isolated volume spikes which might indicate manipulation
    if hacim_orani > 3.0 and hacim_onceki < 1.5:
        return -10  
    return 0

# --- SCORING FUNCTIONS ---

def calculate_category_scores(data):
    """
    Calculates scores for individual categories: Trend, Momentum, Volume, Durability.
    """
    scores = {
        'trend': 0,
        'momentum': 0,
        'volume': 0,
        'durability': 0
    }
    
    # Helper for safe key access
    def get(key, default=0):
        return data.get(key, default)

    fiyat = data['fiyat']
    sma50 = data['sma50']
    sma200 = data['sma200']
    
    # Trend Strength Scoring
    if fiyat > sma50:
        scores['trend'] += 10
    if sma50 > sma200:
        scores['trend'] += 10
    
    # Strong Separation from SMAs
    max_sma = max(sma50, sma200)
    if max_sma > 0:
        gap_pct = ((fiyat - max_sma) / max_sma)
        if fiyat > sma50 and fiyat > sma200 and gap_pct > 0.02:
            scores['trend'] += 15 
    
    # Momentum Scoring
    rsi = data['rsi']
    if 50 <= rsi <= 65:
        scores['momentum'] += 10
    if rsi > get('rsi_onceki'):
        scores['momentum'] += 10 
    if data['macd_hist'] > get('macd_hist_onceki'):
        scores['momentum'] += 5
    if data['macd_line'] > 0:
        scores['momentum'] += 5
    
    # Volume Scoring
    hacim_orani = data['hacim_orani']
    if hacim_orani > 1.2:
        scores['volume'] += 10
    if hacim_orani > get('hacim_onceki'):
        scores['volume'] += 5
    
    # Volume/Price Alignment
    price_up = fiyat > get('fiyat_onceki', fiyat)
    volume_up = hacim_orani > get('hacim_onceki', hacim_orani)
    if price_up == volume_up:
        scores['volume'] += 5
    
    # Trend Durability Scoring
    adx = data['adx']
    if 20 <= adx <= 30:
        scores['durability'] += 5
    if adx > get('adx_onceki'):
        scores['durability'] += 5
    if data['dmp'] > data['dmn']:
        scores['durability'] += 5
    
    return scores

def calculate_total_score(data):
    """
    Aggregates category scores and applies penalties to calculate total score.
    """
    category_scores = calculate_category_scores(data)
    base_score = sum(category_scores.values())
    
    def get(key, default=0):
        return data.get(key, default)
        
    penalties = 0
    penalties += check_rsi_penalty(data['rsi'])
    penalties += check_volume_divergence(
        data['fiyat'], 
        get('fiyat_onceki', data['fiyat']),
        data['hacim_orani'],
        get('hacim_onceki', data['hacim_orani'])
    )
    penalties += check_macd_momentum_loss(
        data['macd_hist'],
        get('macd_hist_onceki', data['macd_hist'])
    )
    penalties += check_adx_weakness(
        data['adx'],
        get('adx_onceki', data['adx']),
        data['fiyat'],
        get('fiyat_onceki', data['fiyat'])
    )
    
    penalties += check_sma50_divergence(
        data['fiyat'],
        data['sma50'],
        get('sma50_onceki', data['sma50'])
    )
    penalties += check_volume_spike_trap(
        data['hacim_orani'],
        get('hacim_onceki', data['hacim_orani'])
    )
    
    total_score = max(0, base_score + penalties)
    return total_score, category_scores

# --- DECISION ENGINE ---

def validate_strong_buy_categories(category_scores):
    """
    Validates if the stock meets the criteria for a STRONG_BUY signal.
    Requires at least 3 categories to pass 70% of their max score.
    """
    thresholds = {
        'trend': 24.5,      
        'momentum': 21,     
        'volume': 14,       
        'durability': 11    
    }
    
    categories_passed = sum(
        1 for category, score in category_scores.items()
        if score >= thresholds.get(category, 999)
    )
    
    return categories_passed >= 3

def generate_signal(total_score, category_scores):
    """
    Determines the trading signal based on score and category validation.
    """
    if total_score >= 80: 
        if validate_strong_buy_categories(category_scores):
            return 'STRONG_BUY'
        else:
            return 'BUY'
    elif total_score >= 70: 
        return 'BUY'
    elif total_score >= 60:
        return 'WATCH' 
    else:
        return 'NO_TRADE'

def calculate_stop_and_target(fiyat, atr, rsi, adx):
    """
    Calculates dynamic stop-loss and profit target levels using ATR.
    Adjusts targets based on trend strength (ADX) and overbought status (RSI).
    """
    if atr <= 0:
        atr = fiyat * 0.03 
        
    # Stop-Loss: 3.0 ATR (Trailing Stop logic)
    stop_distance = 3.0 * atr 
    stop_price = fiyat - stop_distance
    stop_price = max(0.01, stop_price)
    
    # Target: Dynamic Risk/Reward
    base_multiplier = 4.0 
    
    # Boost target if trend is strong (ADX)
    if adx > 30: base_multiplier += 2.0
    elif adx > 25: base_multiplier += 1.0
    
    # Reduce target if overbought (RSI)
    if rsi > 75: base_multiplier -= 2.0
    elif rsi > 70: base_multiplier -= 1.0
    
    # Minimum 2x ATR profit target
    final_multiplier = max(2.0, base_multiplier)
    
    target_distance = final_multiplier * atr
    target_price = fiyat + target_distance
    
    return round(stop_price, 2), round(target_price, 2)

def evaluate_stock(data):
    """
    Main execution function for the Trend strategy.
    """
    # Apply Hard Filters
    if not hard_filters(data):
        return 'NO_TRADE', 0, 0, 0
        
    # Calculate Scores & Penalties
    total_score, category_scores = calculate_total_score(data)
    
    # Generate Signal
    signal = generate_signal(total_score, category_scores)
    
    # Calculate Risk Levels
    stop_price, target_price = calculate_stop_and_target(
        data['fiyat'], 
        data.get('atr', 0),
        data['rsi'],
        data['adx']
    )
    
    return signal, total_score, stop_price, target_price
