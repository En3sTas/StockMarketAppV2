
import pandas as pd
import numpy as np
import os

# Simulation Parameters
INITIAL_CAPITAL = 30000       
MAX_POSITIONS = 5             
COMMISSION = 0.001           

# Path Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results.csv")

def run_portfolio_simulation(results_file=RESULTS_FILE):
    print(f"💰 Starting Portfolio Simulation (2007-2026)")
    print(f"🎯 Initial Capital: {INITIAL_CAPITAL:,.2f} TL")
    print(f"🧩 Max Positions: {MAX_POSITIONS}")
    print("-" * 40)

    # 1. Load Trade Data
    try:
        df = pd.read_csv(results_file)
    except Exception as e:
        print(f"❌ {results_file} not found! Error: {e}")
        return

    # Convert dates
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    
    # 2. Build Event Timeline (Entries & Exits)
    events = []
    
    for idx, row in df.iterrows():
        # Entry Event
        events.append({
            'date': row['entry_date'],
            'type': 'ENTRY',
            'symbol': row['symbol'],
            'pnl': 0,
            'trade_id': idx
        })
        # Exit Event
        events.append({
            'date': row['exit_date'],
            'type': 'EXIT',
            'symbol': row['symbol'],
            'pnl': row['pnl'],
            'trade_id': idx
        })
    
    events_df = pd.DataFrame(events)
    events_df = events_df.sort_values(by=['date', 'type'], ascending=[True, False]) 
    
    # 3. Execution Loop
    dashboard = {
        'cash': INITIAL_CAPITAL,
        'equity': INITIAL_CAPITAL,
        'active_positions': {}, # trade_id -> invested_amount
        'history': [],
        'skipped_trades': 0
    }

    current_positions = 0
    
    for _, event in events_df.iterrows():
        trade_id = event['trade_id']
        
        # Process Exits
        if event['type'] == 'EXIT':
            if trade_id in dashboard['active_positions']:
                invested = dashboard['active_positions'][trade_id]
                gross_return = invested * (1 + event['pnl'])
                net_return = gross_return * (1 - COMMISSION)
                
                dashboard['cash'] += net_return
                del dashboard['active_positions'][trade_id]
                current_positions -= 1
        
        # Process Entries
        elif event['type'] == 'ENTRY':
            if current_positions < MAX_POSITIONS:
                total_equity = dashboard['cash'] + sum(dashboard['active_positions'].values())
                target_per_trade = total_equity / MAX_POSITIONS
                allocation = min(dashboard['cash'], target_per_trade)
                
                if allocation > 100:
                    allocation = allocation * (1 - COMMISSION)
                    dashboard['cash'] -= allocation
                    dashboard['active_positions'][trade_id] = allocation
                    current_positions += 1
                else:
                    dashboard['skipped_trades'] += 1
            else:
                dashboard['skipped_trades'] += 1

    # 4. Reporting
    final_equity = dashboard['cash'] + sum(dashboard['active_positions'].values())
    total_years = (events_df['date'].max() - events_df['date'].min()).days / 365.25
    cagr = (final_equity / INITIAL_CAPITAL) ** (1 / total_years) - 1
    
    print(f"🏁 Final Equity: {final_equity:,.2f} TL")
    print(f"📈 Total Return: {((final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100:.2f}%")
    print(f"📅 CAGR (Yıllık Ortalama Getiri): %{cagr*100:.2f}")
    print(f"🚫 Skipped Trades (Full Portfolio): {dashboard['skipped_trades']}")
    print("-" * 40)

if __name__ == "__main__":
    run_portfolio_simulation()
