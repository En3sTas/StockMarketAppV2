# database.py
import psycopg2
from config import DB_AYARLARI

def baglanti_kur():
    return psycopg2.connect(**DB_AYARLARI)

def veriyi_kaydet(sembol, fiyat, sma50, sma200,fk,pd_dd):
    try:
        conn = baglanti_kur()
        cursor = conn.cursor()
        
        # Temiz sembol adı (THYAO.IS -> THYAO)
        temiz_sembol = sembol.replace(".IS", "")

        sql = """
        INSERT INTO Hisseler (sembol, fiyat, sma_50, sma_200, fk, pd_dd, son_guncelleme)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (sembol) 
        DO UPDATE SET 
            fiyat = EXCLUDED.fiyat,
            sma_50 = EXCLUDED.sma_50,
            sma_200 = EXCLUDED.sma_200,
            fk = EXCLUDED.fk,
            pd_dd = EXCLUDED.pd_dd,
            son_guncelleme = EXCLUDED.son_guncelleme;
        """
        cursor.execute(sql, (temiz_sembol, fiyat, sma50, sma200,fk,pd_dd))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ {temiz_sembol} veritabanına kaydedildi.")
    except Exception as e:
        print(f"❌ Veritabanı Hatası ({sembol}): {e}")