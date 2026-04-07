#!/usr/bin/env python3
"""
RICK Trading System - Quick Verification Test
Tests that all core components can be imported and initialized
"""

import sys
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

print("=" * 70)
print("RICK Trading System - Component Verification Test")
print("=" * 70)
print()

# Track results
tests_passed = 0
tests_failed = 0
errors = []

def test_import(module_name, description):
    """Test if a module can be imported"""
    global tests_passed, tests_failed, errors
    try:
        __import__(module_name)
        print(f"✓ {description}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"✗ {description}: {str(e)[:60]}")
        tests_failed += 1
        errors.append(f"{description}: {str(e)}")
        return False

print("1. Testing Core Dependencies:")
print("-" * 70)
test_import('oandapyV20', 'OANDA API Wrapper')
test_import('pandas', 'Pandas Data Analysis')
test_import('numpy', 'NumPy Numerical Computing')
test_import('websocket', 'WebSocket Client')
test_import('dotenv', 'Python-dotenv')

print()
print("2. Testing RICK Core Modules:")
print("-" * 70)
test_import('foundation.rick_charter', 'Charter System')
test_import('brokers.oanda_connector', 'OANDA Connector')
test_import('util.narration_logger', 'Narration Logger')
test_import('util.terminal_display', 'Terminal Display')
test_import('util.rick_narrator', 'Rick Narrator')

print()
print("3. Testing ML Components:")
print("-" * 70)
test_import('ml_learning.regime_detector', 'Regime Detector')
test_import('ml_learning.signal_analyzer', 'Signal Analyzer')

print()
print("4. Testing Trading Engine:")
print("-" * 70)
try:
    from oanda_trading_engine import OandaTradingEngine, main
    print(f"✓ Trading Engine Import")
    tests_passed += 1
except Exception as e:
    print(f"✗ Trading Engine Import: {str(e)[:60]}")
    tests_failed += 1
    errors.append(f"Trading Engine: {str(e)}")

print()
print("=" * 70)
print("Test Results Summary")
print("=" * 70)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
print()

if tests_failed == 0:
    print("✅ ALL TESTS PASSED - System is ready for paper trading!")
    print()
    print("To start paper trading:")
    print("  ./start_trading.sh")
    print("  OR")
    print("  python3 launch_paper_trading.py")
    sys.exit(0)
else:
    print("⚠️  SOME TESTS FAILED - See errors above")
    print()
    if errors:
        print("Errors encountered:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    sys.exit(1)
