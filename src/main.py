
import sys
import os
import time
import random
import schedule
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config 
from core import analiz
from core.rabbitmq_manager import RabbitMQManager 
from config import HISSELER

# Engines
from core import trend_engine
from core import scout_engine
from core import pro_engine

MAX_WORKERS = 3
thread_local = threading.local()

# Global Market Context
market_index_df = None

def get_rabbitmq_connection():
    """
    Retrieves or creates a thread-local RabbitMQ connection.
    """
    if not hasattr(thread_local, "mq"):
        try:
            thread_local.mq = RabbitMQManager()
        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ for thread: {e}")
            thread_local.mq = None
    return thread_local.mq

def hisse_islemcisi(sembol):
    """
    Processes a single stock symbol: fetches data, runs strategies, and publishes results.
    """
    print(f"Checking: {sembol}...")
    try:
        # Each call fetches independent data for a different symbol — no lock needed
        sonuc = analiz.veri_cek_ve_hesapla(sembol)
        
        if sonuc:
            (fiyat, sma50, sma200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, 
             adx, dmp, dmn, hacim_orani, 
             swing_high, swing_low, macd_hist_onceki, hacim_onceki, 
             sma50_onceki, rsi_onceki, fiyat_onceki, adx_onceki, atr,
             current_df) = sonuc

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

            # Strategy Selection (Legacy)
            strategy = "NONE"
            if sma50 > sma200:
                strategy = "TREND"
                signal, score, stop_price, target_price = trend_engine.evaluate_stock(data_dict)
            else:
                strategy = "SCOUT"
                signal, score, stop_price, target_price = scout_engine.evaluate_stock(data_dict)

            # Pro Engine Analysis (Institutional)
            pro_result = pro_engine.evaluate_stock(current_df, market_index_df)
            
            pro_tags = []
            pro_main_strategy = "NEUTRAL"
            pro_regime = "SIDEWAYS"
            pro_conf_score = 0
            
            if pro_result:
                pro_tags = pro_result.get('tags', [])
                pro_main_strategy = pro_result.get('main_strategy', 'NEUTRAL')
                pro_regime = pro_result.get('market_regime', 'SIDEWAYS')
                pro_conf_score = pro_result.get('confidence_score', 0)

            # Fix #6: Regime-Aware Stop-Loss Adjustment
            if pro_regime == "BEAR" and stop_price > 0:
                # Tighten stop in bear regime (move stop closer to entry)
                risk_distance = fiyat - stop_price
                stop_price = fiyat - (risk_distance * 0.5)  # Cut risk in half
                # Reduce target in bear regime
                reward_distance = target_price - fiyat
                target_price = fiyat + (reward_distance * 0.6)  # Conservative target
                stop_price = round(stop_price, 2)
                target_price = round(target_price, 2)

            # Construct Payload
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
                "SonGuncelleme": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "Tags": pro_tags,
                "MainStrategy": pro_main_strategy,
                "MarketRegime": pro_regime,
                "ConfidenceScore": pro_conf_score
            }
            
            # Publish to RabbitMQ
            try:
                mq = get_rabbitmq_connection()
                if mq:
                    mq.publish(payload)
                else:
                    print(f"⚠️ Skipping RabbitMQ publish for {sembol} (No Connection)")

            except Exception as e:
                print(f"⚠️ RabbitMQ Error ({sembol}): {e}")

            print(f"✅ {sembol} [{strategy}] -> Signal: {signal} | Score: {score} | Pro: {pro_main_strategy}")
            time.sleep(random.uniform(0.5, 1.5))
            return None
        else:
            print(f"⚠️ {sembol} returned empty -> Moved to next round.")
            return sembol 
            
    except Exception as e:
        print(f"❌ Error ({sembol}): {e} -> Moved to next round.")
        return sembol

def sistemi_isit():
    """
    Warms up the system connection before starting the main loop.
    """
    print("🔥 Warming up system connection...")
    try:
        analiz.veri_cek_ve_hesapla("THYAO") 
        print("✅ System ready!")
    except Exception as e:
        print(f"⚠️ Warm-up error (minor): {e}")
    time.sleep(2)

def sistemi_calistir():
    """
    Main execution cycle. Fetches market context and processes all stocks using workers.
    """
    global market_index_df
    baslangic = time.time()
    
    # 1. Fetch Market Context (Index)
    print("🌍 Fetching Global Market Context (XU100)...")
    market_index_df = analiz.get_market_index()
    if market_index_df is not None:
         regime = pro_engine.get_market_regime(market_index_df)[0]
         print(f"🌍 Market Regime Detected: {regime}")
    else:
         print("⚠️ Market Context Unavailable. Creating in isolation.")
    
    print(f"🚀 Stock Market Robot (3 Worker - Infinity mode)...")
    kuyruk = HISSELER.copy()
    tur_sayisi = 1
    
    # Process Queue with Retries
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
    print("🔥 Warming up system...")
    time.sleep(5) 
    
    print("✅ System ready!")
    print("🚀 Starting System... (Live Mode: 60s loop)\n")
    
    # Infinite Loop
    while True:
        try:
            sistemi_calistir()
            print("⏳ Waiting 1 day for next update...") 
            time.sleep(86400) 
        except KeyboardInterrupt:
            print("\n🛑 Program stopped.")
            break
        except Exception as e:
            print(f"💥 Critical Loop Error: {e}")
            time.sleep(10)