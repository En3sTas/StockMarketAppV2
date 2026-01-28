
import psycopg2
from config import DB_AYARLARI

def baglanti_kur():
    return psycopg2.connect(**DB_AYARLARI)
# database.py dosyasının veriyi_kaydet fonksiyonunu güncelleyin:

def veriyi_kaydet(sembol, fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani,
                  signal="NO_TRADE", score=0, stop_price=0, target_price=0, macd_hist_onceki=0, hacim_onceki=0,
                  fiyat_onceki=0, rsi_onceki=0, adx_onceki=0, atr=0, strategy="NONE"):
    try:
        conn = baglanti_kur()
        cursor = conn.cursor()
        temiz_sembol = sembol.replace(".IS", "")

        # SQL Sorgusu Güncellendi: strategy eklendi
        sql = """
        INSERT INTO Hisseler (
            sembol, fiyat, sma_50, sma_200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani, 
            signal, score, stop_price, target_price, macd_hist_onceki, hacim_onceki,
            fiyat_onceki, rsi_onceki, adx_onceki, atr,
            son_guncelleme, strategy
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (sembol) 
        DO UPDATE SET 
            fiyat = EXCLUDED.fiyat,
            sma_50 = EXCLUDED.sma_50,
            sma_200 = EXCLUDED.sma_200,
            fk = EXCLUDED.fk,
            pd_dd = EXCLUDED.pd_dd,
            rsi = EXCLUDED.rsi,
            macd_line = EXCLUDED.macd_line,
            macd_signal = EXCLUDED.macd_signal,
            macd_hist= EXCLUDED.macd_hist,
            adx = EXCLUDED.adx,
            dmp = EXCLUDED.dmp,
            dmn = EXCLUDED.dmn,
            hacim_orani = EXCLUDED.hacim_orani,
            
            signal = EXCLUDED.signal,
            score = EXCLUDED.score,
            stop_price = EXCLUDED.stop_price,
            target_price = EXCLUDED.target_price,
            macd_hist_onceki = EXCLUDED.macd_hist_onceki,
            hacim_onceki = EXCLUDED.hacim_onceki,

            fiyat_onceki = EXCLUDED.fiyat_onceki,  -- Daily Change (Dünkü Kapanış)
            rsi_onceki = EXCLUDED.rsi_onceki,
            adx_onceki = EXCLUDED.adx_onceki,
            atr = EXCLUDED.atr,
            
            son_guncelleme = EXCLUDED.son_guncelleme,
            strategy = EXCLUDED.strategy;
        """
        cursor.execute(sql, (
            temiz_sembol, fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani,
            signal, score, stop_price, target_price, macd_hist_onceki, hacim_onceki,
            fiyat_onceki, rsi_onceki, adx_onceki, atr, strategy
        ))
        conn.commit()
        cursor.close()
        conn.close()
        # Konsola basarken farkı göstermiyoruz ama veritabanına kaydettik.
        print(f"✅ {temiz_sembol} saved. RSI: {rsi:.2f} | ADX: {adx:.2f} | Strategy: {strategy}")
    except Exception as e:
        print(f"❌ Database Error ({sembol}): {e}")