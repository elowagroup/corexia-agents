"""
Test API Integration - Verify all data sources work
Run this script to test yfinance, pandas_datareader (FRED), and data flows
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_yfinance():
    """Test yfinance data fetching"""
    print("\n" + "="*60)
    print("TESTING YFINANCE API")
    print("="*60)

    try:
        # Test basic ticker download
        print("\n1. Fetching SPY daily data...")
        spy = yf.download('SPY', period='5d', progress=False)
        print(f"   ✓ Success! Got {len(spy)} days of data")
        print(f"   Latest close: ${spy['Close'].iloc[-1]:.2f}")

        # Test VIX
        print("\n2. Fetching VIX data...")
        vix = yf.download('^VIX', period='1mo', progress=False)
        print(f"   ✓ Success! Current VIX: {vix['Close'].iloc[-1]:.2f}")

        # Test multiple tickers
        print("\n3. Fetching ratio components (NDX, SPX)...")
        ndx = yf.download('^NDX', period='5d', progress=False)
        spx = yf.download('^GSPC', period='5d', progress=False)
        ratio = ndx['Close'].iloc[-1] / spx['Close'].iloc[-1]
        print(f"   ✓ Success! NDX/SPX ratio: {ratio:.4f}")

        # Test multi-timeframe
        print("\n4. Fetching multi-timeframe data...")
        hourly = yf.download('SPY', period='5d', interval='1h', progress=False)
        fifteen_min = yf.download('SPY', period='2d', interval='15m', progress=False)
        print(f"   ✓ Hourly: {len(hourly)} bars")
        print(f"   ✓ 15-min: {len(fifteen_min)} bars")

        print("\n✅ YFINANCE: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ YFINANCE ERROR: {e}")
        return False

def test_fred():
    """Test pandas_datareader with FRED"""
    print("\n" + "="*60)
    print("TESTING FRED (Federal Reserve Economic Data)")
    print("="*60)

    try:
        from pandas_datareader import data as pdr

        # Test Fed Funds Rate
        print("\n1. Fetching Fed Funds Rate (DFF)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        fed_rate = pdr.DataReader('DFF', 'fred', start=start_date, end=end_date)
        current_rate = fed_rate.iloc[-1].values[0]
        print(f"   ✓ Success! Current Fed Funds Rate: {current_rate:.2f}%")

        # Test Fed Balance Sheet
        print("\n2. Fetching Fed Balance Sheet (WALCL)...")
        start_date = end_date - timedelta(days=90)
        balance_sheet = pdr.DataReader('WALCL', 'fred', start=start_date, end=end_date)
        current_bs = balance_sheet.iloc[-1].values[0]
        print(f"   ✓ Success! Fed Balance Sheet: ${current_bs:,.0f}M")

        # Calculate direction
        bs_3mo_ago = balance_sheet.iloc[0].values[0]
        bs_change = current_bs - bs_3mo_ago
        direction = "Expanding (QE)" if bs_change > 0 else "Contracting (QT)"
        print(f"   Direction: {direction} ({bs_change:+,.0f}M in 3 months)")

        print("\n✅ FRED: ALL TESTS PASSED")
        return True

    except ImportError:
        print("\n⚠️  pandas_datareader not installed")
        print("   Run: pip install pandas-datareader")
        return False
    except Exception as e:
        print(f"\n❌ FRED ERROR: {e}")
        print("   Note: FRED may have rate limits or connectivity issues")
        return False

def test_market_memory():
    """Test Market Memory module integration"""
    print("\n" + "="*60)
    print("TESTING MARKET MEMORY MODULE")
    print("="*60)

    try:
        from market_memory import MarketMemoryAnalyzer

        print("\n1. Initializing Market Memory Analyzer...")
        analyzer = MarketMemoryAnalyzer()
        print("   ✓ Initialized")

        print("\n2. Fetching SPY data for analysis...")
        spy = yf.download('SPY', period='1y', progress=False)

        print("\n3. Running Market Memory analysis...")
        result = analyzer.analyze('SPY', spy)

        print(f"\n   Volatility Analysis:")
        if result['volatility']['vix'].get('value'):
            print(f"   - VIX: {result['volatility']['vix']['value']}")
            print(f"   - Zone: {result['volatility']['vix']['zone_type']}")
            print(f"   - BB Stretched: {result['volatility']['vix']['bb_stretched']}")
            if result['volatility']['vix'].get('memory_levels'):
                print(f"   - Memory Levels Found: {len(result['volatility']['vix']['memory_levels'])}")

        print(f"\n   Zone Hit: {result['zone_hit']}")
        print(f"   Divergence: {result['divergence']}")

        print("\n✅ MARKET MEMORY: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ MARKET MEMORY ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regime_detection():
    """Test Regime Detection module"""
    print("\n" + "="*60)
    print("TESTING REGIME DETECTION MODULE")
    print("="*60)

    try:
        from regime_detection import RegimeDetector

        print("\n1. Initializing Regime Detector...")
        detector = RegimeDetector()
        print("   ✓ Initialized")

        print("\n2. Fetching SPY data...")
        spy = yf.download('SPY', period='1y', progress=False)

        print("\n3. Detecting regime...")
        regime = detector.detect(spy)

        print(f"\n   Results:")
        print(f"   - Macro Regime: {regime['macro']}")
        print(f"   - Fed Policy: {regime['fed_policy']}")
        print(f"   - Fed Funds Rate: {regime['fed_funds_rate']}%")
        print(f"   - Rate Direction: {regime['rate_direction']}")
        print(f"   - Wyckoff Phase: {regime['wyckoff_phase']}")
        print(f"   - Regime Quality: {regime['regime_quality']}/10")

        print("\n✅ REGIME DETECTION: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ REGIME DETECTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_numerology():
    """Test Sequence Map module"""
    print("\n" + "="*60)
    print("TESTING SHYLO SEQUENCE (NUMEROLOGY)")
    print("="*60)

    try:
        from numerology import SequenceMap

        print("\n1. Initializing Sequence Analyzer...")
        analyzer = SequenceMap()
        print("   ✓ Initialized")

        print("\n2. Testing various price levels...")
        test_prices = [424.56, 394.00, 424.24, 469.00, 500.00]

        for price in test_prices:
            result = analyzer.analyze(price)
            print(f"\n   Price: ${price}")
            print(f"   - Floor: {result['current_floor']}")
            print(f"   - Palindrome: {result['is_palindrome']}")
            print(f"   - Holy Trinity: {result['is_holy_trinity']}")
            print(f"   - OJ Pivot: {result['is_oj_pivot']}")
            print(f"   - Next Magnets: {result['next_magnets'][:3]}")

        print("\n✅ NUMEROLOGY: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ NUMEROLOGY ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all API integration tests"""
    print("\n")
    print("█" * 60)
    print("  MATRIX SCANNER - API INTEGRATION TEST SUITE")
    print("█" * 60)

    results = {
        'yfinance': test_yfinance(),
        'FRED': test_fred(),
        'Market Memory': test_market_memory(),
        'Regime Detection': test_regime_detection(),
        'Numerology': test_numerology()
    }

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<30} {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print("="*60)
    print(f"Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL SYSTEMS GO! Your Matrix Scanner is ready.")
        print("   Run: streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("   Make sure you've run: pip install -r requirements.txt")

    print("="*60)

if __name__ == "__main__":
    run_all_tests()
