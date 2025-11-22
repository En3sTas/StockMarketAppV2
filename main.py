# main.py
from config import HISSELER
import analiz
import database
import time

def sistemi_calistir():
    print("🚀 Borsa Robotu Başlatılıyor...")
    
    for sembol in HISSELER:
        print(f"🔍 {sembol} inceleniyor...")
        
        # 1. Analiz modülüne işi yaptır
        sonuc = analiz.veri_cek_ve_hesapla(sembol)
        
        if sonuc:
            fiyat, sma50, sma200 ,fk, pd_dd,rsi,macd_line,macd_signal,macd_hist,buyume_orani = sonuc
            
            # 2. Database modülüne kaydettir
            database.veriyi_kaydet(sembol, fiyat, sma50, sma200,fk,pd_dd,rsi,macd_line,macd_signal,macd_hist,buyume_orani)
        else:
            print(f"⚠️ {sembol} için veri alınamadı.")
            
    print("🏁 Döngü tamamlandı.")

if __name__ == "__main__":
    # İstersen bunu sonsuz döngüye alıp her 15 dakikada bir çalıştırabilirsin
    while True:
        sistemi_calistir()
        print("⏳ 15 dakika bekleniyor...")
        time.sleep(900) # 900 saniye = 15 dakika