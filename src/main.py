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
from config import STOCKS
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
    multiplier  = REGIME_MULTIPLIER.get(regime, 0.85)
    raw_score   = base_score + pro_modifier
    raw_score   = max(0, min(100, raw_score))   # clamp before multiplier
    unified_score = int(raw_score * multiplier)
    unified_score = max(0, min(100, unified_score))

    # 4. Determine base unified signal
    has_falling_knife  = any("Falling Knife" in t for t in pro_tags)
    has_bear_regime    = any("Bear Regime Risk" in t for t in pro_tags)
    has_high_sell_vol  = any("High Sell Vol" in t for t in pro_tags)
    has_overbought     = any("Overbought" in t for t in pro_tags)
    has_mfi_overbought = any("MFI Overbought" in t for t in pro_tags)

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
    """Retrieves or creates a global RabbitMQ connection."""
    global global_mq
    if global_mq is None:
        try:
            global_mq = RabbitMQManager()
        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ: {e}")
            global_mq = None
    return global_mq


def process_stock(symbol):
    """Processes a single stock symbol: fetch → analyze → publish → notify."""
    print(f"Checking: {symbol}...")
    try:
        result = analiz.fetch_and_calculate(symbol)

        if result:
            (price, sma50, sma200, pe_ratio, pb_ratio, rsi, macd_line, macd_signal, macd_hist,
             adx, dmp, dmn, volume_ratio,
             swing_high, swing_low, macd_hist_prev, volume_prev,
             sma50_prev, rsi_prev, price_prev, adx_prev, atr,
             current_df) = result

            data_dict = {
                'symbol': symbol, 'price': price, 'sma50': sma50, 'sma200': sma200,
                'pe_ratio': pe_ratio, 'pb_ratio': pb_ratio, 'rsi': rsi,
                'macd_line': macd_line, 'macd_signal': macd_signal, 'macd_hist': macd_hist,
                'adx': adx, 'dmp': dmp, 'dmn': dmn, 'volume_ratio': volume_ratio,
                'swing_low': swing_low, 'macd_hist_prev': macd_hist_prev,
                'volume_prev': volume_prev, 'sma50_prev': sma50_prev,
                'rsi_prev': rsi_prev, 'price_prev': price_prev,
                'adx_prev': adx_prev, 'atr': atr
            }

            # Strategy Selection — Trend Engine only
            strategy = "TREND"
            signal, score, stop_price, target_price = trend_engine.evaluate_stock(data_dict)

            # Pro Engine Analysis (Institutional)
            pro_result       = pro_engine.evaluate_stock(current_df, market_index_df)
            pro_tags         = []
            pro_main_strategy = "NEUTRAL"
            pro_regime       = "SIDEWAYS"
            pro_conf_score   = 0

            if pro_result:
                pro_tags          = pro_result.get('tags', [])
                pro_main_strategy = pro_result.get('main_strategy', 'NEUTRAL')
                pro_regime        = pro_result.get('market_regime', 'SIDEWAYS')
                pro_conf_score    = pro_result.get('confidence_score', 0)

            # Regime-Aware Stop-Loss Adjustment
            if pro_regime == "BEAR" and stop_price > 0:
                risk_distance   = price - stop_price
                stop_price      = price - (risk_distance * 0.5)
                reward_distance = target_price - price
                target_price    = price + (reward_distance * 0.6)
                stop_price      = round(stop_price, 2)
                target_price    = round(target_price, 2)

            # Unified Conviction Engine
            unified_score, unified_signal, conviction = calculate_unified_score(
                base_score=score,
                pro_tags=pro_tags,
                regime=pro_regime,
                signal=signal
            )

            # Build JSON payload — keys match C# Stock model (PascalCase)
            payload = {
                "Symbol":          symbol,
                "Price":           price,
                "Sma50":           sma50,
                "Sma200":          sma200,
                "PeRatio":         pe_ratio,
                "PbRatio":         pb_ratio,
                "Rsi":             rsi,
                "MacdLine":        macd_line,
                "MacdSignal":      macd_signal,
                "MacdHist":        macd_hist,
                "Adx":             adx,
                "Dmp":             dmp,
                "Dmn":             dmn,
                "VolumeRatio":     volume_ratio,
                "Signal":          signal,
                "Score":           score,
                "StopPrice":       stop_price,
                "TargetPrice":     target_price,
                "MacdHistPrev":    macd_hist_prev,
                "VolumePrev":      volume_prev,
                "PricePrev":       price_prev,
                "RsiPrev":         rsi_prev,
                "AdxPrev":         adx_prev,
                "Atr":             atr,
                "Strategy":        strategy,
                "LastUpdated":     time.strftime('%Y-%m-%dT%H:%M:%S'),
                "Tags":            pro_tags,
                "MainStrategy":    pro_main_strategy,
                "MarketRegime":    pro_regime,
                "ConfidenceScore": pro_conf_score,
                "UnifiedScore":    unified_score,
                "Conviction":      conviction
            }

            # Publish to RabbitMQ
            try:
                mq = get_rabbitmq_connection()
                if mq:
                    mq.publish(payload)
                else:
                    print(f"⚠️ Skipping RabbitMQ publish for {symbol} (no connection)")
            except Exception as e:
                print(f"⚠️ RabbitMQ error ({symbol}): {e}")

            # Telegram Notifications (guard-controlled)
            try:
                # Type 1: Trend Hunter — BUY or STRONG_BUY
                if signal in ("BUY", "STRONG_BUY"):
                    if should_notify(f"{symbol}_trend", signal, score):
                        if telegram_notifier.send_trend_notification(payload):
                            print(f"📲 Telegram Trend sent: {symbol}")

                # Type 2: Smart Picks — unified_signal BUY or STRONG_BUY
                if unified_signal in ("BUY", "STRONG_BUY"):
                    if should_notify(f"{symbol}_smart", unified_signal, unified_score):
                        if telegram_notifier.send_smart_picks_notification(payload):
                            print(f"📲 Telegram Smart Picks sent: {symbol}")
            except Exception as e:
                print(f"⚠️ Telegram error ({symbol}): {e}")

            print(f"✅ {symbol} [{strategy}] -> Signal: {signal} | Score: {score} | Unified: {unified_score} [{conviction}] | Pro: {pro_main_strategy}")
            time.sleep(random.uniform(0.5, 1.5))
            return None   # Success — don't add to retry queue

        else:
            print(f"⚠️ {symbol} returned empty → will retry.")
            return symbol   # Failure — retry

    except Exception as e:
        print(f"❌ Error ({symbol}): {e} → will retry.")
        return symbol   # Failure — retry


