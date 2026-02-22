
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE_PATH = os.path.join(BASE_DIR, "data", "backtest_results.csv")

def run_deep_dive(results_file=FILE_PATH):
    try:
        df = pd.read_csv(results_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("="*50)
    print("       🚀 DEEP DIVE BACKTEST ANALYSIS        ")
    print("="*50)

    # 1. Signal Type Analysis
    print("\n--- 1. ANALYSIS BY SIGNAL TYPE ---")
    signal_grp = df.groupby('signal').agg(
        Trades=('pnl', 'count'),
        Win_Rate=('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Return=('pnl', lambda x: x.mean() * 100),
        Max_DD=('pnl', lambda x: x.min() * 100)
    ).sort_values('Win_Rate', ascending=False)
    
    print(signal_grp.round(2))

    # 2. Score Bucket Analysis
    print("\n--- 2. ANALYSIS BY SCORE BUCKET (Is Higher Better?) ---")
    bins = [60, 65, 70, 75, 80, 85, 101]
    labels = ['60-64', '65-69', '70-74', '75-79', '80-84', '85+']
    df['Score_Range'] = pd.cut(df['score'], bins=bins, labels=labels, right=False)
    
    score_grp = df.groupby('Score_Range', observed=True).agg(
        Trades=('pnl', 'count'),
        Win_Rate=('pnl', lambda x: (x > 0).mean() * 100),
        Avg_Return=('pnl', lambda x: x.mean() * 100),
        Avg_Days=('days_held', 'mean')
    )
    print(score_grp.round(2))

    # 3. Exit Reason Breakdown
    print("\n--- 3. EXIT REASON BREAKDOWN ---")
    exit_counts = df['exit_reason'].value_counts()
    exit_pct = df['exit_reason'].value_counts(normalize=True) * 100
    
    exit_df = pd.DataFrame({'Count': exit_counts, 'Percentage': exit_pct})
    print(exit_df.round(1))

    # 4. Win/Loss Ratio Analysis
    print("\n--- 4. WIN VS LOSS ANALYSIS ---")
    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    
    avg_win = wins['pnl'].mean() * 100 if not wins.empty else 0
    avg_loss = losses['pnl'].mean() * 100 if not losses.empty else 0
    
    print(f"Average Winner:  +{round(avg_win, 2)}%")
    print(f"Average Loser :  {round(avg_loss, 2)}%")
    print(f"Risk/Reward Ratio: 1 : {round(abs(avg_win/avg_loss), 2) if avg_loss != 0 else 0}")

if __name__ == "__main__":
    run_deep_dive()
