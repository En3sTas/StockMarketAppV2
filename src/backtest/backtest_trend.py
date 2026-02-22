
import sys
import os

# Configure path to access core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import market_data
import pandas as pd
import numpy as np
from core import trend_engine
from datetime import timedelta
import simulation

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "data", "backtest_data.parquet")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "backtest_results_trend.csv")

# Backtest Settings
INITIAL_CAPITAL = 100000 
WARM_UP_DAYS = 250

def run_simulation(df=None, data_path=DATA_FILE, holding_days=45, min_score=70):
    if df is None:
        print(f"🚀 Starting Trend Strategy Backtest (Max Hold: {holding_days} days, Min Score: {min_score})...")
    
    # Init Data
    if df is None:
        try:
            df = pd.read_parquet(data_path)
        except Exception as e:
            print(f"⚠️ Parquet read failed ({e}), trying CSV...")
            if os.path.exists(data_path.replace("parquet", "csv")):
                df = pd.read_csv(data_path.replace("parquet", "csv"))
            else:
                print(f"Error: Data file not found at {data_path}")
                return None
            
        df = df.reset_index() 
        df['Date'] = pd.to_datetime(df['datetime'])
        df = df.sort_values(['Symbol', 'Date'])
    else:
         if 'Date' not in df.columns and 'datetime' in df.columns:
             df['Date'] = pd.to_datetime(df['datetime'])
         df = df.sort_values(['Symbol', 'Date'])
    
    # Calculate Market Regime
    print("  Calculating Market Regime (Proxy Index)...")
    market_regime = market_data.get_market_regime(df)
    
    trades = []
    active_positions = {}
    
    symbols = df['Symbol'].unique()
    
    for symbol in symbols:
        stock_df = df[df['Symbol'] == symbol].reset_index(drop=True)
        
        if len(stock_df) < WARM_UP_DAYS:
            continue

        for i in range(WARM_UP_DAYS, len(stock_df) - 1):
            today = stock_df.iloc[i]
            tomorrow = stock_df.iloc[i+1] 
            
            # Position Management (Exits)
            if symbol in active_positions:
                trade = active_positions[symbol]
                days_held = (today['Date'] - trade['entry_date']).days
                
                # Trailing Stop Management
                current_price = today['Close'] 
                atr = trade.get('atr_at_entry', trade['entry_price'] * 0.03)
                
                # Trail distance: 2 ATR
                trailing_distance = 2.0 * atr
                potential_new_stop = current_price - trailing_distance
                
                # Only move stop UP
                if potential_new_stop > trade['stop_price']:
                    trade['stop_price'] = potential_new_stop

                # Exit Conditions
                exit_reason = None
                exit_price = 0
                
                if tomorrow['Low'] <= trade['stop_price']:
                    exit_price = min(trade['stop_price'], tomorrow['Open'])
                    
                    # Check if stopped out in profit (Trailing Stop hit)
                    if exit_price > trade['entry_price']:
                        exit_reason = 'TRAILING_STOP'
                    else:
                        exit_reason = 'STOP_LOSS'
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
            
            # New Entry Logic
            
            # Market Regime Filter
            # Only trade if market was bullish today
            if not market_regime.get(today['Date'], False):
                continue

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
            
            # Entry Signal Check
            if score >= min_score:
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
    return results

if __name__ == "__main__":
    results = run_simulation(holding_days=45, min_score=70)
    print(f"\n✅ Simulation Complete. Total Trades: {len(results) if results is not None else 0}")
    
    if results is not None and not results.empty:
        results.to_csv(RESULTS_FILE, index=False)
        print("\n--- Portfolio Simulation Results ---")
        simulation.run_portfolio_simulation(RESULTS_FILE)
        
        import deep_dive
        deep_dive.run_deep_dive(RESULTS_FILE)
    else:
        print("⚠️ No trades generated.")
