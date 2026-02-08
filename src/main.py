import sys
import os
import time
import random
import schedule
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Determine local directory and add to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config 
# from core import database # REMOVED: Direct DB access
from core import analiz
from core.rabbitmq_manager import RabbitMQManager # ADDED: RabbitMQ
from config import HISSELER

# Import New Engines
from core import trend_engine
from core import scout_engine

MAX_WORKERS = 3
data_lock = threading.Lock()
# Thread-local storage for RabbitMQ connections
thread_local = threading.local()

def get_rabbitmq_connection():
    """Get or create a thread-local RabbitMQ connection."""
    if not hasattr(thread_local, "mq"):
        try:
            thread_local.mq = RabbitMQManager()
        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ for thread: {e}")
            thread_local.mq = None
    return thread_local.mq

def hisse_islemcisi(sembol):
    print(f"Checking: {sembol}...")
    try:
        # Critical Section: TV Datafeed is likely not thread-safe or reusing buffers
        with data_lock:
            sonuc = analiz.veri_cek_ve_hesapla(sembol)
        
        if sonuc:
            # Unpack expanded results from analiz.py
            (fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, 
             adx, dmp, dmn, hacim_orani, 
             swing_high, swing_low, macd_hist_onceki, hacim_onceki, 
             sma50_onceki, rsi_onceki, fiyat_onceki, adx_onceki, atr) = sonuc

            # Prepare data dictionary for trading engine
            data_dict = {
                'sembol': sembol, 'fiyat': fiyat, 'sma50': sma50, 'sma200': sma200,
                'fk': fk, 'pd_dd': pd_dd, 'rsi': rsi,
                'macd_line': macd_line, 'macd_signal': macd_signal, 'macd_hist': macd_hist,
                'adx': adx, 'dmp': dmp, 'dmn': dmn, 'hacim_orani': hacim_orani,
                'swing_low': swing_low, 'macd_hist_onceki': macd_hist_onceki,
                'hacim_onceki': hacim_onceki, 'sma50_onceki': sma50_onceki,
                'rsi_onceki': rsi_onceki, 'fiyat_onceki': fiyat_onceki, 
                'adx_onceki': adx_onceki, 'atr': atr
            }

            # --- HYBRID STRATEGY SELECTION ---
            strategy = "NONE"
            if sma50 > sma200:
                strategy = "TREND"
                signal, score, stop_price, target_price = trend_engine.evaluate_stock(data_dict)
            else:
                strategy = "SCOUT"
                signal, score, stop_price, target_price = scout_engine.evaluate_stock(data_dict)

            # --- PREPARE PAYLOAD ---
            payload = {
                "Sembol": sembol,
                "Fiyat": fiyat,
                "Sma50": sma50,
                "Sma200": sma200,
                "Fk": fk,
                "PdDd": pd_dd,
                "Rsi": rsi,
                "MacdLine": macd_line,
                "MacdSignal": macd_signal,
                "MacdHist": macd_hist,
                "Adx": adx,
                "Dmp": dmp,
                "Dmn": dmn,
                "HacimOrani": hacim_orani,
                "Signal": signal,
                "Score": score,
                "StopPrice": stop_price,
                "TargetPrice": target_price,
                "MacdHistOnceki": macd_hist_onceki,
                "HacimOnceki": hacim_onceki,
                "FiyatOnceki": fiyat_onceki,
                "RsiOnceki": rsi_onceki,
                "AdxOnceki": adx_onceki,
                "Atr": atr,
                "Strategy": strategy,
                "SonGuncelleme": time.strftime('%Y-%m-%dT%H:%M:%S') 
            }
            
            # --- SEND TO RABBITMQ (Optimized) ---
            try:
                # Use thread-local connection
                mq = get_rabbitmq_connection()
                if mq:
                    mq.publish(payload)
                    # Do NOT close here, keep it open for reuse
                    # print(f"🐰 Published to RabbitMQ: {sembol}")
                else:
                    print(f"⚠️ Skipping RabbitMQ publish for {sembol} (No Connection)")

            except Exception as e:
                print(f"⚠️ RabbitMQ Error ({sembol}): {e}")

            print(f"✅ {sembol} [{strategy}] -> Signal: {signal} | Score: {score}")
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
            print("⏳ Bir sonraki güncelleme için 1 gün bekleniyor...") 
            time.sleep(86400) 
        except KeyboardInterrupt:
            print("\n🛑 Program durduruldu.")
            break
        except Exception as e:
            print(f"💥 Kritik Döngü Hatası: {e}")
            time.sleep(10)