from tvDatafeed import TvDatafeed, Interval
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

print("🔗 Connecting to data providers...")

try:
    tv = TvDatafeed()
    print("✅ Connection successful.")
except:
    print("⚠️ Initial connection error, retrying...")
    time.sleep(3)
    tv = TvDatafeed()

def hacim_analizi(df):
    try:
        vol_sma = df['Volume'].rolling(window=20).mean()
        current_vol = df['Volume'].iloc[-1]
        avg_vol = vol_sma.iloc[-1]
        
        if avg_vol == 0 or pd.isna(avg_vol): return 0.0
        return float(current_vol / avg_vol)
    except:
        return 0.0

def safe_float(val):
    if pd.isna(val) or val is None: return 0.0
    return float(val)

def tv_veri_cek_retry(symbol, retries=3):
    for i in range(retries):
        try:
            df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_daily, n_bars=5000)
            return df
        except Exception as e:
            hata_mesaji = str(e)
            if "429" in hata_mesaji:
                wait_time = (i + 1) * 5
                print(f"⚠️ Rate limit (429) - waiting {wait_time} seconds for {symbol}...")
                time.sleep(wait_time)
            else:
                print(f"❌ Data Error ({symbol}): {e}")
                return None
    return None

def veri_cek_ve_hesapla(sembol):
    try:
      
        sembol = sembol.upper().strip()
        tv_symbol = sembol.replace(".IS", "")
        
        if ".IS" not in sembol:
            yf_symbol = sembol + ".IS"
        else:
            yf_symbol = sembol

       
        df = tv_veri_cek_retry(tv_symbol)
        
        if df is None or df.empty:
            return None

        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

        if len(df) < 200: return None

        guncel_fiyat = df['Close'].iloc[-1]

        fk_orani = 0.0
        pd_dd = 0.0
        
        # YFinance Retry Mekanizması Eklendi
        for _ in range(3):
            try:
                info = yf.Ticker(yf_symbol).info
                if info:
                    fk_orani = safe_float(info.get('trailingPE', 0))
                    pd_dd = safe_float(info.get('priceToBook', 0))
                    break
            except:
                time.sleep(1)
                continue

       
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.adx(length=14, append=True)

        return (
            safe_float(guncel_fiyat), 
            safe_float(df['SMA_50'].iloc[-1]),
            safe_float(df['SMA_200'].iloc[-1]),
            fk_orani, 
            pd_dd, 
            safe_float(df['RSI_14'].iloc[-1]),
            safe_float(df['MACD_12_26_9'].iloc[-1]),
            safe_float(df['MACDs_12_26_9'].iloc[-1]),
            safe_float(df['MACDh_12_26_9'].iloc[-1]),
            safe_float(df['ADX_14'].iloc[-1]),
            safe_float(df['DMP_14'].iloc[-1]), 
            safe_float(df['DMN_14'].iloc[-1]), 
            hacim_analizi(df)
        )

    except Exception as e:
        print(f"❌ General Code Error ({sembol}): {e}")
        return None

if __name__ == "__main__":
    print(veri_cek_ve_hesapla("HEKTS"))