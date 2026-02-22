
import pandas as pd
import numpy as np
from datetime import timedelta
import random
import copy
import itertools

class WalkForwardOptimizer:
    def __init__(self, df, strategy_func, param_grid):
        """
        Initializes the Walk-Forward Optimizer.
        """
        self.df = df.sort_values('Date').reset_index(drop=True)
        self.strategy_func = strategy_func
        self.param_grid = param_grid
        self.results = []
        
    def generate_slices(self, train_months=24, test_months=12):
        """
        Generates training and testing data slices for walk-forward analysis.
        """
        if self.df.empty:
            return []
            
        start_date = self.df['Date'].min()
        end_date = self.df['Date'].max()
        
        current_start = start_date
        
        slices = []
        while current_start < end_date:
            train_end = current_start + timedelta(days=train_months*30)
            test_end = train_end + timedelta(days=test_months*30)
            
            if train_end >= end_date:
                break
                
            train_df = self.df[(self.df['Date'] >= current_start) & (self.df['Date'] < train_end)].copy()
            
            # Include warm-up data for test slice
            lookback_start = train_end - timedelta(days=400)
            test_df = self.df[(self.df['Date'] >= lookback_start) & (self.df['Date'] < test_end)].copy()
            
            if not test_df.empty and not train_df.empty:
                slices.append({
                    'train': train_df,
                    'test': test_df,
                    'test_start_date': train_end,
                    'period': f"{test_df['Date'].min().strftime('%Y-%m')} to {test_df['Date'].max().strftime('%Y-%m')}"
                })
            
            # Move to next period
            current_start = current_start + timedelta(days=test_months*30) 
            
        return slices

    def calculate_metric(self, trades_df):
        """
        Calculates Geometric Return (Compound Growth) as the performance metric.
        """
        if trades_df is None or trades_df.empty:
            return -1.0 
            
        # Clamp losses to -100%
        pnl = trades_df['pnl'].clip(lower=-1.0)
        
        # Calculate Compound Return
        compound_return = (1 + pnl).prod() - 1
        return compound_return

    def optimize(self, train_df):
        """
        Finds the best parameter set on the training data using Grid Search.
        """
        best_params = None
        best_score = -np.inf
        
        keys, values = zip(*self.param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        for params in combinations:
            try:
                results = self.strategy_func(train_df, **params)
            except Exception as e:
                print(f"Error in strategy execution with params {params}: {e}")
                continue
                
            if results is None or results.empty:
                continue
                
            score = self.calculate_metric(results)
            
            # Penalize insufficient trade count
            trade_count = len(results)
            if trade_count < 5: 
                score = -1.0 
            
            if score > best_score:
                best_score = score
                best_params = params
                
        return best_params

    def run(self):
        """
        Executes the walk-forward analysis across all generated slices.
        """
        slices = self.generate_slices()
        print(f"\n🔄 Starting Walk-Forward Analysis with {len(slices)} periods...")
        
        wf_results = []
        
        for i, s in enumerate(slices):
            print(f"\n--- Period {i+1}: {s['period']} ---")
            
            # Optimize on Training Set
            print("  [1] Optimizing on Training Set...")
            best_params = self.optimize(s['train'])
            
            if best_params:
                print(f"      best_params: {best_params}")
                
                # Test on Out-of-Sample Set
                print("  [2] Testing on Out-of-Sample Set...")
                test_results = self.strategy_func(s['test'], **best_params)
                
                if test_results is not None and not test_results.empty:
                    # Filter results for valid test period
                    test_start_date = s['test_start_date']
                    if 'entry_date' in test_results.columns:
                        test_results = test_results[test_results['entry_date'] >= test_start_date]
                
                if test_results is not None and not test_results.empty:
                    total_return = self.calculate_metric(test_results)
                    win_rate = len(test_results[test_results['pnl'] > 0]) / len(test_results)
                    trade_count = len(test_results)
                    
                    print(f"      Result: Return={total_return:.2%}, WinRate={win_rate:.2%}, Trades={trade_count}")
                    
                    wf_results.append({
                        'period': s['period'],
                        'params': best_params,
                        'return': total_return,
                        'trades': trade_count,
                        'win_rate': win_rate
                    })
                else:
                    print("      Result: No Trades generated in Test period.")
            else:
                print("      Optimization Failed (No profitable params found in Train set)")
                
        return pd.DataFrame(wf_results)


class RobustnessTester:
    def __init__(self, df, strategy_func, base_params):
        """
        Initializes the Robustness Tester.
        """
        self.df = df
        self.strategy_func = strategy_func
        self.base_params = base_params
        
    def calculate_metric(self, trades_df):
        if trades_df is None or trades_df.empty: return -1.0
        pnl = trades_df['pnl'].clip(lower=-1.0)
        return (1 + pnl).prod() - 1

    def run_noise_test(self, iterations=20, noise_level=0.1):
        """
        Tests strategy stability by applying random noise to parameters.
        """
        print(f"\n🎲 Starting Robustness Test ({iterations} iterations)...")
        results = []
        
        # Baseline Run
        print("  Running Baseline...")
        base_res = self.strategy_func(self.df, **self.base_params)
        if base_res is not None:
             results.append({
                'iteration': 'Baseline',
                'params': str(self.base_params),
                'return': self.calculate_metric(base_res),
                'win_rate': len(base_res[base_res['pnl'] > 0]) / len(base_res),
                'trade_count': len(base_res)
            })
        
        for i in range(iterations):
            noisy_params = copy.deepcopy(self.base_params)
            
            # Apply random perturbation to parameters
            for key, val in noisy_params.items():
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    perturbation = random.uniform(-noise_level, noise_level)
                    
                    if isinstance(val, int):
                        noisy_val = int(round(val * (1 + perturbation)))
                        if noisy_val == val and val > 5:
                            noisy_val += random.choice([-1, 1])
                        
                        noisy_params[key] = max(1, noisy_val) 
                    else:
                        noisy_val = val * (1 + perturbation)
                        noisy_params[key] = noisy_val
            
            # Run Strategy with noisy parameters
            res = self.strategy_func(self.df, **noisy_params)
            
            if res is not None and not res.empty:
                results.append({
                    'iteration': i,
                    'params': str(noisy_params),
                    'return': self.calculate_metric(res),
                    'win_rate': len(res[res['pnl'] > 0]) / len(res),
                    'trade_count': len(res)
                })
                
        df_res = pd.DataFrame(results)
        
        # Analyze and Print Statistics
        if not df_res.empty:
            returns = df_res[df_res['iteration'] != 'Baseline']['return']
            
            if not returns.empty:
                mean_ret = returns.mean()
                std_ret = returns.std()
                min_ret = returns.min()
                max_ret = returns.max()
                
                print("\n--- Robustness Statistics ---")
                print(f"Mean Return: {mean_ret:.2%}")
                print(f"Std Dev: {std_ret:.2%}")
                print(f"Min Return: {min_ret:.2%}")
                print(f"Max Return: {max_ret:.2%}")
                
                if std_ret > 0:
                    stability = mean_ret / std_ret
                    print(f"Stability Score: {stability:.2f} (Higher is better, >1.0 is good)")
                else:
                    print("Stability Score: Infinite (No variation)")
            
        return df_res
