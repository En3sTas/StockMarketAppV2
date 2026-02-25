"""
Smart Picks Backtest — Unified Conviction Engine (REAL DATA)
==============================================================
Self-contained: market regime, portfolio simulation, and deep-dive
analysis are all inlined — no external helper imports required.

Run:  python src/backtest/backtest_smart_picks.py
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from core import trend_engine

# ==============================================================================
# Market Regime (inline — no external import needed)
# ==============================================================================
def get_market_regime(df, window=200):
    """Equal-weighted proxy index > MA(200) → BULL."""
    df = df.sort_values(['Symbol', 'Date'])
    df['_prev'] = df.groupby('Symbol')['Close'].shift(1)
    df['_ret']  = (df['Close'] / df['_prev']) - 1
    index_ret   = df.groupby('Date')['_ret'].mean()
    market_idx  = (1 + index_ret.fillna(0)).cumprod() * 100
    regime      = market_idx > market_idx.rolling(window).mean()
    df.drop(columns=['_prev', '_ret'], inplace=True, errors='ignore')
    return regime.fillna(False)


# ==============================================================================
# Config
# ==============================================================================
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE    = os.path.join(BASE_DIR, "data", "backtest_data.parquet")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results_smart_picks.csv")

WARM_UP_DAYS  = 250
MAX_HOLD_DAYS = 40    
ATR_TRAIL_AMP = 4.0   
ATR_TARGET    = 6.0

# ==============================================================================
# Unified Score Logic  (main.py ile birebir eslendirildi)
# ==============================================================================
REGIME_MULTIPLIER = {"BULL": 1.0, "SIDEWAYS": 0.85, "BEAR": 0.6}


def derive_tags(row, regime):
    """
    Pre-computed parquet kolonlarindan tag listesi türet.
    main.py / pro_engine.py mantigi ile uyumlu.
    """
    tags = []
    rsi     = row['RSI_14']
    adx     = row['ADX_14']
    dmp     = row['DMP_14']
    dmn     = row['DMN_14']
    macd_h  = row['MACDh_12_26_9']
    sma50   = row['SMA_50']
    sma200  = row['SMA_200']
    close   = row['Close']
    vol_r   = row['hacim_orani']

    # --- Positive tags ---
    if adx > 25 and dmp > dmn:
        tags.append("Strong Trend")
    if vol_r > 2.0:
        tags.append("Whale Volume")
    if close > sma50 > sma200:
        tags.append("Long-Term Bull")
    if close > sma200 and macd_h > 0:
        tags.append("Above VWMA")

    # --- Warning tags ---
    if rsi > 70:
        tags.append("Overbought warning")
    if vol_r > 3.5 and macd_h < 0:
        tags.append("Vol Divergence")
    if adx < 20:
        tags.append("Weak Trend")

    # --- Danger tags ---
    falling_knife = (close < sma200 * 0.92 and rsi < 35 and vol_r > 1.5)
    if falling_knife:
        tags.append("Falling Knife")

    high_sell_vol = (vol_r > 2.5 and macd_h < -0.5 and close < sma50)
    if high_sell_vol:
        tags.append("High Sell Vol")

    bear_risk = (regime == "BEAR" and close < sma200)
    if bear_risk:
        tags.append("Bear Regime Risk")

    return tags


def calculate_unified_score(base_score, tags, regime):
    POSITIVE = {"Strong Trend", "Whale Volume", "Long-Term Bull", "Above VWMA"}
    WARNING  = {"Overbought warning", "Vol Divergence", "Weak Trend"}
    DANGER   = {"Falling Knife", "High Sell Vol", "Bear Regime Risk"}

    pc = sum(1 for t in tags if any(p in t for p in POSITIVE))
    wc = sum(1 for t in tags if any(w in t for w in WARNING))
    dc = sum(1 for t in tags if any(d in t for d in DANGER))

    modifier = pc*5 + wc*-5 + dc*-15
    mult     = REGIME_MULTIPLIER.get(regime, 0.85)
    raw      = max(0, min(100, base_score + modifier))
    unified  = max(0, min(100, int(raw * mult)))

    # --- Veto rules ---
    has_knife = any("Falling Knife" in t for t in tags)
    has_bear  = any("Bear Regime Risk" in t for t in tags)
    has_hvol  = any("High Sell Vol" in t for t in tags)
    has_ob    = any("Overbought" in t for t in tags)

    if unified >= 80 and dc == 0:  sig = "STRONG_BUY"
    elif unified >= 65:             sig = "BUY"
    elif unified >= 50:             sig = "WATCH"
    else:                           sig = "NO_TRADE"

    if has_knife:                                            sig = "NO_TRADE"
    elif has_bear and base_score < 70 and sig in ("STRONG_BUY","BUY"): sig = "WATCH"
    elif has_ob and has_hvol and sig in ("STRONG_BUY","BUY"):           sig = "WATCH"
    if has_hvol and sig in ("STRONG_BUY","BUY"):                        sig = "WATCH"

    # --- Conviction ---
    if base_score >= 70 and pc >= 2 and dc == 0 and regime != "BEAR": conv = "DIAMOND"
    elif base_score >= 65 and pc >= 1 and dc == 0:                      conv = "GOLD"
    elif base_score >= 50 and pc >= 1:                                   conv = "SILVER"
    else:                                                                 conv = "BRONZE"

    return unified, sig, conv


# ==============================================================================
# Simulation
# ==============================================================================

def run_simulation(data_path=DATA_FILE, holding_days=MAX_HOLD_DAYS):
    print(f"Starting Smart Picks Backtest (Max Hold: {holding_days} days)...")

    # -- Load data --
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        print(f"Parquet read failed ({e}), trying CSV...")
        csv_path = data_path.replace("parquet", "csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            print(f"Error: Data file not found at {data_path}")
            return None

    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['datetime'])
    df = df.sort_values(['Symbol', 'Date'])

    # -- Market Regime --
    print("  Calculating Market Regime (XU100 proxy)...")
    market_regime = get_market_regime(df)

    trades           = []
    active_positions = {}
    symbols          = df['Symbol'].unique()

    print(f"  Symbols: {len(symbols)} | Rows: {len(df):,}")

    for symbol in symbols:
        sdf = df[df['Symbol'] == symbol].reset_index(drop=True)

        if len(sdf) < WARM_UP_DAYS:
            continue

        for i in range(WARM_UP_DAYS, len(sdf) - 1):
            today    = sdf.iloc[i]
            tomorrow = sdf.iloc[i+1]
            date_today = today['Date']

            # ── Exits ──────────────────────────────────────────────────
            if symbol in active_positions:
                trade     = active_positions[symbol]
                days_held = (date_today - trade['entry_date']).days
                atr_entry = trade.get('atr_at_entry', trade['entry_price'] * 0.025)

                # Trailing stop (move up only)
                current_price = today['Close']
                new_trail = current_price - ATR_TRAIL_AMP * atr_entry
                if new_trail > trade['stop_price']:
                    trade['stop_price'] = new_trail

                exit_reason = None
                exit_price  = 0

                if tomorrow['Low'] <= trade['stop_price']:
                    exit_price = min(trade['stop_price'], tomorrow['Open'])
                    exit_reason = 'TRAILING_STOP' if exit_price > trade['entry_price'] else 'STOP_LOSS'
                elif tomorrow['High'] >= trade['target_price']:
                    exit_reason = 'TAKE_PROFIT'
                    exit_price  = max(trade['target_price'], tomorrow['Open'])
                elif days_held >= holding_days:
                    exit_reason = 'TIME_EXIT'
                    exit_price  = tomorrow['Close']

                if exit_reason:
                    trade['exit_date']  = tomorrow['Date']
                    trade['exit_price'] = exit_price
                    trade['pnl']        = (exit_price - trade['entry_price']) / trade['entry_price']
                    trade['exit_reason']= exit_reason
                    trade['days_held']  = days_held
                    trades.append(trade)
                    del active_positions[symbol]
                    continue

            # ── Entries ────────────────────────────────────────────────
            # Market regime filter
            is_bull = market_regime.get(date_today, False)
            regime  = "BULL" if is_bull else "SIDEWAYS"

            # Kural 3: Yatayda dur — SIDEWAYS rejiminde yeni pozisyon acma
            if regime == "SIDEWAYS":
                continue

            # Build row_data for engine
            try:
                row_data = {
                    'fiyat':            float(today['Close']),
                    'sma50':            float(today['SMA_50']),
                    'sma200':           float(today['SMA_200']),
                    'rsi':              float(today['RSI_14']),
                    'macd_hist':        float(today['MACDh_12_26_9']),
                    'macd_line':        float(today['MACD_12_26_9']),
                    'adx':              float(today['ADX_14']),
                    'dmp':              float(today['DMP_14']),
                    'dmn':              float(today['DMN_14']),
                    'hacim_orani':      float(today['hacim_orani']),
                    'fiyat_onceki':     float(today['fiyat_onceki']),
                    'rsi_onceki':       float(today['rsi_onceki']),
                    'adx_onceki':       float(today['adx_onceki']),
                    'macd_hist_onceki': float(today['macd_hist_onceki']),
                    'hacim_onceki':     float(today['hacim_onceki']),
                    'sma50_onceki':     float(today['sma50_onceki']),
                    'swing_low':        float(today['swing_low']),
                    'fk':               10,
                    'pd_dd':            1.5,
                    'atr':              float(today['ATRr_14'])
                }
            except (KeyError, ValueError):
                continue

            # Kural 1: Sadece Trend Engine kullan (Scout kapali)
            try:
                _, base_score, stop_price, target_price = trend_engine.evaluate_stock(row_data)
                engine_used = 'TREND'
            except Exception:
                continue

            # Derive tags + unified score
            tags   = derive_tags(today, regime)
            atr    = row_data['atr']

            # Override stop/target with ATR-based if engine gave 0
            if stop_price <= 0 or stop_price >= today['Close']:
                stop_price   = today['Close'] - ATR_TRAIL_AMP * atr
            if target_price <= today['Close']:
                target_price = today['Close'] + ATR_TARGET * atr

            unified, signal, conviction = calculate_unified_score(base_score, tags, regime)

            # Kural 2: Sadece DIAMOND conviction kabul et
            if signal not in ('STRONG_BUY', 'BUY'):
                continue
            if conviction != 'DIAMOND':
                continue
            if unified < 65:
                continue

            active_positions[symbol] = {
                'symbol':       symbol,
                'signal':       signal,
                'conviction':   conviction,
                'regime':       regime,
                'score':        base_score,
                'unified_score':unified,
                'engine':       engine_used,
                'entry_date':   tomorrow['Date'],
                'entry_price':  tomorrow['Open'],
                'stop_price':   stop_price,
                'target_price': target_price,
                'atr_at_entry': atr,
            }

    results = pd.DataFrame(trades)
    return results


# ==============================================================================
# Deep Dive (Smart Picks ekleri ile)
# ==============================================================================

def run_smart_picks_deep_dive(df):
    """deep_dive.py formatini genisletir: Conviction + Regime analizleri ekle."""

    # -- Baz analizler (deep_dive.py ile ayni) --
    print("\n--- 1. ANALYSIS BY SIGNAL TYPE ---")
    sig = df.groupby('signal').agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
        Max_DD   = ('pnl', lambda x: x.min() * 100),
    ).sort_values('Win_Rate', ascending=False)
    print(sig.round(2))

    print("\n--- 2. ANALYSIS BY UNIFIED SCORE BUCKET ---")
    bins   = [0, 50, 60, 70, 80, 101]
    labels = ['0-49','50-59','60-69','70-79','80+']
    df['Score_Range'] = pd.cut(df['unified_score'], bins=bins, labels=labels, right=False)
    sc = df.groupby('Score_Range', observed=True).agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
        Avg_Days = ('days_held', 'mean'),
    )
    print(sc.round(2))

    print("\n--- 3. EXIT REASON BREAKDOWN ---")
    ec = df['exit_reason'].value_counts()
    ep = df['exit_reason'].value_counts(normalize=True) * 100
    print(pd.DataFrame({'Count': ec, 'Percentage': ep}).round(1))

    print("\n--- 4. WIN VS LOSS ANALYSIS ---")
    wins   = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    aw = wins['pnl'].mean()   * 100 if not wins.empty   else 0
    al = losses['pnl'].mean() * 100 if not losses.empty else 0
    rr = abs(aw / al) if al != 0 else 0
    print(f"Average Winner    :  +{aw:.2f}%")
    print(f"Average Loser     :   {al:.2f}%")
    print(f"Risk/Reward Ratio :  1 : {rr:.2f}")

    print("\n--- 5. ANALYSIS BY CONVICTION TIER ---")
    conv = df.groupby('conviction').agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
        Sharpe   = ('pnl', lambda x: x.mean()/x.std() if x.std()>0 else 0),
    ).reindex(['DIAMOND','GOLD','SILVER','BRONZE']).dropna()
    print(conv.round(2))

    print("\n--- 6. ANALYSIS BY MARKET REGIME ---")
    reg = df.groupby('regime').agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
    )
    print(reg.round(2))





# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("Smart Picks Strategy Backtest (2006-2026)")
    print("Kurallar: Sadece TREND Engine | Sadece DIAMOND | BULL rejiminde gir")
    print("-" * 60)

    results = run_simulation()

    print(f"\nSimulation Complete. Total Trades: {len(results) if results is not None else 0}")

    if results is not None and not results.empty:
        results.to_csv(RESULTS_FILE, index=False)

        # --- Inline Portfolio Simulation ---
        INIT_CAP = 30_000; MAX_POS = 5; COM = 0.001
        df_r = results.copy()
        df_r['entry_date'] = pd.to_datetime(df_r['entry_date'])
        df_r['exit_date']  = pd.to_datetime(df_r['exit_date'])
        events = []
        for idx, r in df_r.iterrows():
            events.append({'date': r['entry_date'], 'type': 'ENTRY', 'pnl': 0,       'id': idx})
            events.append({'date': r['exit_date'],  'type': 'EXIT',  'pnl': r['pnl'], 'id': idx})
        ev = pd.DataFrame(events).sort_values(['date','type'], ascending=[True,False])
        cash, pos, skipped = INIT_CAP, {}, 0
        for _, e in ev.iterrows():
            tid = e['id']
            if e['type'] == 'EXIT' and tid in pos:
                cash += pos[tid] * (1 + e['pnl']) * (1 - COM); del pos[tid]
            elif e['type'] == 'ENTRY' and len(pos) < MAX_POS:
                equity = cash + sum(pos.values())
                alloc  = min(cash, equity / MAX_POS)
                if alloc > 100: pos[tid] = alloc*(1-COM); cash -= alloc
                else: skipped += 1
            else:
                if e['type'] == 'ENTRY': skipped += 1
        final = cash + sum(pos.values())
        yrs   = (ev['date'].max() - ev['date'].min()).days / 365.25
        cagr  = (final / INIT_CAP) ** (1 / max(yrs, 0.01)) - 1
        print(f"Initial Capital: {INIT_CAP:,.2f} TL | Max Positions: {MAX_POS}")
        print("-" * 40)
        print(f"Final Equity : {final:,.2f} TL")
        print(f"Total Return : {(final-INIT_CAP)/INIT_CAP*100:.2f}%")
        print(f"CAGR         : %{cagr*100:.2f}")
        print(f"Skipped      : {skipped}")
        print("-" * 40)

        print("\n" + "="*50)
        print("       DEEP DIVE - SMART PICKS ANALYSIS")
        print("="*50)
        run_smart_picks_deep_dive(results)
    else:
        print("No trades generated.")
