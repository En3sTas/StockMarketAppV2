
import sys
import os
import pandas as pd
import analysis_core
import backtest_scout
import backtest_trend

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "backtest_data.parquet")

def load_data():
    """
    Loads backtest data, filtering for recent years and specified symbols.
    """
    print(f"📂 Loading Data from {DATA_FILE}...")
    try:
        df = pd.read_parquet(DATA_FILE)
    except Exception as e:
        print(f"DEBUG: read_parquet failed: {e}")
        csv_path = DATA_FILE.replace("parquet", "csv")
        if os.path.exists(csv_path):
             df = pd.read_csv(csv_path)
        else:
            print(f"❌ Data file not found at {DATA_FILE}!")
            sys.exit(1)
            
    df = df.reset_index() 
    if 'Date' not in df.columns and 'datetime' in df.columns:
        df['Date'] = pd.to_datetime(df['datetime'])
    
    # Filter for Speed (Recent Data Only)
    df = df[df['Date'] >= '2020-01-01']
    
    # Filter Symbols (Config or Top Volume)
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config
        if hasattr(config, 'HISSELER'):
            df = df[df['Symbol'].isin(config.HISSELER)]
            print(f"📉 Filtered to {len(config.HISSELER)} symbols from config.")
            print(f"📉 Date range: {df['Date'].min()} to {df['Date'].max()}")
    except ImportError:
        print("⚠️ Config not found, using all symbols.")

    df = df.sort_values(['Symbol', 'Date'])
    return df

def analyze_scout(df):
    print("\n\n" + "="*50)
    print("🔍 ANALYZING SCOUT STRATEGY")
    print("="*50)
    
    # 1. Walk-Forward Analysis
    param_grid = {
        'min_score': [60, 70], 
        'holding_days': [30, 40, 50]
    }
    
    optimizer = analysis_core.WalkForwardOptimizer(df, backtest_scout.run_simulation, param_grid)
    wf_results = optimizer.run()
    
    if not wf_results.empty:
        print("\n📈 Walk-Forward Summary:")
        print(wf_results[['period', 'params', 'return', 'win_rate']].to_string())
    
    # 2. Robustness Test (Noise Injection)
    print("\n\n🛡️ Robustness Test (Noise Injection)")
    base_params = {'min_score': 60, 'holding_days': 40}
    tester = analysis_core.RobustnessTester(df, backtest_scout.run_simulation, base_params)
    robustness_results = tester.run_noise_test(iterations=10, noise_level=0.15) 

def analyze_trend(df):
    print("\n\n" + "="*50)
    print("📈 ANALYZING TREND STRATEGY")
    print("="*50)
    
    # 1. Walk-Forward Analysis
    param_grid = {
        'min_score': [65, 75], 
        'holding_days': [45, 60]
    }
    
    optimizer = analysis_core.WalkForwardOptimizer(df, backtest_trend.run_simulation, param_grid)
    wf_results = optimizer.run()
    
    if not wf_results.empty:
        print("\n📈 Walk-Forward Summary:")
        print(wf_results[['period', 'params', 'return', 'win_rate']].to_string())

    # 2. Robustness Test (Noise Injection)
    print("\n\n🛡️ Robustness Test (Noise Injection)")
    base_params = {'min_score': 70, 'holding_days': 45}
    tester = analysis_core.RobustnessTester(df, backtest_trend.run_simulation, base_params)
    robustness_results = tester.run_noise_test(iterations=10, noise_level=0.15)

if __name__ == "__main__":
    df = load_data()
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = '3'
        
    if choice == '1':
        analyze_scout(df)
    elif choice == '2':
        analyze_trend(df)
    elif choice == '3':
        analyze_scout(df)
        analyze_trend(df)
