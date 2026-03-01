"""Quick standalone unit test for notification_guard logic (no DB dependency)."""
import sys, os, time

# Don't import config - test guard in isolation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5433')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_NAME', 'borsa_db')

# Patch state file to use temp location for test
import core.notification_guard as guard
guard._STATE_FILE = '/tmp/test_notif_state.json'

from core.notification_guard import should_notify, reset_all

reset_all()

ok = True

def expect(label, result, expected):
    global ok
    status = '✅' if result == expected else '❌'
    if result != expected:
        ok = False
    print(f"  {status} {label}: got {result}, expected {expected}")

print("\n=== TEST 1: First time — both should fire ===")
expect("SDTTR_trend ilk", should_notify('SDTTR_trend', 'BUY', 85), True)
expect("SDTTR_smart ilk", should_notify('SDTTR_smart', 'BUY', 100), True)

print("\n=== TEST 2: Immediate repeat — both should block ===")
expect("SDTTR_trend tekrar", should_notify('SDTTR_trend', 'BUY', 85), False)
expect("SDTTR_smart tekrar", should_notify('SDTTR_smart', 'BUY', 100), False)

print("\n=== TEST 3: Signal escalation BUY->STRONG_BUY — should fire ===")
expect("SDTTR BUY->STRONG_BUY", should_notify('SDTTR_trend', 'STRONG_BUY', 90), True)

print("\n=== TEST 4: NO_TRADE — always block ===")
expect("THYAO NO_TRADE", should_notify('THYAO', 'NO_TRADE', 20), False)

print("\n=== TEST 5: Score jump +9, but 0h elapsed (< 1h) — should block ===")
should_notify('KOZAL', 'WATCH', 60)  # seed
expect("KOZAL skor +9, 0h", should_notify('KOZAL', 'WATCH', 69), False)

print("\n=== TEST 6: WATCH -> BUY (escalation) — should fire ===")
should_notify('EREGL', 'WATCH', 55)  # seed
expect("EREGL WATCH->BUY", should_notify('EREGL', 'BUY', 65), True)

print()
if ok:
    print("🎉 TÜM TESTLER GEÇTİ — Guard doğru çalışıyor!")
else:
    print("💥 Bazı testler başarısız!")

sys.exit(0 if ok else 1)
