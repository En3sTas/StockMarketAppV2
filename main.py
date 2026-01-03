from config import HISSELER
import analiz
import database
import time
import random
from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 3

def hisse_islemcisi(sembol):
    print(f"Checking: {sembol}...")
    try:
        sonuc = analiz.veri_cek_ve_hesapla(sembol)
        if sonuc:
            fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani = sonuc
            database.veriyi_kaydet(sembol, fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani)
            print(f"✅ {sembol} SUCCESS!")
            time.sleep(random.uniform(0.5, 1.5))
            return None
        else:
            print(f"⚠️ {sembol} returned empty -> Moved to next round.")
            return sembol 

    except Exception as e:
        print(f"❌ Error ({sembol}): {e} -> Moved to next round.")
        return sembol

def sistemi_isit():
    """Sistemi başlatmadan önce bağlantıları ısıtır."""
    print("🔥 Sistem ısıtılıyor (Connection Warm-up)...")
    try:
        # Rastgele güçlü bir hisse ile test isteği atıyoruz
        analiz.veri_cek_ve_hesapla("THYAO") 
        print("✅ Sistem ısındı ve kullanıma hazır!")
    except Exception as e:
        print(f"⚠️ Isınma sırasında hata (önemsiz): {e}")
    time.sleep(2)

def sistemi_calistir():
    baslangic = time.time()
    print(f"🚀 Stock Market Robot (3 Worker - Infinity mode)...")
    kuyruk = HISSELER.copy()
    tur_sayisi = 1
    while len(kuyruk) > 0:
        print(f"\n🔄 ROUND {tur_sayisi} STARTING | Remaining Stocks: {len(kuyruk)}")
        yeni_kuyruk = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            sonuclar = executor.map(hisse_islemcisi, kuyruk)
            for sonuc in sonuclar:
                if sonuc is not None:
                    yeni_kuyruk.append(sonuc)
        kuyruk = yeni_kuyruk
        if len(kuyruk) > 0:
            print(f"🛑 {len(kuyruk)} stocks failed. Will retry after cooling down...")
            bekleme_suresi = min(tur_sayisi * 5, 60)
            print(f"💤 Cooling down for {bekleme_suresi} seconds...")
            time.sleep(bekleme_suresi)
        tur_sayisi += 1
    bitis = time.time()
    print(f"🏁 CONGRATULATIONS! All stocks completed in {bitis - baslangic:.2f} seconds.")

if __name__ == "__main__":
  
    
    print("🔥 Sistem ısıtılıyor (Connection Warm-up)...")
    time.sleep(5) # Gerçek ısınma süresi (API'nin kendine gelmesi için)
    
    print("✅ Sistem ısındı ve kullanıma hazır!")
    print("🚀 Sistem Başlatılıyor... (Canlı Mod: 60sn)\n")
    
    # --- SONSUZ DÖNGÜ ---  
    while True:
        try:
            sistemi_calistir()
            print("⏳ Bir sonraki güncelleme için 60 saniye bekleniyor...") 
            time.sleep(50000) 
        except KeyboardInterrupt:
            print("\n🛑 Program durduruldu.")
            break
        except Exception as e:
            print(f"💥 Kritik Döngü Hatası: {e}")
            time.sleep(10)