def warmup():
    print("🔥 Warming up system connection...")
    try:
        analiz.fetch_and_calculate("THYAO")
        get_rabbitmq_connection()
        print("✅ System ready!")
    except Exception as e:
        print(f"⚠️ Warm-up error (minor): {e}")
    time.sleep(2)


def run_cycle():
    """Main execution cycle — sequential single-worker processing."""
    global market_index_df
    start_time = time.time()

    # 1. Fetch Market Context (Index)
    print("🌍 Fetching Market Context (XU100)...")
    market_index_df = analiz.get_market_index()
    if market_index_df is not None:
        regime = pro_engine.get_market_regime(market_index_df)[0]
        print(f"🌍 Market Regime Detected: {regime}")
    else:
        print("⚠️ Market Context unavailable. Proceeding in isolation.")

    print("🚀 Stock Market Robot (SINGLE WORKER MODE)...")
    queue     = STOCKS.copy()
    round_num = 1

    while len(queue) > 0:
        print(f"\n🔄 ROUND {round_num} STARTING | Remaining stocks: {len(queue)}")
        failed = []

        for symbol in queue:
            result = process_stock(symbol)
            if result is not None:
                failed.append(result)

        queue = failed

        if len(queue) > 0:
            wait_sec = min(round_num * 5, 30)
            print(f"🛑 {len(queue)} stocks failed. Cooling down for {wait_sec}s...")
            time.sleep(wait_sec)

        round_num += 1

    elapsed = time.time() - start_time
    print(f"🏁 All stocks completed in {elapsed:.2f} seconds.")

    # Update performance metrics and Excel signal history report
    try:
        from performance_tracker import run_performance_tracker
        run_performance_tracker()
        from excel_exporter import export_signal_history
        export_signal_history()
    except Exception as e:
        print(f"⚠️ Report or Tracking error (non-critical): {e}")


if __name__ == "__main__":
    print("🔥 Warming up system...")
    time.sleep(2)
    warmup()

    print("🚀 Starting system... (Live Mode: 1-minute loop)\n")

    while True:
        try:
            run_cycle()
            print("⏳ Waiting 1 minute for next update...")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Program stopped.")
            break
        except Exception as e:
            print(f"💥 Critical loop error: {e}")
            time.sleep(10)