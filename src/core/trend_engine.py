
def hard_filters(data):
    """
    Applies strict filtering criteria to potential candidates for Trend Strategy.
    Returns True if the stock meets all tradeability requirements.
    """
    try:
        # Trend Condition: Golden Cross zone (Price > SMA200 and SMA50 > SMA200)
        if not (data['price'] > data['sma200'] and data['sma50'] > data['sma200']):
            return False

        # Liquidity Filter: Volume Ratio
        if data['volume_ratio'] < 0.5:
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
    """Penalty for overbought conditions."""
    if rsi > 80:
        return -20
    elif rsi > 70:
        return -10
    return 0


def check_volume_divergence(price, price_prev, volume_ratio, volume_prev):
    """Detects bearish volume divergence (price up, volume down)."""
    price_rising    = price > price_prev
    volume_declining = volume_ratio < volume_prev
    if price_rising and volume_declining:
        return -10
    return 0


def check_macd_momentum_loss(macd_hist, macd_hist_prev):
    """Detects weakening momentum."""
    if macd_hist < macd_hist_prev:
        return -8
    return 0


def check_adx_weakness(adx, adx_prev, price, price_prev):
    """Detects weak or weakening trends."""
    penalty = 0
    price_change_pct = abs(price - price_prev) / (price_prev if price_prev else 1)

    # Choppy range
    if adx < 20 and price_change_pct < 0.01:
        penalty -= 5

    # Trend weakening
    if adx < adx_prev and price_change_pct > 0.01:
        penalty -= 5

    return penalty


def check_sma50_divergence(price, sma50, sma50_prev):
    """Detects potential false breakouts (price > decreasing SMA50)."""
    if sma50_prev == 0:
        return 0

    sma50_slope    = (sma50 - sma50_prev) / sma50_prev
    price_above_sma50 = price > sma50

    if price_above_sma50 and sma50_slope < -0.005:
        return -10
    return 0


def check_volume_spike_trap(volume_ratio, volume_prev):
    """Detects isolated volume spikes which might indicate manipulation."""
    if volume_ratio > 3.0 and volume_prev < 1.5:
        return -10
    return 0


# --- SCORING FUNCTIONS ---

def calculate_category_scores(data):
    """
    Calculates scores for individual categories: Trend, Momentum, Volume, Durability.
    """
    scores = {
        'trend':      0,
        'momentum':   0,
        'volume':     0,
        'durability': 0
    }

    def get(key, default=0):
        return data.get(key, default)

    price  = data['price']
    sma50  = data['sma50']
    sma200 = data['sma200']

    # Trend Strength Scoring
    if price > sma50:
        scores['trend'] += 10
    if sma50 > sma200:
        scores['trend'] += 10

    # Strong Separation from SMAs
    max_sma = max(sma50, sma200)
    if max_sma > 0:
        gap_pct = (price - max_sma) / max_sma
        if price > sma50 and price > sma200 and gap_pct > 0.02:
            scores['trend'] += 15

    # Momentum Scoring
    rsi = data['rsi']
    if 50 <= rsi <= 65:
        scores['momentum'] += 10
    if rsi > get('rsi_prev'):
        scores['momentum'] += 10
    if data['macd_hist'] > get('macd_hist_prev'):
        scores['momentum'] += 5
    if data['macd_line'] > 0:
        scores['momentum'] += 5

    # Volume Scoring
    volume_ratio = data['volume_ratio']
    if volume_ratio > 1.2:
        scores['volume'] += 10
    if volume_ratio > get('volume_prev'):
        scores['volume'] += 5

    # Volume/Price Alignment
    price_up  = price > get('price_prev', price)
    volume_up = volume_ratio > get('volume_prev', volume_ratio)
    if price_up == volume_up:
        scores['volume'] += 5

    # Trend Durability Scoring
    adx = data['adx']
    if 20 <= adx <= 30:
        scores['durability'] += 5
    if adx > get('adx_prev'):
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
        data['price'],
        get('price_prev',  data['price']),
        data['volume_ratio'],
        get('volume_prev', data['volume_ratio'])
    )
    penalties += check_macd_momentum_loss(
        data['macd_hist'],
        get('macd_hist_prev', data['macd_hist'])
    )
    penalties += check_adx_weakness(
        data['adx'],
        get('adx_prev',   data['adx']),
        data['price'],
        get('price_prev', data['price'])
    )
    penalties += check_sma50_divergence(
        data['price'],
        data['sma50'],
        get('sma50_prev', data['sma50'])
    )
    penalties += check_volume_spike_trap(
        data['volume_ratio'],
        get('volume_prev', data['volume_ratio'])
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
        'trend':      24.5,
        'momentum':   21,
        'volume':     14,
        'durability': 11
    }

    categories_passed = sum(
        1 for category, score in category_scores.items()
        if score >= thresholds.get(category, 999)
    )

    return categories_passed >= 3


def generate_signal(total_score, category_scores):
    """Determines the trading signal based on score and category validation."""
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


def calculate_stop_and_target(price, atr, rsi, adx):
    """
    Calculates dynamic stop-loss and profit target levels using ATR.
    Adjusts targets based on trend strength (ADX) and overbought status (RSI).
    """
    if atr <= 0:
        atr = price * 0.03

    # Stop-Loss: 3.0 ATR (Trailing Stop logic)
    stop_distance = 3.0 * atr
    stop_price    = price - stop_distance
    stop_price    = max(0.01, stop_price)

    # Target: Dynamic Risk/Reward
    base_multiplier = 4.0

    # Boost target if trend is strong (ADX)
    if adx > 30:   base_multiplier += 2.0
    elif adx > 25: base_multiplier += 1.0

    # Reduce target if overbought (RSI)
    if rsi > 75:   base_multiplier -= 2.0
    elif rsi > 70: base_multiplier -= 1.0

    # Minimum 2x ATR profit target
    final_multiplier = max(2.0, base_multiplier)

    target_price = price + (final_multiplier * atr)

    return round(stop_price, 2), round(target_price, 2)


def evaluate_stock(data):
    """Main execution function for the Trend strategy."""
    # Apply Hard Filters
    if not hard_filters(data):
        return 'NO_TRADE', 0, 0, 0

    # Calculate Scores & Penalties
    total_score, category_scores = calculate_total_score(data)

    # Generate Signal
    signal = generate_signal(total_score, category_scores)

    # Calculate Risk Levels
    stop_price, target_price = calculate_stop_and_target(
        data['price'],
        data.get('atr', 0),
        data['rsi'],
        data['adx']
    )

    return signal, total_score, stop_price, target_price
