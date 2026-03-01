import sys
import os
import time
import random
import schedule
import json

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config 
from core import analiz
from core.rabbitmq_manager import RabbitMQManager 
from config import HISSELER
from core import telegram_notifier
from core.notification_guard import should_notify

# Engines
from core import trend_engine
from core import pro_engine

# ─────────────────────────────────────────────────────────
# UNIFIED CONVICTION ENGINE
# Merges Trend/Scout base_score + Pro Engine tags into a
# single unified_score and conviction level.
# ─────────────────────────────────────────────────────────

# Tag classification constants
POSITIVE_TAGS = {
    "Strong Trend", "Whale Volume", "Smart Money In",
    "Above VWMA", "BB Squeeze", "Long-Term Bull"
}
WARNING_TAGS = {
    "Overbought ⚠️", "MFI Overbought", "Vol Divergence",
    "Tiring Trend", "RSI Reversal", "Weak Trend"
}
DANGER_TAGS = {
    "Falling Knife", "High Sell Vol", "Bear Regime Risk"
}

REGIME_MULTIPLIER = {"BULL": 1.0, "SIDEWAYS": 0.85, "BEAR": 0.6}


def calculate_unified_score(base_score: int, pro_tags: list, regime: str, signal: str):
    """
    Calculates UnifiedScore and Conviction from Trend/Scout base_score
    combined with Pro Engine tags and market regime.

    Returns (unified_score: int, unified_signal: str, conviction: str)
    """
    # 1. Count tag categories
    positive_count = sum(1 for t in pro_tags if any(pt in t for pt in POSITIVE_TAGS))
    warning_count  = sum(1 for t in pro_tags if any(wt in t for wt in WARNING_TAGS))
    danger_count   = sum(1 for t in pro_tags if any(dt in t for dt in DANGER_TAGS))

    # 2. Pro modifier: +5 per positive, -5 per warning, -15 per danger
    pro_modifier = (positive_count * 5) + (warning_count * -5) + (danger_count * -15)

    # 3. Apply regime multiplier
    multiplier = REGIME_MULTIPLIER.get(regime, 0.85)
    raw_score = base_score + pro_modifier
    raw_score = max(0, min(100, raw_score))  # clamp before multiplier
    unified_score = int(raw_score * multiplier)
    unified_score = max(0, min(100, unified_score))

    # 4. Determine base unified signal
    danger_tag_names = [t for t in pro_tags if any(dt in t for dt in DANGER_TAGS)]
    has_falling_knife   = any("Falling Knife" in t for t in pro_tags)
    has_bear_regime     = any("Bear Regime Risk" in t for t in pro_tags)
    has_high_sell_vol   = any("High Sell Vol" in t for t in pro_tags)
    has_overbought      = any("Overbought" in t for t in pro_tags)
    has_mfi_overbought  = any("MFI Overbought" in t for t in pro_tags)

    if unified_score >= 80 and danger_count == 0:
        unified_signal = "STRONG_BUY"
    elif unified_score >= 65:
        unified_signal = "BUY"
    elif unified_score >= 50:
        unified_signal = "WATCH"
    else:
        unified_signal = "NO_TRADE"

    # 5. Veto rules (override signal downward)
    # Veto 1: Falling Knife → NO_TRADE no matter what
    if has_falling_knife:
        unified_signal = "NO_TRADE"
    # Veto 2: Bear Regime Risk + low score → max WATCH
    elif has_bear_regime and base_score < 70:
        if unified_signal in ("STRONG_BUY", "BUY"):
            unified_signal = "WATCH"
    # Veto 3: Double overbought → max WATCH
    elif has_overbought and has_mfi_overbought:
        if unified_signal in ("STRONG_BUY", "BUY"):
            unified_signal = "WATCH"
    # Veto 4: High Sell Vol → max WATCH
    if has_high_sell_vol:
        if unified_signal in ("STRONG_BUY", "BUY"):
            unified_signal = "WATCH"

    # 6. Conviction level
    if base_score >= 70 and positive_count >= 3 and danger_count == 0 and regime != "BEAR":
        conviction = "DIAMOND"
    elif base_score >= 65 and positive_count >= 2 and danger_count == 0:
        conviction = "GOLD"
    elif base_score >= 50 and positive_count >= 1:
        conviction = "SILVER"
    else:
        conviction = "BRONZE"

    return unified_score, unified_signal, conviction

# Global Market Context
market_index_df = None
# Global RabbitMQ Instance
global_mq = None

def get_rabbitmq_connection():
    """
    Retrieves or creates a global RabbitMQ connection.
    """
    global global_mq
    if global_mq is None:
        try:
            global_mq = RabbitMQManager()
        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ: {e}")
            global_mq = None
    return global_mq

