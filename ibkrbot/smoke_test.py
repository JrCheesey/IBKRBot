"""
Smoke test module for IBKRBot.

This module tests that all critical imports work without errors
and that no code executes at import time.

Usage:
    python -m ibkrbot.smoke_test
"""
from __future__ import annotations
import sys


def smoke_test() -> int:
    """Run smoke tests on all critical imports."""
    print("🔍 Running IBKRBot smoke test...")
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Core package imports
    print("1. Testing core package imports...", end=" ")
    try:
        import ibkrbot
        from ibkrbot import __version__
        from ibkrbot.core import config, logging_setup, paths, plan, data_sources, task_runner
        from ibkrbot.core.ibkr import client, contracts, orders
        from ibkrbot.core.features import proposer, placer, show_orders, canceller, janitor, manager
        from ibkrbot.core.visual import chart
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 2: UI imports (should not execute any GUI code)
    print("2. Testing UI imports (no GUI execution)...", end=" ")
    try:
        from ibkrbot.ui import main_window, dialogs, logging_handler
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 3: Main window class can be imported
    print("3. Testing MainWindow class import...", end=" ")
    try:
        from ibkrbot.ui.main_window import MainWindow
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 4: PySide6 QAction import location
    print("4. Testing PySide6 QAction import (from QtGui)...", end=" ")
    try:
        from PySide6.QtGui import QAction
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 5: Critical dependencies
    print("5. Testing critical dependencies...", end=" ")
    try:
        import PySide6
        import pandas
        import numpy
        import yfinance
        import matplotlib
        import ibapi
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
    
    # Test 6: Main module can be imported
    print("6. Testing main module import...", end=" ")
    try:
        from ibkrbot import main
        print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: {e}")
        tests_failed += 1
    
    # Summary
    print()
    print("=" * 50)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print("=" * 50)
    
    if tests_failed == 0:
        print("✅ Smoke test passed! All imports successful.")
        return 0
    else:
        print("❌ Smoke test failed! See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(smoke_test())
