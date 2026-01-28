
def hard_filters(data):
    """
    Layer 1: Hard Filters (Must Pass)
    Returns True if stock is tradeable
    
    TREND STRATEGY:
    - SMA50 > SMA200 (Golden Cross zone)
    - ADX > 25 (Strong Trend)
    - Momentum positive
    """
    try:
        # 1. Trend Filter: Price > SMA200 and SMA50 > SMA200 (Golden Cross zone)
        if not (data['fiyat'] > data['sma200'] and data['sma50'] > data['sma200']):
            return False
            
        # 2. Minimum Liquidity (using volume ratio as proxy since absolute vol varies)
        if data['hacim_orani'] < 0.5: # Extremely low volume relative to avg
            return False
            
        # 3. Momentum Base Requirements
        if data['rsi'] <= 35: return False
        if data['macd_hist'] < 0: return False
        if data['adx'] <= 25: return False # Stricter Trend Filter (Was 20)

        # 4. Directional Filter (NEW: Hard Reject if Sellers > Buyers)
        if data['dmp'] < data['dmn']:
            return False
        
        return True
    except Exception as e:
        print(f"Error in hard_filters: {e}")
        return False

# --- PENALTY FUNCTIONS ---

def check_rsi_penalty(rsi):
    """Returns penalty points for overbought RSI conditions"""
    if rsi > 80:
        return -20  # Extreme overbought
    elif rsi > 70:
        return -10  # Severely overheated
    return 0

def check_volume_divergence(fiyat, fiyat_onceki, hacim_orani, hacim_onceki):
    """Detects bearish volume divergence"""
    price_rising = fiyat > fiyat_onceki
    volume_declining = hacim_orani < hacim_onceki
    
    if price_rising and volume_declining:
        return -10  # Weak rally, likely to fail
    return 0

def check_macd_momentum_loss(macd_hist, macd_hist_onceki):
    """Detects weakening momentum"""
    if macd_hist < macd_hist_onceki:
        return -8  # Losing steam
    return 0

def check_adx_weakness(adx, adx_onceki, fiyat, fiyat_onceki):
    """Detects weak or weakening trends"""
    penalty = 0
    
    # No trend in choppy range
    if adx < 20 and abs(fiyat - fiyat_onceki) / (fiyat_onceki if fiyat_onceki else 1) < 0.01:
        penalty -= 5
    
    # Trend weakening while price moving
    if adx < adx_onceki and abs(fiyat - fiyat_onceki) / (fiyat_onceki if fiyat_onceki else 1) > 0.01:
        penalty -= 5
    
    return penalty

def check_sma50_divergence(fiyat, sma50, sma50_onceki):
    """Detects false breakouts - price above declining SMA50"""
    if sma50_onceki == 0:
        return 0
    
    sma50_slope = (sma50 - sma50_onceki) / sma50_onceki
    price_above_sma50 = fiyat > sma50
    
    if price_above_sma50 and sma50_slope < -0.005:  # SMA50 declining >0.5%
        return -10  # False breakout risk
    return 0

def check_volume_spike_trap(hacim_orani, hacim_onceki):
    """Detects isolated volume spikes (potential manipulation)"""
    # Current bar has huge volume spike but previous was normal
    if hacim_orani > 3.0 and hacim_onceki < 1.5:
        return -10  # Potential trap/manipulation
    return 0

# --- SCORING FUNCTIONS ---

