
import sys
import os

# Allow import from core when running from backtest/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from core import trend_engine
from datetime import timedelta
import simulation

# --- PATH CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "data", "backtest_data.parquet")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results_trend.csv")

# --- BACKTEST CONFIG ---
INITIAL_CAPITAL = 100000 
HOLDING_PERIODS = [10] # 10 Days default
WARM_UP_DAYS = 250

def run_simulation(data_path=DATA_FILE, holding_days=10):
    print(f"🚀 Starting Trend Strategy Backtest (Max Hold: {holding_days} days)...")
    
    # Load Data
    try:
        df = pd.read_parquet(data_path)
    except:
        df = pd.read_csv(data_path.replace("parquet", "csv"))
        
    df = df.reset_index() 
    df['Date'] = pd.to_datetime(df['datetime'])
    df = df.sort_values(['Symbol', 'Date'])
    
    trades = []
    active_positions = {} # Symbol -> TradeDict
    
    symbols = df['Symbol'].unique()
    
    for symbol in symbols:
        stock_df = df[df['Symbol'] == symbol].reset_index(drop=True)
        
        # Iterate Row by Row
        for i in range(WARM_UP_DAYS, len(stock_df) - 1):
            today = stock_df.iloc[i]
            tomorrow = stock_df.iloc[i+1] 
            
            # 1. Manage Active Position (Exit Logic)
            if symbol in active_positions:
                trade = active_positions[symbol]
                days_held = (today['Date'] - trade['entry_date']).days
                
                # --- OPTIMIZED TRAILING LOGIC ---
                atr_entry = trade.get('atr_at_entry', trade['entry_price'] * 0.03)
                breakeven_trigger = trade['entry_price'] + (1.0 * atr_entry)
                
                if today['High'] >= breakeven_trigger:
                    new_stop = trade['entry_price'] + (0.1 * atr_entry)
                    if new_stop > trade['stop_price']:
                        trade['stop_price'] = new_stop

                # --- EXIT CHECKS ---
                exit_reason = None
                exit_price = 0
                
                if tomorrow['Low'] <= trade['stop_price']:
                    exit_reason = 'STOP_LOSS'
                    exit_price = min(trade['stop_price'], tomorrow['Open'])
                elif tomorrow['High'] >= trade['target_price']:
                    exit_reason = 'TAKE_PROFIT'
                    exit_price = max(trade['target_price'], tomorrow['Open'])
                elif days_held >= holding_days:
                    exit_reason = 'TIME_EXIT'
                    exit_price = tomorrow['Close']
                    
                if exit_reason:
                    trade['exit_date'] = tomorrow['Date']
                    trade['exit_price'] = exit_price
                    trade['pnl'] = (exit_price - trade['entry_price']) / trade['entry_price']
                    trade['exit_reason'] = exit_reason
                    trade['days_held'] = days_held
                    
                    trades.append(trade)
                    del active_positions[symbol]
                    continue 
            
            # 2. Check for New Entry
            row_data = {
                'fiyat': float(today['Close']),
                'sma50': float(today['SMA_50']),
                'sma200': float(today['SMA_200']),
                'rsi': float(today['RSI_14']),
                'macd_hist': float(today['MACDh_12_26_9']),
                'macd_line': float(today['MACD_12_26_9']),
                'adx': float(today['ADX_14']),
                'dmp': float(today['DMP_14']),
                'dmn': float(today['DMN_14']),
                'hacim_orani': float(today['hacim_orani']),
                'fiyat_onceki': float(today['fiyat_onceki']),
                'rsi_onceki': float(today['rsi_onceki']),
                'adx_onceki': float(today['adx_onceki']),
                'macd_hist_onceki': float(today['macd_hist_onceki']),
                'hacim_onceki': float(today['hacim_onceki']),
                'sma50_onceki': float(today['sma50_onceki']),
                'swing_low': float(today['swing_low']),
                'fk': 10,
                'pd_dd': 1.5,
                'atr': float(today['ATRr_14'])
            }
            
            signal, score, stop_price, target_price = trend_engine.evaluate_stock(row_data)
            
            if (signal == 'BUY' or signal == 'STRONG_BUY'):
                active_positions[symbol] = {
                    'symbol': symbol,
                    'signal': signal,
                    'score': score,
                    'entry_date': tomorrow['Date'],
                    'entry_price': tomorrow['Open'],
                    'stop_price': stop_price,
                    'target_price': target_price,
                    'atr_at_entry': row_data['atr'], 
                    'penalty_applied': (score < 60)
                }

    results = pd.DataFrame(trades)
    if not results.empty:
        print(f"✅ Simulation Complete. Total Trades: {len(results)}")
        results.to_csv(RESULTS_FILE, index=False)
        return results
    else:
        print("⚠️ No trades generated.")
        return None

if __name__ == "__main__":
    run_simulation(holding_days=10)
    print("\n--- Portfolio Simulation Results ---")
    simulation.run_portfolio_simulation(RESULTS_FILE)
    
    import deep_dive
    deep_dive.run_deep_dive(RESULTS_FILE)
