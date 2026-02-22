
def hard_filters(data):
    """
    Applies strict filtering criteria to potential candidates.
    Returns True if the stock meets all tradeability requirements.
    """
    try:
        # Trend Condition: Counter-trend or reversal setup (SMA50 < SMA200)
        if not (data['sma50'] < data['sma200']):
            return False
            
        # Breakout Condition: Price must be above SMA50
        if not (data['fiyat'] > data['sma50']):
            return False

        # Volume Condition: Ensure minimum liquidity (relaxed to catch quiet breakouts)
        if data['hacim_orani'] <= 0.8:
            return False
            
        # Momentum Condition: Positive MACD and healthy RSI range
        if data['macd_hist'] <= 0: return False 
        if not (35 <= data['rsi'] <= 70): return False 

        return True
    except Exception as e:
        print(f"Error in hard_filters: {e}")
        return False

def calculate_category_scores(data):
    """
    Calculates scores for individual categories: Volume, Momentum, and Breakout.
    """
    scores = {
        'volume': 0,
        'momentum': 0,
        'breakout': 0
    }
    
    # Helper for safe key access
    def get(key, default=0):
        return data.get(key, default)

    # Volume Scoring
    hacim_orani = data['hacim_orani']
    
    if hacim_orani > 2.0:
        scores['volume'] += 40 
    elif hacim_orani > 1.5:
        scores['volume'] += 30 
    elif hacim_orani > 1.2:
        scores['volume'] += 20 
        
    # Bonus: Increasing Volume
    if hacim_orani > get('hacim_onceki'):
        if scores['volume'] < 40:
            scores['volume'] = min(40, scores['volume'] + 5)

    # Momentum Scoring
    rsi = data['rsi']
    macd_hist = data['macd_hist']
    
    if rsi > get('rsi_onceki'):
        scores['momentum'] += 15
        
    if macd_hist > get('macd_hist_onceki'):
        scores['momentum'] += 15
        
    # Bonus: Positive MACD Line
    if data['macd_line'] > 0.1:
        scores['momentum'] += 10
        
    # Breakout Quality Scoring
    fiyat = data['fiyat']
    sma50 = data['sma50']
    
    # Calculate distance from SMA50
    pct_above = (fiyat - sma50) / sma50
    if 0.01 <= pct_above <= 0.05:
        scores['breakout'] += 20
    elif pct_above > 0.05:
        scores['breakout'] += 10 
    else:
        scores['breakout'] += 10 
        
    return scores

def calculate_total_score(data):
    """
    Aggregates category scores into a total score (capped at 100).
    """
    category_scores = calculate_category_scores(data)
    total_score = sum(category_scores.values())
    
    total_score = min(100, total_score)
    
    return total_score, category_scores

def generate_signal(total_score):
    """
    Determines the trading signal based on the total score.
    """
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
    Calculates dynamic stop-loss and profit target levels based on ATR.
    """
    if atr <= 0:
        atr = fiyat * 0.03 
        
    # Stop-Loss: 2.0 ATR
    stop_distance = 2.0 * atr
    stop_price = fiyat - stop_distance
    stop_price = max(0.01, stop_price)
            
    # Target: 3.0 Risk Reward Ratio
    risk = fiyat - stop_price
    multiplier = 3.0
    
    target_price = fiyat + (risk * multiplier)
    
    return round(stop_price, 2), round(target_price, 2)

def evaluate_stock(data):
    """
    Main execution function for the Scout strategy.
    """
    # Apply Hard Filters
    if not hard_filters(data):
        return 'NO_TRADE', 0, 0, 0
        
    # Calculate Scores
    total_score, category_scores = calculate_total_score(data)
    
    # Generate Signal
    signal = generate_signal(total_score)
    
    # Calculate Risk Levels
    stop_price, target_price = calculate_stop_and_target(
        data['fiyat'], 
        data.get('atr', 0)
    )
    
    return signal, total_score, stop_price, target_price