def calculate_category_scores(data):
    """
    Returns individual category scores (Fundamental REMOVED)
    Redistributed: Trend +5, Momentum +5
    """
    scores = {
        'trend': 0,
        'momentum': 0,
        'volume': 0,
        'durability': 0
    }
    
    # Helper for safe access
    def get(key, default=0):
        return data.get(key, default)

    fiyat = data['fiyat']
    sma50 = data['sma50']
    sma200 = data['sma200']
    
    # TREND STRENGTH (35 points max - Updated)
    if fiyat > sma50:
        scores['trend'] += 10
    if sma50 > sma200:
        scores['trend'] += 10
    
    # Both SMAs passed with >2% gap (Boosted from 10 to 15)
    max_sma = max(sma50, sma200)
    if max_sma > 0:
        gap_pct = ((fiyat - max_sma) / max_sma)
        if fiyat > sma50 and fiyat > sma200 and gap_pct > 0.02:
            scores['trend'] += 15 # +5 Boost
    
    # MOMENTUM (30 points max - Updated)
    rsi = data['rsi']
    if 50 <= rsi <= 65:
        scores['momentum'] += 10
    if rsi > get('rsi_onceki'):
        scores['momentum'] += 10 # Boosted from 5 to 10
    if data['macd_hist'] > get('macd_hist_onceki'):
        scores['momentum'] += 5
    if data['macd_line'] > 0:
        scores['momentum'] += 5
    
    # VOLUME (20 points max - Unchanged)
    hacim_orani = data['hacim_orani']
    if hacim_orani > 1.2:
        scores['volume'] += 10
    if hacim_orani > get('hacim_onceki'):
        scores['volume'] += 5
    
    # Volume + price aligned
    price_up = fiyat > get('fiyat_onceki', fiyat)
    volume_up = hacim_orani > get('hacim_onceki', hacim_orani)
    if price_up == volume_up:
        scores['volume'] += 5
    
    # TREND DURABILITY (15 points max - Unchanged)
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
    Calculates total score including penalties
    Returns: (total_score, category_scores_dict)
    """
    category_scores = calculate_category_scores(data)
    base_score = sum(category_scores.values())
    
    # Helper for safe access
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
    Category Validation for STRONG_BUY:
    Requires at least 3 categories to pass 70% threshold
    """
    thresholds = {
        'trend': 24.5,      # 70% of 35
        'momentum': 21,     # 70% of 30
        'volume': 14,       # 70% of 20
        'durability': 11    # 70% of 15
    }
    
    categories_passed = sum(
        1 for category, score in category_scores.items()
        if score >= thresholds.get(category, 999)
    )
    
    return categories_passed >= 3

def generate_signal(total_score, category_scores):
    # --- AYAR 3: Barajı Yükselt ---
    
    if total_score >= 80: # 80 üzeri Strong Buy olsun
        if validate_strong_buy_categories(category_scores):
            return 'STRONG_BUY'
        else:
            return 'BUY'
    elif total_score >= 70: # ESKİSİ 65 İDİ -> ŞİMDİ 70
        return 'BUY'
    elif total_score >= 60:
        return 'WATCH' # 60-69 arası artık sadece izleme listesinde
    else:
        return 'NO_TRADE'

def calculate_stop_and_target(fiyat, atr, rsi, adx):
    """
    Final Tuning: Balanced Approach
    Stop: 2.5 ATR (Sweet spot between 2.0 and 3.0)
    Target: Boosted back to ~2.0x because Win Rate is high (>55%)
    """
    if atr <= 0:
        atr = fiyat * 0.03 
        
    # --- AYAR 1: Stop Mesafesi (2.5 ATR) ---
    stop_distance = 2.5 * atr
    stop_price = fiyat - stop_distance
    stop_price = max(0.01, stop_price)
            
    risk = fiyat - stop_price
    
    # --- AYAR 2: Hedef Çarpanı (Target Multiplier) ---
    multiplier = 2.0  # Standart Hedef (Geri yükselttik)
    
    # RSI İnce Ayarı
    if rsi > 70:
        if adx > 30:
            multiplier = 2.0 # Güçlü trend, korkma, bırak koşsun.
        else:
            multiplier = 1.2 # Sadece şişmiş, vur-kaç yap.
    elif rsi > 60:
        multiplier = 1.8 # Hafif temkinli
        
    target_price = fiyat + (risk * multiplier)
    
    return round(stop_price, 2), round(target_price, 2)

def evaluate_stock(data):
    """
    Main entry point for trading engine
    Returns: (signal, score, stop_price, target_price)
    """
    # 1. Hard Filters
    if not hard_filters(data):
        return 'NO_TRADE', 0, 0, 0
        
    # 2. Scoring & Penalties
    total_score, category_scores = calculate_total_score(data)
    
    # 3. Decision
    signal = generate_signal(total_score, category_scores)
    
    # 4. Stop/Target (Dynamic ATR + RSI/ADX)
    stop_price, target_price = calculate_stop_and_target(
        data['fiyat'], 
        data.get('atr', 0),
        data['rsi'],
        data['adx']
    )
    
    # If signal is NO_TRADE by score, reset targets
    if signal == 'NO_TRADE':
        stop_price = 0
        target_price = 0
        
    return signal, total_score, stop_price, target_price
