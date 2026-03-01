"""
notification_guard.py
──────────────────────────────────────────────────────────────────
Telegram bildirim spamını önleyen akıllı kontrol modülü.

Bir hisse için bildirim GÖNDERİR eğer:
  1. Sinyal YÜKSELDIYSE  (örn: NO_TRADE → BUY, BUY → STRONG_BUY)  ← her zaman
  2. Unified Score ≥ 8 puan arttıysa  VE  son bildirimden ≥1 saat geçtiyse
  3. Aynı sinyal devam ediyorsa  VE  cooldown süresi geçtiyse
     (STRONG_BUY: 4h | BUY: 6h | WATCH: 8h)

State dosyası: data/notif_state.json  (otomatik oluşturulur)
──────────────────────────────────────────────────────────────────
"""

import json
import os
import time
from datetime import datetime

# ─── Ayarlar ──────────────────────────────────────────────────────────────────
_DATA_DIR   = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
_STATE_FILE = os.path.join(_DATA_DIR, 'notif_state.json')

# Sinyal önceliği (yüksek = daha güçlü)
SIGNAL_PRIORITY = {
    'NO_TRADE':  0,
    'WATCH':     1,
    'BUY':       2,
    'STRONG_BUY': 3,
}

# Aynı sinyal için minimum bekleme süresi (saat)
COOLDOWN_HOURS = {
    'STRONG_BUY': 4,
    'BUY':        6,
    'WATCH':      8,
}

# Cooldown'u bypass eden minimum skor artışı
SCORE_JUMP_THRESHOLD = 8   # unified_score'da bu kadar artış gerekli
SCORE_JUMP_MIN_WAIT  = 1   # skor atladığında bile en az bu kadar saat bekle (h)

# ─── State Yönetimi ───────────────────────────────────────────────────────────
def _load_state() -> dict:
    if os.path.exists(_STATE_FILE):
        try:
            with open(_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _update(state: dict, symbol: str, signal: str,
            unified_score: int, now: float) -> None:
    state[symbol] = {
        'signal':        signal,
        'unified_score': unified_score,
        'last_notified': now,
        'last_notified_human': datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M'),
    }
    _save_state(state)


# ─── Ana Karar Fonksiyonu ─────────────────────────────────────────────────────
def should_notify(symbol: str, signal: str, unified_score: int,
                  verbose: bool = True) -> bool:
    """
    True döndürürse bildirim gönder, False döndürürse geç.

    Parametreler
    ────────────
    symbol       : Hisse sembolü (örn: 'THYAO')
    signal       : Mevcut sinyal ('BUY', 'STRONG_BUY', 'WATCH', ...)
    unified_score: Mevcut unified score (0-100)
    verbose      : True ise karar sebebini terminale yazar
    """
    # NO_TRADE asla bildirim almaz
    if SIGNAL_PRIORITY.get(signal, 0) == 0:
        return False

    state        = _load_state()
    now          = time.time()
    last         = state.get(symbol, {})

    last_signal  = last.get('signal',        'NO_TRADE')
    last_score   = last.get('unified_score', 0)
    last_time    = last.get('last_notified', 0)

    cur_priority  = SIGNAL_PRIORITY.get(signal, 0)
    last_priority = SIGNAL_PRIORITY.get(last_signal, 0)
    hours_elapsed = (now - last_time) / 3600
    score_jump    = unified_score - last_score

    def _allow(reason: str) -> bool:
        if verbose:
            print(f"🔔 [{symbol}] Bildirim ONAYLANDI — {reason}")
        _update(state, symbol, signal, unified_score, now)
        return True

    def _block(reason: str) -> bool:
        if verbose:
            print(f"🔕 [{symbol}] Bildirim engellendi — {reason}")
        return False

    # ── Kural 1: Sinyal yükseldi (her zaman bildir) ──────────────────────────
    if cur_priority > last_priority:
        return _allow(f"sinyal yükseltildi {last_signal} → {signal}")

    # ── Kural 2: Skor önemli oranda atladı ───────────────────────────────────
    if score_jump >= SCORE_JUMP_THRESHOLD:
        if hours_elapsed >= SCORE_JUMP_MIN_WAIT:
            return _allow(
                f"skor atladı {last_score}→{unified_score} "
                f"(+{score_jump}) | {hours_elapsed:.1f}h geçti"
            )
        else:
            return _block(
                f"skor atladı ama çok yakın ({hours_elapsed:.1f}h < {SCORE_JUMP_MIN_WAIT}h)"
            )

    # ── Kural 3: Cooldown süresi doldu ───────────────────────────────────────
    cooldown = COOLDOWN_HOURS.get(signal, 6)
    if hours_elapsed >= cooldown:
        return _allow(
            f"cooldown doldu ({hours_elapsed:.1f}h > {cooldown}h) | "
            f"sinyal: {signal} | skor: {unified_score}"
        )

    # ── Engelle ──────────────────────────────────────────────────────────────
    return _block(
        f"aynı sinyal ({signal}) | {hours_elapsed:.1f}h/{cooldown}h geçti | "
        f"skor farkı: {score_jump:+d}"
    )


def reset_symbol(symbol: str) -> None:
    """Belirli bir hissenin state'ini sıfırla (test/debug için)."""
    state = _load_state()
    if symbol in state:
        del state[symbol]
        _save_state(state)
        print(f"♻️  {symbol} state sıfırlandı.")


def reset_all() -> None:
    """Tüm state'i sıfırla."""
    _save_state({})
    print("♻️  Tüm bildirim state'i sıfırlandı.")


def show_state() -> None:
    """Mevcut state'i terminalde göster."""
    state = _load_state()
    if not state:
        print("📭 Hiç kayıt yok.")
        return
    print(f"\n{'Sembol':<10} {'Son Sinyal':<14} {'Unified':<9} {'Son Bildirim'}")
    print("─" * 60)
    for sym, data in sorted(state.items()):
        print(f"{sym:<10} {data.get('signal',''):<14} "
              f"{data.get('unified_score',0):<9} "
              f"{data.get('last_notified_human','')}")
    print()
