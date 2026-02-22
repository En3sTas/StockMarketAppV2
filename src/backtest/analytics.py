import pandas as pd
import numpy as np

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results.csv")

def calculate_metrics(df):
    """
    Calculates key performance indicators for a set of trades.
    """
    if df.empty:
        return {}
    
    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    
    win_rate = len(wins) / len(df) * 100
    avg_return = df['pnl'].mean() * 100
    avg_win = wins['pnl'].mean() * 100 if not wins.empty else 0
    avg_loss = losses['pnl'].mean() * 100 if not losses.empty else 0
    
    # Expectancy: (Win% * AvgWin) - (Loss% * AvgLoss)
    expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * abs(avg_loss))
    
    profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if not losses.empty and losses['pnl'].sum() != 0 else 999
    
    # Max Drawdown (per trade)
    max_dd = df['pnl'].min() * 100
    
    avg_hold = df['days_held'].mean()
    
    return {
        "Trades": len(df),
        "Win Rate %": round(win_rate, 2),
        "Avg Return %": round(avg_return, 2),
        "Expectancy %": round(expectancy, 2),
        "Profit Factor": round(profit_factor, 2),
        "Max DD %": round(max_dd, 2),
        "Avg Hold (Days)": round(avg_hold, 1)
    }

def print_metrics(title, metrics):
    print(f"\n--- {title} ---")
    for k, v in metrics.items():
        print(f"{k.ljust(20)}: {v}")

def run_analytics(file_path=RESULTS_FILE):
    """
    Loads backtest results and prints a comprehensive analysis.
    """
    print("📊 Loading Backtest Results...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Could not load results: {e}")
        return

    # 1. Overall Performance Statistics
    total_metrics = calculate_metrics(df)
    print_metrics("OVERALL PERFORMANCE", total_metrics)
    
    # 2. Score Bucket Analysis (Higher Score vs Performance)
    print("\n--- SCORE VALIDATION (Does Higher Score = Better Result?) ---")
    bins = [55, 65, 75, 85, 101]
    labels = ['55-64', '65-74', '75-84', '85+']
    df['ScoreBucket'] = pd.cut(df['score'], bins=bins, labels=labels, right=False)
    
    bucket_grp = df.groupby('ScoreBucket', observed=True)['pnl'].agg(['count', 'mean', lambda x: (x>0).mean()*100])
    bucket_grp.columns = ['Trades', 'Avg Return', 'Win Rate']
    print(bucket_grp)
    
    # 3. Penalty Analysis (Low Score Performance)
    print("\n--- PENALTY VALIDATION ---")
    penalized = df[df['score'] < 60]
    clean = df[df['score'] >= 60]
    
    print(f"Low Score (<60) Trades: {len(penalized)} | Win Rate: {round((penalized['pnl']>0).mean()*100,2) if not penalized.empty else 0}%")
    print(f"High Score (60+) Trades: {len(clean)} | Win Rate: {round((clean['pnl']>0).mean()*100,2) if not clean.empty else 0}%")

    # Time to Stop Analysis
    stops = df[df['exit_reason'] == 'STOP_LOSS']
    if not stops.empty:
        avg_stop_days = stops['days_held'].mean()
        print(f"\nAvg Days to Stop Loss: {round(avg_stop_days, 1)} days")

if __name__ == "__main__":
    run_analytics()
