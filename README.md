# IBKRBot

[![Cross-Platform Test](https://github.com/JrCheesey/IBKRBot/workflows/Cross-Platform%20Test/badge.svg)](https://github.com/JrCheesey/IBKRBot/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)](INSTALL_LINUX_MAC.md)

A desktop application for Interactive Brokers swing trading with full paper and live trading support.

**Warning: Educational Use Only**: This software is for educational purposes. Trading involves substantial risk of loss. See [LICENSE](LICENSE) for full disclaimer.

---

## Quick Start

### Download Prebuilt Executable (Easiest)

**Windows:**
- Download the latest release: [Releases](https://github.com/JrCheesey/IBKRBot/releases)
- Extract ZIP and run `IBKRBot.exe`

**Linux / macOS:**
- See [INSTALL_LINUX_MAC.md](INSTALL_LINUX_MAC.md) for installation instructions
- Pre-built binaries available in [GitHub Actions artifacts](https://github.com/JrCheesey/IBKRBot/actions)

### Run from Source

```bash
# Clone repository
git clone https://github.com/JrCheesey/IBKRBot.git
cd IBKRBot

# Install dependencies
pip install -e .

# Run application
ibkrbot
```

See [Installation & Setup](#installation--setup) for detailed instructions.

---

## Features

### Core Trading Features
- **ATR-Based Swing Strategy**: Propose bracket orders using ATR pullback methodology
- **Free Data Source**: Uses Yahoo Finance (yfinance) for historical price data
- **Paper & Live Trading**: Switch between paper and live modes with strong confirmation safeguards
- **Draft Plans**: Save and review trading plans before placement
- **Bracket Orders**: Automated entry, stop-loss, and take-profit orders
- **Order Management**: View positions, cancel orders, manage risk
- **Automated Janitor**: Auto-cancel orders before market close
- **Position Manager**: Automated monitoring and management loop

### Safety & User Experience (v1.0.1)
- **Mode Selector**: Dropdown to switch between paper and live trading
- **Live Mode Protection**: Multi-step confirmation required when switching to live trading
- **Visual Indicators**: Color-coded UI shows current trading mode at a glance
- **Keyboard Shortcuts**: F1 for help, quick navigation
- **First-Run Wizard**: Welcome screen with setup guidance
- **Market Hours Warning**: Alerts when market is closed
- **Enhanced Error Messages**: Clear, actionable error descriptions
- **About Dialog**: Full disclaimers and license information

### New in v1.0.2

**Theme & UI**
- **Dark Mode**: Full dark theme with View menu toggle
- **System Tray**: Minimize to tray with desktop notifications
- **Portfolio Widget**: Real-time account summary and positions display
- **Watchlist Widget**: Multi-symbol price monitoring with auto-refresh

**Trading Tools**
- **Trade Journal**: Track all trades with P&L, R-multiple calculations, and CSV export
- **Price Alerts**: Set custom alerts for price levels (above, below, crosses)
- **Sound Notifications**: Audio feedback for connections, orders, and alerts

**Reliability**
- **Auto-Reconnect**: Automatic reconnection with exponential backoff on connection loss
- **Config Backup/Restore**: Backup and restore all settings, journal, and plans
- **Update Checker**: Check for new releases from GitHub

**Developer Features**
- **Unit Tests**: pytest test suite for core modules
- **CI/CD**: GitHub Actions testing on Windows, Linux, and macOS

## Installation & Setup

### 1. Install Package (Editable Mode)

```bash
# From the project root (folder containing pyproject.toml)
pip install -e .

# Or install with dev dependencies (includes PyInstaller, pytest)
pip install -e ".[dev]"
```

After installation, you can run from any directory:

```bash
python -m ibkrbot.main
# or simply
ibkrbot
```

### 2. Run from Source (Alternative)

If you prefer not to install:

```bash
# Make sure you're in the project root (folder containing pyproject.toml)
python -m ibkrbot.main
```

**Important**: You must be in the project root directory that contains the `ibkrbot/` folder.

### 3. Verify Installation (Smoke Test)

```bash
# Test that all imports work without errors
python -m ibkrbot.smoke_test

# Should output: "Smoke test passed! All imports successful."
```

## Building Windows Executable

### Prerequisites

- Windows 10+
- Python 3.11+ (tested with 3.11.14)
- Conda or venv environment
- PyInstaller 6.0+ installed

### Build Steps

```bash
# 1. Ensure package is installed
pip install -e ".[dev]"

# 2. Run the build script (from project root)
scripts\build_exe.bat

# Output will be in: dist\IBKRBot\IBKRBot.exe
```

### Manual Build (Alternative)

```bash
# From project root
pyinstaller scripts\ibkrbot.spec

# Or direct command
pyinstaller --clean ^
    --name IBKRBot ^
    --windowed ^
    --add-data "ibkrbot/resources;ibkrbot/resources" ^
    --hidden-import ibkrbot.ui.main_window ^
    --collect-submodules ibapi ^
    --collect-submodules ibkrbot ^
    run_ibkrbot.py
```

## Project Structure

```
IBKRBot/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Community guidelines
├── SECURITY.md             # Security policy
├── LICENSE                 # MIT License
├── run_ibkrbot.py          # Entry wrapper for PyInstaller
│
├── ibkrbot/                # Main package
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── smoke_test.py       # Import verification
│   │
│   ├── ui/                 # GUI components
│   │   ├── main_window.py  # Main application window
│   │   ├── dialogs.py      # Dialog windows
│   │   ├── logging_handler.py
│   │   ├── theme.py        # Dark/light theme system
│   │   └── widgets/        # Reusable UI widgets
│   │       ├── portfolio_widget.py
│   │       └── watchlist_widget.py
│   │
│   ├── core/               # Business logic
│   │   ├── config.py       # Configuration management
│   │   ├── logging_setup.py
│   │   ├── paths.py        # Path utilities
│   │   ├── plan.py         # Trade plan management
│   │   ├── data_sources.py # Yahoo Finance integration
│   │   ├── task_runner.py  # Background task runner
│   │   │
│   │   ├── sound.py        # Sound notifications (v1.0.2)
│   │   ├── alerts.py       # Price alerts (v1.0.2)
│   │   ├── trade_journal.py # Trade journal (v1.0.2)
│   │   ├── update_checker.py # Update checker (v1.0.2)
│   │   ├── config_backup.py # Backup/restore (v1.0.2)
│   │   ├── auto_reconnect.py # Auto-reconnect (v1.0.2)
│   │   ├── system_tray.py  # System tray (v1.0.2)
│   │   │
│   │   ├── ibkr/           # IBKR API wrappers
│   │   │   ├── client.py
│   │   │   ├── contracts.py
│   │   │   └── orders.py
│   │   │
│   │   ├── features/       # Trading features
│   │   │   ├── proposer.py
│   │   │   ├── placer.py
│   │   │   ├── show_orders.py
│   │   │   ├── canceller.py
│   │   │   ├── janitor.py
│   │   │   └── manager.py
│   │   │
│   │   └── visual/         # Charting
│   │       └── chart.py
│   │
│   └── resources/          # Static resources
│       ├── config.default.json
│       └── docs/
│
├── tests/                  # Unit tests
│   ├── test_trade_journal.py
│   ├── test_alerts.py
│   ├── test_config_backup.py
│   └── test_update_checker.py
│
├── scripts/                # Build scripts
│   ├── build_exe.bat
│   ├── ibkrbot.spec
│   └── make_release_zip.bat
│
├── .github/                # GitHub configuration
│   ├── workflows/          # CI/CD pipelines
│   │   └── test.yml
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── build_artifacts/        # PyInstaller temp files (gitignored)
└── dist/                   # Final executable output (gitignored)
```

## Running Tests

```bash
# Run unit tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=ibkrbot

# Run smoke test (import verification)
python -m ibkrbot.smoke_test
```

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'ibkrbot'`

**Solution**: You're running from the wrong directory or haven't installed the package.

```bash
# Option A: Install the package
pip install -e .

# Option B: Ensure you're in the project root
cd /path/to/IBKRBot
python -m ibkrbot.main
```

### Issue: `ImportError: cannot import name 'QAction' from 'PySide6.QtWidgets'`

**Solution**: This is fixed in this rebuild. QAction is now imported from `PySide6.QtGui`.

### Issue: `NameError: name 'orders' is not defined` during import

**Solution**: Fixed. No code executes at module import time in the UI modules.

### Issue: Build scripts deleted when cleaning

**Solution**: Fixed. Build scripts are now in `scripts/`, artifacts in `build_artifacts/` and `dist/`.

### Issue: `AttributeError: 'MainWindow' object has no attribute '_on_copy_ticket'`

**Solution**: Fixed. All button handlers are implemented in the fixed main_window.py.

## System Requirements

### Windows
- Windows 10 or 11
- Python 3.11+ (tested with 3.14)
- 4 GB RAM minimum (8 GB recommended)

### Linux / macOS
- See [INSTALL_LINUX_MAC.md](INSTALL_LINUX_MAC.md) for installation instructions
- Pre-built binaries available from GitHub Actions

### Dependencies
- Python 3.11+
- PySide6 (Qt6) - cross-platform GUI
- yfinance - market data
- pandas, numpy - data processing
- ibapi (Interactive Brokers API)
- matplotlib - charting
- PyInstaller (for building executables)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy and how to report vulnerabilities.

## License

MIT License - see [LICENSE](LICENSE) file for details.

**IMPORTANT**: This software is for educational purposes only. Trading involves substantial risk of loss. See the trading disclaimer in the LICENSE file and in the application's About dialog.

## Support

- **Issues**: [GitHub Issues](https://github.com/JrCheesey/IBKRBot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/JrCheesey/IBKRBot/discussions)
