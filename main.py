from config import HISSELER
import analiz
import database
import time
from concurrent.futures import ThreadPoolExecutor


def hisse_islemcisi(sembol):
    """Tek bir hisse için tüm süreci yöneten fonksiyon"""
    print(f"Checking: {sembol}...") # Hangi hissede olduğunu görelim
    try:
        sonuc = analiz.veri_cek_ve_hesapla(sembol)
        if sonuc:
            # Tuple'ı aç (unpack)
            fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, buyume_orani = sonuc
            
            # Veritabanına yaz
            database.veriyi_kaydet(sembol, fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, buyume_orani)
        else:
            print(f"⚠️ {sembol} verisi boş döndü.")
    except Exception as e:
        print(f"❌ Hata ({sembol}): {e}")

def sistemi_calistir():
    baslangic = time.time()
    print("🚀 Borsa Robotu (Turbo Mod) Başlatılıyor...")

    # ThreadPoolExecutor: Aynı anda 10 işçi çalıştırır.
    # BIST 30 veya 100 listesi üzerinde aynı anda işlem yapar.
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(hisse_islemcisi, HISSELER) # HISSELER yerine BIST_30 kullandık

    bitis = time.time()
    print(f"🏁 Tüm işlemler {bitis - baslangic:.2f} saniyede tamamlandı.")

if __name__ == "__main__":
    while True:
        sistemi_calistir()
        print("⏳ 15 dakika bekleniyor...")
        time.sleep(900)