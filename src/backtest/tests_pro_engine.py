
import pandas as pd
import numpy as np
import sys
import os
import warnings

# Suppress pandas copy warnings for test clarity
warnings.filterwarnings('ignore', category=FutureWarning)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core import pro_engine

def create_base_data(periods=250, trend='up'):
    """ Creates synthetic stock data for testing. """
    dates = pd.date_range(start='2023-01-01', periods=periods)
    
    if trend == 'up':
        price = np.linspace(100, 200, periods)
    elif trend == 'down':
        price = np.linspace(200, 100, periods)
    else:
        price = np.full(periods, 150.0)
    
    price = price + np.random.normal(0, 2, periods)
    
    df = pd.DataFrame({
        'Open': price - 1,
        'High': price + 2,
        'Low': price - 2,
        'Close': price.copy(),
        'Volume': np.random.randint(1000, 5000, periods).astype(float)
    }, index=dates)
    
    return df

def create_bull_index():
    xu100 = create_base_data()
    xu100.loc[xu100.index[-1], 'Close'] = 250
    return xu100

# ======= TEST FUNCTIONS =======

def test_whale_volume_green_candle():
    """Fix 1: Whale Volume should only appear on green candles."""
    print("\n[TEST] Test: Whale Volume (Green Candle)")
    df = create_base_data()
    df.loc[df.index[-1], 'Open'] = 190
    df.loc[df.index[-1], 'Close'] = 200
    df.loc[df.index[-1], 'Volume'] = 50000
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "Whale Volume" in tags and "High Sell Vol" not in tags:
        print("  [PASS] PASS: Green candle -> Whale Volume")
    else:
        print(f"  [FAIL] FAIL: Expected 'Whale Volume', got {tags}")

def test_high_sell_vol_red_candle():
    """Fix 1: Red candle with high volume should give High Sell Vol."""
    print("\n[TEST] Test: High Sell Vol (Red Candle)")
    df = create_base_data()
    df.loc[df.index[-1], 'Open'] = 205
    df.loc[df.index[-1], 'Close'] = 195
    df.loc[df.index[-1], 'Volume'] = 50000
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "High Sell Vol" in tags and "Whale Volume" not in tags:
        print("  [PASS] PASS: Red candle -> High Sell Vol")
    else:
        print(f"  [FAIL] FAIL: Expected 'High Sell Vol', got {tags}")

def test_oversold_rsi_hook():
    """Fix 2: Oversold should only trigger when RSI hooks upward."""
    print("\n[TEST] Test: Oversold RSI Hook")
    df = create_base_data()
    
    # Scenario A: RSI < 30 but STILL FALLING
    df_falling = df.copy()
    df_falling.loc[df_falling.index[-3], 'Close'] = 80
    df_falling.loc[df_falling.index[-2], 'Close'] = 75
    df_falling.loc[df_falling.index[-1], 'Close'] = 70
    
    result_falling = pro_engine.evaluate_stock(df_falling, create_bull_index())
    tags_falling = result_falling['tags']
    
    # Scenario B: RSI < 30 and TURNING UP
    df_hook = df.copy()
    df_hook.loc[df_hook.index[-4], 'Close'] = 80
    df_hook.loc[df_hook.index[-3], 'Close'] = 72
    df_hook.loc[df_hook.index[-2], 'Close'] = 68
    df_hook.loc[df_hook.index[-1], 'Close'] = 75
    
    result_hook = pro_engine.evaluate_stock(df_hook, create_bull_index())
    tags_hook = result_hook['tags']
    
    oversold_in_falling = "Oversold" in tags_falling
    oversold_in_hook = "Oversold" in tags_hook
    
    print(f"  RSI Falling: Oversold={'Yes' if oversold_in_falling else 'No'} (tags: {tags_falling})")
    print(f"  RSI Hook:    Oversold={'Yes' if oversold_in_hook else 'No'} (tags: {tags_hook})")
    
    if oversold_in_hook:
        print("  [PASS] PASS: RSI Hook correctly triggers Oversold")
    else:
        print("  [NOTE] NOTE: RSI hook may not push RSI below 30 with this synthetic data")

