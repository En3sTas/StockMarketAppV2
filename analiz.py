import yfinance as yf
import pandas as pd
#----------RSI-----------#
def rsi_hesapla(df, periyot=14):
    """Basit RSI Hesaplaması"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=periyot).mean()
    avg_loss = loss.rolling(window=periyot).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
#----------MACD-----------#
def macd_hesapla(df):
    """MACD (12, 26, 9) Hesaplaması"""
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
  
    macd_line = ema12 - ema26
  
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()

    macd_hist = macd_line - macd_signal
    
    return macd_line, macd_signal, macd_hist
#------------------------#
def veri_cek_ve_hesapla(sembol):
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period="1y")
        
        if df.empty: return None

        guncel_fiyat = df['Close'].iloc[-1]
        
        # SMA Hesapları
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]

        # --- YENİ: RSI Hesabı ---
        df['RSI'] = rsi_hesapla(df)
        rsi_degeri = df['RSI'].iloc[-1]
        # ------------------------
        macd_l, macd_s, macd_h = macd_hesapla(df)
        macd_line = macd_l.iloc[-1]
        macd_signal = macd_s.iloc[-1]
        macd_hist = macd_h.iloc[-1]

        bilgi = hisse.info
        fk_orani = bilgi.get('trailingPE', 0)
        pd_dd = bilgi.get('priceToBook', 0)

        # NaN Temizliği
        if pd.isna(sma_50): sma_50 = 0
        if pd.isna(sma_200): sma_200 = 0
        if pd.isna(fk_orani): fk_orani = 0
        if pd.isna(pd_dd): pd_dd = 0
        if pd.isna(rsi_degeri): rsi_degeri = 0 # RSI boşsa 0 yap
        if pd.isna(macd_line): macd_line = 0
        if pd.isna(macd_signal): macd_signal = 0
        if pd.isna(macd_hist): macd_hist = 0

        # Dönüşe rsi_degeri eklendi (6. eleman)
        return (
            float(guncel_fiyat), 
            float(sma_50), 
            float(sma_200), 
            float(fk_orani), 
            float(pd_dd), 
            float(rsi_degeri),
            float(macd_line), 
            float(macd_signal), 
            float(macd_hist)
        )

    except Exception as e:
        print(f"❌ Analiz Hatası ({sembol}): {e}")
        return None