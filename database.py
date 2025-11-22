# database.py
import psycopg2
from config import DB_AYARLARI

def baglanti_kur():
    return psycopg2.connect(**DB_AYARLARI)

def veriyi_kaydet(sembol, fiyat, sma50, sma200,fk,pd_dd,rsi,macd_line,macd_signal,macd_hist,buyume_orani):
    try:
        conn = baglanti_kur()
        cursor = conn.cursor()
        
        # Temiz sembol adı (THYAO.IS -> THYAO)
        temiz_sembol = sembol.replace(".IS", "")

        sql = """
        INSERT INTO Hisseler (sembol, fiyat, sma_50, sma_200, fk, pd_dd,rsi,macd_line,macd_signal,macd_hist,buyume_orani, son_guncelleme)
        VALUES (%s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s, NOW())
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
            buyume_orani= EXCLUDED.buyume_orani,
            son_guncelleme = EXCLUDED.son_guncelleme;
        """
        cursor.execute(sql, (temiz_sembol, fiyat, sma50, sma200,fk,pd_dd,rsi,macd_line,macd_signal,macd_hist,buyume_orani))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ {temiz_sembol} veritabanına kaydedildi.(RSI: {rsi:.2f}),(MACD Hist: {macd_hist:.2f}),(Büyüme Oranı: {buyume_orani:.2f}%)")
    except Exception as e:
        print(f"❌ Veritabanı Hatası ({sembol}): {e}")