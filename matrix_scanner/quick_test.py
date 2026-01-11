"""Quick 5-scenario test to verify system works before running full 50"""

import yfinance as yf
from market_memory import MarketMemoryAnalyzer
from regime_detection import RegimeDetector
from numerology import SequenceMap
import time

print("="*60)
print("  QUICK API TEST - 5 Scenarios")
print("="*60)

test_tickers = ['SPY', 'AAPL', 'TSLA', '^VIX', 'QQQ']

memory_analyzer = MarketMemoryAnalyzer()
regime_detector = RegimeDetector()
sequence_analyzer = SequenceMap()

passed = 0
failed = 0

for i, ticker in enumerate(test_tickers, 1):
    print(f"\n[{i}/5] Testing {ticker}...")

    try:
        # Fetch data
        data = yf.download(ticker, period='1y', progress=False)

        if len(data) == 0:
            print(f"   [FAIL] No data returned")
            failed += 1
            continue

        price = float(data['Close'].iloc[-1])
        print(f"   Price: ${price:.2f}")

        # Test each module
        memory = memory_analyzer.analyze(ticker, data)
        regime = regime_detector.detect(data)
        sequence = sequence_analyzer.analyze(price)

        print(f"   VIX: {memory['volatility']['vix'].get('value', 'N/A')}")
        print(f"   Regime: {regime.get('macro', 'Unknown')}")
        print(f"   Floor: {sequence.get('current_floor', 'N/A')}")
        print(f"   [PASS]")
        passed += 1

    except Exception as e:
        print(f"   [FAIL] {str(e)[:60]}")
        failed += 1

    time.sleep(0.5)

print("\n" + "="*60)
print(f"Results: {passed}/5 passed, {failed}/5 failed")

if passed == 5:
    print("[OK] All systems working! Ready for full 50-scenario test.")
    print("Run: python stress_test_50_scenarios.py")
else:
    print("[WARN] Some issues detected. Review errors above.")

print("="*60)
