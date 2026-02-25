"""
Trend Strategy Backtest
=======================
Self-contained: market regime, portfolio simulation, and deep-dive analysis
are all included inline — no external helper imports required.

Run:  python src/backtest/backtest_trend.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from core import trend_engine

# ── Paths & Config ────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE    = os.path.join(BASE_DIR, "data", "backtest_data.parquet")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results_trend.csv")

WARM_UP_DAYS    = 250
MAX_HOLD_DAYS   = 45
MIN_SCORE       = 70
INITIAL_CAPITAL = 30_000
MAX_POSITIONS   = 5
COMMISSION      = 0.001


# ── Market Regime ─────────────────────────────────────────────────────────────
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


# ── Backtest Core ─────────────────────────────────────────────────────────────
def run_simulation(df=None, data_path=DATA_FILE,
                   holding_days=MAX_HOLD_DAYS, min_score=MIN_SCORE):
    if df is None:
        print(f"Starting Trend Strategy Backtest "
              f"(Max Hold: {holding_days}d | Min Score: {min_score})...")
        try:
            df = pd.read_parquet(data_path)
        except Exception as e:
            csv = data_path.replace("parquet", "csv")
            if os.path.exists(csv):
                df = pd.read_csv(csv)
            else:
                print(f"Data file not found: {data_path} ({e})")
                return None

    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['datetime'])
    df = df.sort_values(['Symbol', 'Date'])

    print("  Calculating Market Regime (XU100 proxy)...")
    market_regime = get_market_regime(df)
    print(f"  Symbols: {df['Symbol'].nunique()} | Rows: {len(df):,}")

    trades, active = [], {}

    for symbol in df['Symbol'].unique():
        sdf = df[df['Symbol'] == symbol].reset_index(drop=True)
        if len(sdf) < WARM_UP_DAYS:
            continue

        for i in range(WARM_UP_DAYS, len(sdf) - 1):
            today    = sdf.iloc[i]
            tomorrow = sdf.iloc[i + 1]

            # ── Exit logic ──────────────────────────────────────────────────
            if symbol in active:
                t         = active[symbol]
                days_held = (today['Date'] - t['entry_date']).days
                atr       = t.get('atr_at_entry', t['entry_price'] * 0.03)

                # Trailing stop: only move up
                new_stop = today['Close'] - 2.0 * atr
                if new_stop > t['stop_price']:
                    t['stop_price'] = new_stop

                exit_reason = exit_price = None
                if tomorrow['Low'] <= t['stop_price']:
                    exit_price  = min(t['stop_price'], tomorrow['Open'])
                    exit_reason = 'TRAILING_STOP' if exit_price > t['entry_price'] else 'STOP_LOSS'
                elif tomorrow['High'] >= t['target_price']:
                    exit_price  = max(t['target_price'], tomorrow['Open'])
                    exit_reason = 'TAKE_PROFIT'
                elif days_held >= holding_days:
                    exit_price  = tomorrow['Close']
                    exit_reason = 'TIME_EXIT'

                if exit_reason:
                    t.update(exit_date=tomorrow['Date'], exit_price=exit_price,
                             pnl=(exit_price - t['entry_price']) / t['entry_price'],
                             exit_reason=exit_reason, days_held=days_held)
                    trades.append(t)
                    del active[symbol]
                    continue

            # ── Entry logic ─────────────────────────────────────────────────
            if not market_regime.get(today['Date'], False):
                continue

            row = {
                'fiyat': float(today['Close']),  'sma50': float(today['SMA_50']),
                'sma200': float(today['SMA_200']), 'rsi': float(today['RSI_14']),
                'macd_hist': float(today['MACDh_12_26_9']),
                'macd_line': float(today['MACD_12_26_9']),
                'adx': float(today['ADX_14']),    'dmp': float(today['DMP_14']),
                'dmn': float(today['DMN_14']),
                'hacim_orani': float(today['hacim_orani']),
                'fiyat_onceki': float(today['fiyat_onceki']),
                'rsi_onceki': float(today['rsi_onceki']),
                'adx_onceki': float(today['adx_onceki']),
                'macd_hist_onceki': float(today['macd_hist_onceki']),
                'hacim_onceki': float(today['hacim_onceki']),
                'sma50_onceki': float(today['sma50_onceki']),
                'swing_low': float(today['swing_low']),
                'fk': 10, 'pd_dd': 1.5, 'atr': float(today['ATRr_14'])
            }
            signal, score, stop_price, target_price = trend_engine.evaluate_stock(row)

            if score >= min_score:
                active[symbol] = {
                    'symbol': symbol, 'signal': signal, 'score': score,
                    'entry_date': tomorrow['Date'], 'entry_price': tomorrow['Open'],
                    'stop_price': stop_price, 'target_price': target_price,
                    'atr_at_entry': row['atr'],
                }

    return pd.DataFrame(trades)


# ── Portfolio Simulation ───────────────────────────────────────────────────────
def run_portfolio_simulation(results_file):
    print(f"\n--- Portfolio Simulation Results ---")
    print(f"Initial Capital: {INITIAL_CAPITAL:,.2f} TL | Max Positions: {MAX_POSITIONS}")
    print("-" * 40)

    df = pd.read_csv(results_file)
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date']  = pd.to_datetime(df['exit_date'])

    events = []
    for idx, r in df.iterrows():
        events.append({'date': r['entry_date'], 'type': 'ENTRY', 'pnl': 0,       'id': idx})
        events.append({'date': r['exit_date'],  'type': 'EXIT',  'pnl': r['pnl'], 'id': idx})
    ev = pd.DataFrame(events).sort_values(['date', 'type'], ascending=[True, False])

    cash, positions, skipped = INITIAL_CAPITAL, {}, 0
    for _, e in ev.iterrows():
        tid = e['id']
        if e['type'] == 'EXIT' and tid in positions:
            cash += positions[tid] * (1 + e['pnl']) * (1 - COMMISSION)
            del positions[tid]
        elif e['type'] == 'ENTRY' and len(positions) < MAX_POSITIONS:
            equity = cash + sum(positions.values())
            alloc  = min(cash, equity / MAX_POSITIONS)
            if alloc > 100:
                positions[tid] = alloc * (1 - COMMISSION)
                cash -= alloc
            else:
                skipped += 1
        else:
            if e['type'] == 'ENTRY':
                skipped += 1

    final  = cash + sum(positions.values())
    years  = (ev['date'].max() - ev['date'].min()).days / 365.25
    cagr   = (final / INITIAL_CAPITAL) ** (1 / max(years, 0.01)) - 1

    print(f"Final Equity : {final:,.2f} TL")
    print(f"Total Return : {(final - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100:.2f}%")
    print(f"CAGR         : %{cagr * 100:.2f}")
    print(f"Skipped      : {skipped}")
    print("-" * 40)


# ── Deep Dive Analysis ────────────────────────────────────────────────────────
def run_deep_dive(results_file):
    df = pd.read_csv(results_file)

    print("\n" + "=" * 50)
    print("       DEEP DIVE - TREND STRATEGY ANALYSIS")
    print("=" * 50)

    # 1. Signal
    print("\n--- 1. ANALYSIS BY SIGNAL TYPE ---")
    sig = df.groupby('signal').agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
        Max_DD   = ('pnl', lambda x: x.min() * 100),
    )
    print(sig.round(2))

    # 2. Score buckets
    print("\n--- 2. ANALYSIS BY SCORE BUCKET ---")
    df['Score_Range'] = pd.cut(df['score'],
        bins=[0, 60, 70, 80, 101], labels=['<60', '60-69', '70-79', '80+'], right=False)
    sc = df.groupby('Score_Range', observed=True).agg(
        Trades   = ('pnl', 'count'),
        Win_Rate = ('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Ret  = ('pnl', lambda x: x.mean() * 100),
        Avg_Days = ('days_held', 'mean'),
    )
    print(sc.round(2))

    # 3. Exit reasons
    print("\n--- 3. EXIT REASON BREAKDOWN ---")
    ex = pd.DataFrame({'Count': df['exit_reason'].value_counts(),
                       'Percentage': df['exit_reason'].value_counts(normalize=True) * 100})
    print(ex.round(1))

    # 4. Win/Loss
    print("\n--- 4. WIN VS LOSS ANALYSIS ---")
    wins   = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    avg_w  = wins['pnl'].mean() * 100   if not wins.empty   else 0
    avg_l  = losses['pnl'].mean() * 100 if not losses.empty else 0
    rr     = abs(avg_w / avg_l) if avg_l != 0 else 0
    print(f"Average Winner    : +{avg_w:.2f}%")
    print(f"Average Loser     :  {avg_l:.2f}%")
    print(f"Risk/Reward Ratio :  1 : {rr:.2f}")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = run_simulation()
    print(f"\nSimulation Complete. Total Trades: {len(results) if results is not None else 0}")

    if results is not None and not results.empty:
        results.to_csv(RESULTS_FILE, index=False)
        run_portfolio_simulation(RESULTS_FILE)
        run_deep_dive(RESULTS_FILE)
    else:
        print("No trades generated.")
