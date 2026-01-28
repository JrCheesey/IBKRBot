"""
Smoke test module for IBKRBot.

This module tests that all critical imports work without errors
and that no code executes at import time.

Usage:
    python -m ibkrbot.smoke_test
"""
from __future__ import annotations
import sys
import os


def safe_print(msg: str = "", **kwargs) -> None:
    """Print message with fallback for systems that don't support Unicode."""
    try:
        print(msg, **kwargs)
    except UnicodeEncodeError:
        # Fallback: remove emojis and special characters
        ascii_msg = msg.encode('ascii', 'ignore').decode('ascii')
        print(ascii_msg, **kwargs)


def smoke_test() -> int:
    """Run smoke tests on all critical imports."""
    safe_print("🔍 Running IBKRBot smoke test...")
    safe_print("")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Core package imports
    safe_print("1. Testing core package imports...", end=" ")
    try:
        import ibkrbot
        from ibkrbot import __version__
        from ibkrbot.core import config, logging_setup, paths, plan, data_sources, task_runner
        from ibkrbot.core.ibkr import client, contracts, orders
        from ibkrbot.core.features import proposer, placer, show_orders, canceller, janitor, manager
        from ibkrbot.core.visual import chart
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 2: UI imports (should not execute any GUI code)
    safe_print("2. Testing UI imports (no GUI execution)...", end=" ")
    try:
        from ibkrbot.ui import main_window, dialogs, logging_handler
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 3: Main window class can be imported (skip in CI/headless)
    safe_print("3. Testing MainWindow class import...", end=" ")
    is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_ci:
        safe_print("⏭️  SKIP (headless CI environment)")
    else:
        try:
            from ibkrbot.ui.main_window import MainWindow
            safe_print("✅ PASS")
            tests_passed += 1
        except Exception as e:
            safe_print(f"❌ FAIL: {e}")
            tests_failed += 1
        
    # Test 4: PySide6 QAction import location
    safe_print("4. Testing PySide6 QAction import (from QtGui)...", end=" ")
    try:
        from PySide6.QtGui import QAction
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1
        
    # Test 5: Critical dependencies
    safe_print("5. Testing critical dependencies...", end=" ")
    try:
        import PySide6
        import pandas
        import numpy
        import yfinance
        import matplotlib
        import ibapi
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1
    
    # Test 6: New v1.0.2 core modules
    safe_print("6. Testing v1.0.2 core modules...", end=" ")
    try:
        from ibkrbot.core import sound, update_checker, trade_journal, alerts, config_backup, auto_reconnect, system_tray
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1

    # Test 7: New v1.0.2 UI widgets
    safe_print("7. Testing v1.0.2 UI widgets...", end=" ")
    try:
        from ibkrbot.ui.widgets import PortfolioWidget, WatchlistWidget
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1

    # Test 8: Theme system
    safe_print("8. Testing theme system...", end=" ")
    try:
        from ibkrbot.ui.theme import ThemeMode, ThemeManager, get_theme_manager, Colors, ColorsDark
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1

    # Test 9: Main module can be imported
    safe_print("9. Testing main module import...", end=" ")
    try:
        from ibkrbot import main
        safe_print("✅ PASS")
        tests_passed += 1
    except Exception as e:
        safe_print(f"❌ FAIL: {e}")
        tests_failed += 1
    
    # Summary
    safe_print()
    safe_print("=" * 50)
    safe_print(f"Tests passed: {tests_passed}")
    safe_print(f"Tests failed: {tests_failed}")
    safe_print("=" * 50)
    
    if tests_failed == 0:
        safe_print("✅ Smoke test passed! All imports successful.")
        return 0
    else:
        safe_print("❌ Smoke test failed! See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(smoke_test())
