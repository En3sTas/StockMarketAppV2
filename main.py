from config import HISSELER
import analiz
import database
import time
import random
from concurrent.futures import ThreadPoolExecutor

# İŞÇİ SAYISI (Hem ilk tur hem telafi için sabit)
MAX_WORKERS = 3 

def hisse_islemcisi(sembol):
    """
    İşlem başarılıysa -> None döner.
    Başarısızsa -> Sembolü geri döner (Listeye tekrar girmesi için).
    """
    print(f"Checking: {sembol}...") 
    try:
        sonuc = analiz.veri_cek_ve_hesapla(sembol)
        
        if sonuc:
            # Veriyi kaydet
            fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani = sonuc
            database.veriyi_kaydet(sembol, fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani)
            
            print(f"✅ {sembol} BAŞARILI.")
            time.sleep(random.uniform(0.5, 1.5)) # Kısa mola
            return None # Listeden düş
        else:
            # Veri boş döndüyse hata sayılır
            print(f"⚠️ {sembol} boş döndü -> Sonraki tura kaldı.")
            return sembol 

    except Exception as e:
        print(f"❌ Hata ({sembol}): {e} -> Sonraki tura kaldı.")
        return sembol

def sistemi_calistir():
    baslangic = time.time()
    print(f"🚀 Borsa Robotu Başlatılıyor (3 Worker - Sonsuz Döngü Modu)...")

    # İlk başta kuyrukta tüm hisseler var
    kuyruk = HISSELER.copy() 
    tur_sayisi = 1

    # KUYRUK BİTENE KADAR DÖN (WHILE LOOP)
    while len(kuyruk) > 0:
        print(f"\n🔄 TUR {tur_sayisi} BAŞLIYOR | Kalan Hisse: {len(kuyruk)}")
        
        yeni_kuyruk = [] # Bu turda başarısız olanlar buraya birikecek

        # 3 Worker ile kuyruğu erit
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            sonuclar = executor.map(hisse_islemcisi, kuyruk)
            
            for sonuc in sonuclar:
                if sonuc is not None:
                    # Başarısız olanı yeni kuyruğa ekle
                    yeni_kuyruk.append(sonuc)
        
        # Tur bitti, durumu değerlendir
        kuyruk = yeni_kuyruk # Kalanları ana kuyruğa ata
        
        if len(kuyruk) > 0:
            print(f"🛑 {len(kuyruk)} hisse başarısız oldu. Dinlenip tekrar denenecek...")
            
            # Dinamik Bekleme: Tur sayısı arttıkça bekleme süresini artır (Ban yememek için)
            # 1. Tur sonu: 5sn, 2. Tur sonu: 10sn, 3. Tur sonu: 15sn...
            bekleme_suresi = min(tur_sayisi * 5, 60) 
            print(f"💤 {bekleme_suresi} saniye soğuma süresi...")
            time.sleep(bekleme_suresi)
            
        tur_sayisi += 1

    bitis = time.time()
    print(f"🏁 TEBRİKLER! Tüm liste {bitis - baslangic:.2f} saniyede eksiksiz tamamlandı.")

if __name__ == "__main__":
    while True:
        try:
            sistemi_calistir()
            print("⏳ 15 dakika bekleniyor...")
            time.sleep(900)
        except KeyboardInterrupt:
            print("\n🛑 Program durduruldu.")
            break
        except Exception as e:
            print(f"💥 Kritik Döngü Hatası: {e}")
            time.sleep(60)