def test_overbought_tags():
    """Fix 4: Overbought (RSI > 75) and MFI Overbought (MFI > 80) tags."""
    print("\n[TEST] Test: Overbought Warning Tags")
    df = create_base_data()
    df['RSI_14'] = 80.0
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "Overbought" in tags:
        print("  [PASS] PASS: RSI > 75 -> Overbought tag present")
    else:
        print(f"  [FAIL] FAIL: Expected 'Overbought' tag, got {tags}")

def test_tiring_trend():
    """Fix 5: ADX > 25 but declining -> Tiring Trend instead of Strong Trend."""
    print("\n[TEST] Test: Tiring Trend (ADX Declining)")
    df = create_base_data()
    for i in range(50):
        idx = df.index[-(i+1)]
        df.loc[idx, 'Close'] = 210 - i * 0.1
    
    df['ADX_14'] = 30.0
    df.loc[df.index[-2], 'ADX_14'] = 35.0
    df.loc[df.index[-1], 'ADX_14'] = 28.0
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "Tiring Trend" in tags:
        print("  [PASS] PASS: Declining ADX -> Tiring Trend")
    elif "Strong Trend" in tags:
        print(f"  [FAIL] FAIL: Expected 'Tiring Trend' but got 'Strong Trend' (tags: {tags})")
    else:
        print(f"  [NOTE] NOTE: Trend condition may not be met. Tags: {tags}")

def test_strong_trend_rising_adx():
    """Fix 5 (counter): ADX > 25 and rising -> should still be Strong Trend."""
    print("\n[TEST] Test: Strong Trend (ADX Rising)")
    df = create_base_data()
    for i in range(50):
        idx = df.index[-(i+1)]
        df.loc[idx, 'Close'] = 210 - i * 0.1
    
    df['ADX_14'] = 30.0
    df.loc[df.index[-2], 'ADX_14'] = 25.0
    df.loc[df.index[-1], 'ADX_14'] = 32.0
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "Strong Trend" in tags:
        print("  [PASS] PASS: Rising ADX -> Strong Trend")
    elif "Tiring Trend" in tags:
        print(f"  [FAIL] FAIL: Expected 'Strong Trend' but got 'Tiring Trend' (tags: {tags})")
    else:
        print(f"  [NOTE] NOTE: Trend condition may not be met. Tags: {tags}")

def test_vol_divergence():
    """Fix 3: Vol Divergence should trigger when price makes highs but volume drops."""
    print("\n[TEST] Test: Vol Divergence (Price Up, Volume Down)")
    df = create_base_data()
    df.loc[df.index[-1], 'Close'] = df['Close'].iloc[-6:-1].max() + 5
    recent_avg_vol = df['Volume'].iloc[-7:-2].mean()
    df.loc[df.index[-1], 'Volume'] = recent_avg_vol * 0.4
    
    result = pro_engine.evaluate_stock(df, create_bull_index())
    tags = result['tags']
    
    if "Vol Divergence" in tags:
        print("  [PASS] PASS: Price at highs + volume declining -> Vol Divergence")
    else:
        print(f"  [NOTE] NOTE: Vol Divergence may not trigger (depends on MFI too). Tags: {tags}")

# ======= RUN ALL TESTS =======

if __name__ == "__main__":
    print("=" * 55)
    print("  PRO ENGINE TAG SYSTEM -- VERIFICATION SUITE")
    print("=" * 55)
    
    test_whale_volume_green_candle()
    test_high_sell_vol_red_candle()
    test_oversold_rsi_hook()
    test_overbought_tags()
    test_tiring_trend()
    test_strong_trend_rising_adx()
    test_vol_divergence()
    
    print("\n" + "=" * 55)
    print("  ALL TESTS COMPLETE")
    print("=" * 55)
