
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Emoji maps
SIGNAL_EMOJI = {
    "STRONG_BUY": "🚀",
    "BUY":        "📈",
    "WATCH":      "👀",
}
CONVICTION_EMOJI = {
    "DIAMOND": "💎",
    "GOLD":    "🥇",
    "SILVER":  "🥈",
    "BRONZE":  "🥉",
}
REGIME_EMOJI = {
    "BULL":     "🐂",
    "SIDEWAYS": "↔️",
    "BEAR":     "🐻",
}


# ──────────────────────────────────────────────────────────────
# Notification Type 1: Trend Hunter Signal
# RSI, Score, ADX focused — Trend Engine output
# ──────────────────────────────────────────────────────────────
def send_trend_notification(payload: dict) -> bool:
    """
    Sends a Trend Hunter signal notification via Telegram.
    Payload fields: Signal, Score, Rsi, Adx, MacdHist, Price, StopPrice, TargetPrice, LastUpdated.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token/chat_id missing — notification not sent.")
        return False

    symbol       = payload.get("Symbol", "?")
    signal       = payload.get("Signal", "NO_TRADE")
    score        = payload.get("Score", 0)
    rsi          = payload.get("Rsi", 0)
    adx          = payload.get("Adx", 0)
    macd_hist    = payload.get("MacdHist", 0)
    price        = payload.get("Price", 0)
    stop_price   = payload.get("StopPrice", 0)
    target_price = payload.get("TargetPrice", 0)
    date_str     = payload.get("LastUpdated", "")[:16]
    sig_emoji    = SIGNAL_EMOJI.get(signal, "📊")

    text = (
        f"{sig_emoji} *{symbol}* — Trend Hunter Signal\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Signal: *{signal}*\n"
        f"⭐ Score: `{score}`\n"
        f"📉 RSI: `{rsi:.1f}`\n"
        f"📊 ADX: `{adx:.1f}`\n"
        f"〰️ MACD Hist: `{macd_hist:.4f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: `{price:.2f} TL`\n"
        f"🎯 Target: `{target_price:.2f} TL`\n"
        f"🛑 Stop: `{stop_price:.2f} TL`\n"
        f"📅 {date_str}"
    )
    return _send(text)


# ──────────────────────────────────────────────────────────────
# Notification Type 2: Smart Picks Signal
# Conviction (Diamond/Gold/Silver/Bronze), UnifiedScore,
# MarketRegime, Tags + Trend Hunter summary
# ──────────────────────────────────────────────────────────────
def send_smart_picks_notification(payload: dict) -> bool:
    """
    Sends a Smart Picks (Pro Engine) signal notification via Telegram.
    Payload fields: conviction, unified_score, regime, tags + trend fields.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token/chat_id missing — notification not sent.")
        return False

    symbol        = payload.get("Symbol", "?")
    signal        = payload.get("Signal", "NO_TRADE")
    unified_score = payload.get("UnifiedScore", 0)
    conviction    = payload.get("Conviction", "BRONZE")
    main_strategy = payload.get("MainStrategy", "NEUTRAL")
    market_regime = payload.get("MarketRegime", "SIDEWAYS")
    tags          = payload.get("Tags", [])
    score         = payload.get("Score", 0)
    rsi           = payload.get("Rsi", 0)
    adx           = payload.get("Adx", 0)
    price         = payload.get("Price", 0)
    stop_price    = payload.get("StopPrice", 0)
    target_price  = payload.get("TargetPrice", 0)
    date_str      = payload.get("LastUpdated", "")[:16]

    sig_emoji  = SIGNAL_EMOJI.get(signal, "📊")
    conv_emoji = CONVICTION_EMOJI.get(conviction, "🥉")
    reg_emoji  = REGIME_EMOJI.get(market_regime, "↔️")

    if unified_score >= 80 and conviction in ("DIAMOND", "GOLD"):
        category = "🔝 TOP PICKS"
    elif unified_score >= 65:
        category = "👁 WATCHLIST"
    else:
        category = "⚠️ AVOID"

    tags_str = ", ".join(tags) if tags else "—"

    text = (
        f"{sig_emoji} *{symbol}* — Smart Picks\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Category: *{category}*\n"
        f"{conv_emoji} Conviction: *{conviction}*\n"
        f"🎯 Unified Score: `{unified_score}`\n"
        f"📌 Strategy: `{main_strategy}`\n"
        f"{reg_emoji} Market: `{market_regime}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Tags: `{tags_str}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Trend Hunter Summary\n"
        f"  Score: `{score}` | RSI: `{rsi:.1f}` | ADX: `{adx:.1f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: `{price:.2f} TL`\n"
        f"🎯 Target: `{target_price:.2f} TL`\n"
        f"🛑 Stop: `{stop_price:.2f} TL`\n"
        f"📅 {date_str}"
    )
    return _send(text)


# ──────────────────────────────────────────────────────────────
# HTTP Sender
# ──────────────────────────────────────────────────────────────
def _send(text: str) -> bool:
    """Sends a message via the Telegram Bot API."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "Markdown"
        }, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"⚠️ Telegram API error: {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")
        return False
