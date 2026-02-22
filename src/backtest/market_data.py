
import pandas as pd
import numpy as np

def get_market_regime(df, window=200):
    """
    Calculates Market Regime based on an Equal-Weighted Index of all stocks in df.
    Returns a Series (Date -> Boolean) where True = Bullish, False = Bearish.
    Logic: Index Price > MA(200) = Bullish.
    """
    # Ensure data is sorted
    df = df.sort_values(['Symbol', 'Date'])
    
    # 1. Calculate Daily Returns per stock
    df['prev_close'] = df.groupby('Symbol')['Close'].shift(1)
    df['ret'] = (df['Close'] / df['prev_close']) - 1
    
    # 2. Calculate Index Return (Equal Weighted)
    index_returns = df.groupby('Date')['ret'].mean()
    
    # 3. Construct Synthetic Index (Start at 100)
    market_index = (1 + index_returns.fillna(0)).cumprod() * 100
    
    # 4. Calculate Simple Moving Average
    market_sma = market_index.rolling(window=window).mean()
    
    # 5. Determine Regime
    regime = market_index > market_sma
    
    # Clean up temporary columns
    df.drop(columns=['prev_close', 'ret'], inplace=True, errors='ignore')
    
    regime = regime.fillna(False)
    
    return regime
