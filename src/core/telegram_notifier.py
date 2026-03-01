
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
# Bildirim Türü 1: Trend Hunter Sinyali
# RSI, Score, ADX odaklı — Trend Engine çıktısı
# ──────────────────────────────────────────────────────────────
def send_trend_notification(payload: dict) -> bool:
    """
    Trend Hunter bazlı bildirim.
    Gönderilecek bilgiler: sinyal, score, RSI, ADX, fiyat.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token/chat_id eksik, bildirim gönderilmedi.")
        return False

    sembol      = payload.get("Sembol", "?")
    signal      = payload.get("Signal", "NO_TRADE")
    score       = payload.get("Score", 0)
    rsi         = payload.get("Rsi", 0)
    adx         = payload.get("Adx", 0)
    macd_hist   = payload.get("MacdHist", 0)
    fiyat       = payload.get("Fiyat", 0)
    stop_price  = payload.get("StopPrice", 0)
    target_price= payload.get("TargetPrice", 0)
    tarih       = payload.get("SonGuncelleme", "")[:16]
    sig_emoji   = SIGNAL_EMOJI.get(signal, "📊")

    text = (
        f"{sig_emoji} *{sembol}* — Trend Hunter Sinyali\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Sinyal: *{signal}*\n"
        f"⭐ Score: `{score}`\n"
        f"📉 RSI: `{rsi:.1f}`\n"
        f"📊 ADX: `{adx:.1f}`\n"
        f"〰️ MACD Hist: `{macd_hist:.4f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Fiyat: `{fiyat:.2f} TL`\n"
        f"🎯 Hedef: `{target_price:.2f} TL`\n"
        f"🛑 Stop: `{stop_price:.2f} TL`\n"
        f"📅 {tarih}"
    )
    return _send(text)


# ──────────────────────────────────────────────────────────────
# Bildirim Türü 2: Smart Picks Sinyali
# Conviction (Diamond/Gold/Silver/Bronze), UnifiedScore,
# MarketRegime, Tags + Trend Hunter özeti dahil
# ──────────────────────────────────────────────────────────────
def send_smart_picks_notification(payload: dict) -> bool:
    """
    Smart Picks (Pro Engine) bazlı bildirim.
    Gönderilecek bilgiler: conviction, unified_score, regime, tags + trend bilgileri.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token/chat_id eksik, bildirim gönderilmedi.")
        return False

    sembol        = payload.get("Sembol", "?")
    signal        = payload.get("Signal", "NO_TRADE")
    unified_score = payload.get("UnifiedScore", 0)
    conviction    = payload.get("Conviction", "BRONZE")
    main_strategy = payload.get("MainStrategy", "NEUTRAL")
    market_regime = payload.get("MarketRegime", "SIDEWAYS")
    tags          = payload.get("Tags", [])
    score         = payload.get("Score", 0)
    rsi           = payload.get("Rsi", 0)
    adx           = payload.get("Adx", 0)
    fiyat         = payload.get("Fiyat", 0)
    stop_price    = payload.get("StopPrice", 0)
    target_price  = payload.get("TargetPrice", 0)
    tarih         = payload.get("SonGuncelleme", "")[:16]

    sig_emoji   = SIGNAL_EMOJI.get(signal, "📊")
    conv_emoji  = CONVICTION_EMOJI.get(conviction, "🥉")
    reg_emoji   = REGIME_EMOJI.get(market_regime, "↔️")

    # Kategori belirleme (Top Picks / WatchList / Avoid)
    if unified_score >= 80 and conviction in ("DIAMOND", "GOLD"):
        kategori = "🔝 TOP PICKS"
    elif unified_score >= 65:
        kategori = "👁 WATCHLIST"
    else:
        kategori = "⚠️ AVOID"

    tags_str = ", ".join(tags) if tags else "—"

    text = (
        f"{sig_emoji} *{sembol}* — Smart Picks\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Kategori: *{kategori}*\n"
        f"{conv_emoji} Conviction: *{conviction}*\n"
        f"🎯 Unified Score: `{unified_score}`\n"
        f"📌 Strateji: `{main_strategy}`\n"
        f"{reg_emoji} Piyasa: `{market_regime}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Tags: `{tags_str}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Trend Hunter Özeti\n"
        f"  Score: `{score}` | RSI: `{rsi:.1f}` | ADX: `{adx:.1f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Fiyat: `{fiyat:.2f} TL`\n"
        f"🎯 Hedef: `{target_price:.2f} TL`\n"
        f"🛑 Stop: `{stop_price:.2f} TL`\n"
        f"📅 {tarih}"
    )
    return _send(text)


# ──────────────────────────────────────────────────────────────
# HTTP Gönderici
# ──────────────────────────────────────────────────────────────
def _send(text: str) -> bool:
    """Telegram Bot API ile mesaj gönderir."""
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
            print(f"⚠️ Telegram API hatası: {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram gönderim hatası: {e}")
        return False
