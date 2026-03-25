"""
notification_guard.py
──────────────────────────────────────────────────────────────────
Smart notification spam prevention module.

A notification IS sent for a symbol if:
  1. The signal has ESCALATED  (e.g. NO_TRADE → BUY, BUY → STRONG_BUY)  ← always
  2. The unified_score jumped ≥ 8 points  AND  ≥1 hour has elapsed since last notification
  3. The same signal is repeating  AND  the cooldown period has expired:
     (STRONG_BUY: 4h | BUY: 6h | WATCH: 8h)

State file: data/notif_state.json  (auto-created)
──────────────────────────────────────────────────────────────────
"""

import json
import os
import time
from datetime import datetime

# ─── Settings ────────────────────────────────────────────────────────────────
_DATA_DIR   = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
_STATE_FILE = os.path.join(_DATA_DIR, 'notif_state.json')

# Signal priority (higher = stronger)
SIGNAL_PRIORITY = {
    'NO_TRADE':   0,
    'WATCH':      1,
    'BUY':        2,
    'STRONG_BUY': 3,
}

# Minimum wait time (hours) before re-notifying for the same signal
COOLDOWN_HOURS = {
    'STRONG_BUY': 4,
    'BUY':        6,
    'WATCH':      8,
}

# Score jump required to bypass cooldown
SCORE_JUMP_THRESHOLD = 8   # minimum unified_score increase required
SCORE_JUMP_MIN_WAIT  = 1   # minimum hours to wait even when score jumps


# ─── State Management ─────────────────────────────────────────────────────────
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
        'signal':              signal,
        'unified_score':       unified_score,
        'last_notified':       now,
        'last_notified_human': datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M'),
    }
    _save_state(state)


# ─── Main Decision Function ───────────────────────────────────────────────────
def should_notify(symbol: str, signal: str, unified_score: int,
                  verbose: bool = True) -> bool:
    """
    Returns True if a notification should be sent, False to skip.

    Parameters
    ──────────
    symbol       : Stock symbol (e.g. 'THYAO')
    signal       : Current signal ('BUY', 'STRONG_BUY', 'WATCH', ...)
    unified_score: Current unified score (0–100)
    verbose      : If True, prints decision reason to terminal
    """
    # NO_TRADE never triggers a notification
    if SIGNAL_PRIORITY.get(signal, 0) == 0:
        return False

    state  = _load_state()
    now    = time.time()
    last   = state.get(symbol, {})

    last_signal = last.get('signal',        'NO_TRADE')
    last_score  = last.get('unified_score', 0)
    last_time   = last.get('last_notified', 0)

    cur_priority  = SIGNAL_PRIORITY.get(signal, 0)
    last_priority = SIGNAL_PRIORITY.get(last_signal, 0)
    hours_elapsed = (now - last_time) / 3600
    score_jump    = unified_score - last_score

    def _allow(reason: str) -> bool:
        if verbose:
            print(f"🔔 [{symbol}] Notification APPROVED — {reason}")
        _update(state, symbol, signal, unified_score, now)
        return True

    def _block(reason: str) -> bool:
        if verbose:
            print(f"🔕 [{symbol}] Notification blocked — {reason}")
        return False

    # ── Rule 1: Signal escalated → always notify ─────────────────────────────
    if cur_priority > last_priority:
        return _allow(f"signal escalated {last_signal} → {signal}")

    # ── Rule 2: Score jumped significantly ───────────────────────────────────
    if score_jump >= SCORE_JUMP_THRESHOLD:
        if hours_elapsed >= SCORE_JUMP_MIN_WAIT:
            return _allow(
                f"score jumped {last_score}→{unified_score} "
                f"(+{score_jump}) | {hours_elapsed:.1f}h elapsed"
            )
        else:
            return _block(
                f"score jumped but too soon ({hours_elapsed:.1f}h < {SCORE_JUMP_MIN_WAIT}h)"
            )

    # ── Rule 3: Cooldown expired ──────────────────────────────────────────────
    cooldown = COOLDOWN_HOURS.get(signal, 6)
    if hours_elapsed >= cooldown:
        return _allow(
            f"cooldown expired ({hours_elapsed:.1f}h > {cooldown}h) | "
            f"signal: {signal} | score: {unified_score}"
        )

    # ── Block ─────────────────────────────────────────────────────────────────
    return _block(
        f"same signal ({signal}) | {hours_elapsed:.1f}h/{cooldown}h elapsed | "
        f"score diff: {score_jump:+d}"
    )


def reset_symbol(symbol: str) -> None:
    """Reset the notification state for a specific symbol (for testing/debug)."""
    state = _load_state()
    if symbol in state:
        del state[symbol]
        _save_state(state)
        print(f"♻️  {symbol} state reset.")


def reset_all() -> None:
    """Reset the entire notification state."""
    _save_state({})
    print("♻️  All notification state reset.")


def show_state() -> None:
    """Display the current notification state in the terminal."""
    state = _load_state()
    if not state:
        print("📭 No records found.")
        return
    print(f"\n{'Symbol':<10} {'Last Signal':<14} {'Unified':<9} {'Last Notified'}")
    print("─" * 60)
    for sym, data in sorted(state.items()):
        print(f"{sym:<10} {data.get('signal',''):<14} "
              f"{data.get('unified_score',0):<9} "
              f"{data.get('last_notified_human','')}")
    print()
