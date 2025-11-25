import yfinance as yf
import pandas as pd
import pandas_ta as ta

#----------RSI-----------#
def rsi_hesapla(df, periyot=14):

    delta = df['Close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # İlk ortalama için SMA
    avg_gain = gain.rolling(window=periyot).mean()
    avg_loss = loss.rolling(window=periyot).mean()
    
    # RMA (Wilder smoothing)
    for i in range(periyot, len(df)):
        avg_gain.iat[i] = (avg_gain.iat[i-1] * (periyot - 1) + gain.iat[i]) / periyot
        avg_loss.iat[i] = (avg_loss.iat[i-1] * (periyot - 1) + loss.iat[i]) / periyot

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

#----------ADX ve DMI Hesaplaması (YENİ)-----------#
def adx_dmi_hesapla(df):
    """ADX, +DI (DMP) ve -DI (DMN) Hesaplar"""
    # pandas_ta ile hesaplama (Standart 14 periyot)
    # Bu fonksiyon bize bir DataFrame döner: ADX_14, DMP_14, DMN_14 sütunları olur
    adx_df = df.ta.adx(high=df['High'], low=df['Low'], close=df['Close'], length=14)
    
    if adx_df is None or adx_df.empty:
        return 0, 0, 0

    # Sütun isimleri bazen kütüphane sürümüne göre değişebilir ama genelde şöyledir:
    # ADX_14, DMP_14, DMN_14
    adx = adx_df.iloc[-1]['ADX_14']
    dmp = adx_df.iloc[-1]['DMP_14'] # Plus DI (+DI)
    dmn = adx_df.iloc[-1]['DMN_14'] # Minus DI (-DI)
    
    return adx, dmp, dmn
#----------HACİM ANALİZİ (YENİ METOD)-----------#
def hacim_analizi(df):
    """
    Son 20 günün hacim ortalamasını (Volume SMA) hesaplar.
    Mevcut hacmi buna böler. (Örn: 2.0 -> Hacim 2 katına çıkmış)
    """
    try:
        # Son 20 günün ortalaması
        vol_sma = df['Volume'].rolling(window=20).mean()
        
        current_vol = df['Volume'].iloc[-1]
        avg_vol = vol_sma.iloc[-1]
        
        # Sıfıra bölünme hatasını önle
        if avg_vol == 0 or pd.isna(avg_vol):
            return 0
            
        oran = current_vol / avg_vol
        return oran
    except:
        return 0

   
    
def veri_cek_ve_hesapla(sembol):
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period="1y")
        
        if df.empty: return None

        guncel_fiyat = df['Close'].iloc[-1]

        df.dropna(subset=['High', 'Low', 'Close', 'Volume'], inplace=True)
        if len(df) < 50: return None
        
        
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
        #----------#
        adx, dmp, dmn = adx_dmi_hesapla(df)
        #---------#
        hacim_orani = hacim_analizi(df)
        #---------#

        
        #----------#
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
        if pd.isna(adx): adx = 0
        if pd.isna(dmp): dmp = 0
        if pd.isna(dmn): dmn = 0
        if pd.isna(hacim_orani): hacim_orani = 0
       
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
            float(macd_hist),
            float(adx), 
            float(dmp),  
            float(dmn),  
            float(hacim_orani),
            
            
        )

    except Exception as e:
        print(f"❌ Analiz Hatası ({sembol}): {e}")
        return None