def hisse_islemcisi(sembol):
    """
    Processes a single stock symbol sequentially.
    """
    print(f"Checking: {sembol}...")
    try:
        # Analiz modülünü çağır
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

            # Strategy Selection — sadece TREND Engine
            strategy = "TREND"
            signal, score, stop_price, target_price = trend_engine.evaluate_stock(data_dict)

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
                risk_distance = fiyat - stop_price
                stop_price = fiyat - (risk_distance * 0.5)
                reward_distance = target_price - fiyat
                target_price = fiyat + (reward_distance * 0.6)
                stop_price = round(stop_price, 2)
                target_price = round(target_price, 2)

            # Unified Conviction Engine
            unified_score, unified_signal, conviction = calculate_unified_score(
                base_score=score,
                pro_tags=pro_tags,
                regime=pro_regime,
                signal=signal
            )

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
                "ConfidenceScore": pro_conf_score,
                # ── Unified Conviction Engine ──
                "UnifiedScore": unified_score,
                "Conviction": conviction
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

            # ── Telegram Bildirimleri (Guard Kontrollü) ───────────────
            try:
                # Tür 1: Trend Hunter — BUY veya STRONG_BUY
                if signal in ("BUY", "STRONG_BUY"):
                    if should_notify(f"{sembol}_trend", signal, score):
                        if telegram_notifier.send_trend_notification(payload):
                            print(f"📲 Telegram Trend gönderildi: {sembol}")

                # Tür 2: Smart Picks — unified_signal BUY veya STRONG_BUY
                if unified_signal in ("BUY", "STRONG_BUY"):
                    if should_notify(f"{sembol}_smart", unified_signal, unified_score):
                        if telegram_notifier.send_smart_picks_notification(payload):
                            print(f"📲 Telegram Smart Picks gönderildi: {sembol}")
            except Exception as e:
                print(f"⚠️ Telegram Hata ({sembol}): {e}")
            # ────────────────────────────────────────────────────────

            print(f"✅ {sembol} [{strategy}] -> Signal: {signal} | Score: {score} | Unified: {unified_score} [{conviction}] | Pro: {pro_main_strategy}")
            time.sleep(random.uniform(0.5, 1.5))
            return None # Başarılı olduğu için None döndür (hata listesine eklenmesin)
        else:
            print(f"⚠️ {sembol} returned empty -> Will retry.")
            return sembol # Başarısız, tekrar denenecek
            
    except Exception as e:
        print(f"❌ Error ({sembol}): {e} -> Will retry.")
        return sembol # Başarısız, tekrar denenecek

def sistemi_isit():
    print("🔥 Warming up system connection...")
    try:
        # Test amaçlı tek bir analiz
        analiz.veri_cek_ve_hesapla("THYAO") 
        get_rabbitmq_connection() # MQ bağlantısını da test et
        print("✅ System ready!")
    except Exception as e:
        print(f"⚠️ Warm-up error (minor): {e}")
    time.sleep(2)

def sistemi_calistir():
    """
    Main execution cycle. SEQUENTIAL processing.
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
    
    print(f"🚀 Stock Market Robot (SINGLE WORKER MODE)...")
    kuyruk = HISSELER.copy()
    tur_sayisi = 1
    
    # Kuyruk bitene kadar dön
    while len(kuyruk) > 0:
        print(f"\n🔄 ROUND {tur_sayisi} STARTING | Remaining Stocks: {len(kuyruk)}")
        hatali_hisseler = []
        
        # --- TEK WORKER DÖNGÜSÜ (Veri karışmasını %100 engeller) ---
        for sembol in kuyruk:
            sonuc = hisse_islemcisi(sembol)
            # Eğer fonksiyon sembolü geri döndürdüyse hata var demektir, listeye ekle
            if sonuc is not None:
                hatali_hisseler.append(sonuc)
        
        kuyruk = hatali_hisseler
        
        if len(kuyruk) > 0:
            print(f"🛑 {len(kuyruk)} stocks failed. Will retry after cooling down...")
            bekleme_suresi = min(tur_sayisi * 5, 30) # Bekleme süresini biraz kısalttım
            print(f"💤 Cooling down for {bekleme_suresi} seconds...")
            time.sleep(bekleme_suresi)
        
        tur_sayisi += 1
        
    bitis = time.time()
    print(f"🏁 CONGRATULATIONS! All stocks completed in {bitis - baslangic:.2f} seconds.")

    # ── Excel Geçmiş Raporu Güncelle ─────────────────────────────────────────
    try:
        from excel_exporter import export_signal_history
        export_signal_history()
    except Exception as e:
        print(f"⚠️ Excel export hatası (kritik değil): {e}")


if __name__ == "__main__":
    print("🔥 Warming up system...")
    time.sleep(2)
    sistemi_isit()
    
    print("🚀 Starting System... (Live Mode: 1 Day Loop)\n")
    
    while True:
        try:
            sistemi_calistir()
            print("⏳ Waiting 1 minutes for next update...") 
            # 24 Saat bekleme (veya schedule kütüphanesi ile belirli saate ayarlayabilirsin)
            time.sleep(60) 
        except KeyboardInterrupt:
            print("\n🛑 Program stopped.")
            break
        except Exception as e:
            print(f"💥 Critical Loop Error: {e}")
            time.sleep(10)