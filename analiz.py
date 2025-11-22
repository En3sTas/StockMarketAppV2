import yfinance as yf
import pandas as pd

def veri_cek_ve_hesapla(sembol):
    """
    Bir hissenin teknik (SMA) ve temel (F/K, PD/DD) verilerini çeker.
    Dönüş: (fiyat, sma50, sma200, fk, pd_dd) demeti.
    """
    try:
        # 1. Hisse Bağlantısı
        hisse = yf.Ticker(sembol)
        
        # ---------------------------
        # BÖLÜM A: TEKNİK ANALİZ (Grafik Verileri)
        # ---------------------------
        # Son 1 yıllık veriyi çekiyoruz (SMA 200 hesaplayabilmek için en az 200 gün lazım)
        df = hisse.history(period="1y")
        
        if df.empty:
            print(f"⚠️ Veri boş geldi: {sembol}")
            return None

        # Güncel Fiyat (Listenin sonundaki 'Close' değeri)
        guncel_fiyat = df['Close'].iloc[-1]

        # Hareketli Ortalamaları Hesapla (Pandas ile sihirbazlık)
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Son günün ortalamalarını al
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]

        # ---------------------------
        # BÖLÜM B: TEMEL ANALİZ (Bilanço Verileri)
        # ---------------------------
        # hisse.info çok büyük bir sözlüktür, içinden cımbızla veri çekeceğiz.
        bilgi = hisse.info
        
        # .get() metodu HAYAT KURTARIR. 
        # Eğer veri yoksa hata verme, yerine 0 koy demektir.
        fk_orani = bilgi.get('trailingPE', 0)    # F/K (Price to Earnings)
        pd_dd = bilgi.get('priceToBook', 0)      # PD/DD (Price to Book)

        # ---------------------------
        # BÖLÜM C: TEMİZLİK VE PAKETLEME
        # ---------------------------
        # Veritabanı NaN (Not a Number) sevmez, onları 0'a çevirelim.
        if pd.isna(sma_50): sma_50 = 0
        if pd.isna(sma_200): sma_200 = 0
        if pd.isna(fk_orani): fk_orani = 0
        if pd.isna(pd_dd): pd_dd = 0

       

        # Tüm verileri SAF PYTHON float tipine çevirip gönderiyoruz
        return (
            float(guncel_fiyat), 
            float(sma_50), 
            float(sma_200), 
            float(fk_orani), 
            float(pd_dd)
        )

    except Exception as e:
        print(f"❌ Analiz Hatası ({sembol}): {e}")
        return None