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
#----------BÜYÜME ANALİZİ (YENİ)-----------#
def buyume_orani_hesapla(hisse):
    """
    Önce ÇEYREKLİK (Quarterly) büyümeye bakar (Son Çeyrek vs Geçen Sene Aynı Çeyrek).
    Veri yoksa YILLIK (Annual) büyümeye döner.
    """
    try:
        # --- PLAN A: ÇEYREKLİK (Son Çeyrek vs 1 Yıl Önceki Çeyrek) ---
        ceyrek_tablo = hisse.quarterly_income_stmt
        
        if not ceyrek_tablo.empty and 'Net Income' in ceyrek_tablo.index:
            net_kar_serisi = ceyrek_tablo.loc['Net Income']
            
            # Bize en az 5 veri lazım ki (0. indeks) ile (4. indeks yani geçen sene aynı çeyrek) kıyaslayalım
            # yfinance bazen 4 veri döner, o zaman kıyaslayamayız.
            if len(net_kar_serisi) >= 5:
                bu_ceyrek = net_kar_serisi.iloc[0]      # En son açıklanan (Örn: 2025 Q3)
                gecen_sene_ceyrek = net_kar_serisi.iloc[4] # 1 sene öncesi (Örn: 2024 Q3)

                if gecen_sene_ceyrek != 0:
                    buyume = ((bu_ceyrek - gecen_sene_ceyrek) / abs(gecen_sene_ceyrek)) * 100
                    return buyume

        # --- PLAN B: YILLIK (Veri yetersizse buraya düşer) ---
        yillik_tablo = hisse.income_stmt
        if not yillik_tablo.empty and 'Net Income' in yillik_tablo.index:
            net_kar_serisi = yillik_tablo.loc['Net Income']
            
            if len(net_kar_serisi) >= 2:
                bu_sene = net_kar_serisi.iloc[0]
                gecen_sene = net_kar_serisi.iloc[1]

                if gecen_sene != 0:
                    buyume = ((bu_sene - gecen_sene) / abs(gecen_sene)) * 100
                    return buyume

        return 0

    except Exception as e:
        # Hata olursa sessizce 0 dön
        return 0
    #-----------------------------------------#
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
        #----------#
        buyume_orani = buyume_orani_hesapla(hisse)
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
        if pd.isna(buyume_orani): buyume_orani = 0
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
            float(buyume_orani)
        )

    except Exception as e:
        print(f"❌ Analiz Hatası ({sembol}): {e}")
        return None