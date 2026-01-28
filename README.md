# IBKRBot v1.0.1

A Windows desktop application for Interactive Brokers swing trading with full paper and live trading support.

## ✨ Features

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

## Key Fixes in This Rebuild

✅ **QAction Import Fixed**: Imports from `PySide6.QtGui` (not QtWidgets)
✅ **Import-Safe UI**: No runtime code executes at module import time
✅ **Proper Package Structure**: Uses `pyproject.toml` for installable package
✅ **Defensive Coding**: Guards against None, empty lists, missing dict keys
✅ **Clean Build Process**: Build scripts separated from artifacts
✅ **PyInstaller Ready**: Proper spec file with all resources included
✅ **Smoke Test Included**: Can verify imports without launching GUI

## Installation & Setup

### 1. Install Package (Editable Mode)

```bash
# From the project root (folder containing pyproject.toml)
pip install -e .

# Or install with dev dependencies (includes PyInstaller)
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

# Should output: "✅ Smoke test passed! All imports successful."
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
IBKRBot_v2_FIXED/
├── pyproject.toml          # Package configuration (NEW!)
├── README.md               # This file
├── run_ibkrbot.py          # Simple entry wrapper for PyInstaller
├── requirements.txt        # Deprecated (use pyproject.toml)
│
├── ibkrbot/                # Main package
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── smoke_test.py      # Import verification (NEW!)
│   │
│   ├── ui/                # GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py  # FIXED: QAction from QtGui, import-safe
│   │   ├── dialogs.py
│   │   └── logging_handler.py
│   │
│   ├── core/              # Business logic
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging_setup.py
│   │   ├── paths.py
│   │   ├── plan.py
│   │   ├── data_sources.py
│   │   ├── task_runner.py
│   │   │
│   │   ├── ibkr/          # IBKR API wrappers
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── contracts.py
│   │   │   └── orders.py
│   │   │
│   │   ├── features/      # Trading features
│   │   │   ├── __init__.py
│   │   │   ├── proposer.py
│   │   │   ├── placer.py
│   │   │   ├── show_orders.py
│   │   │   ├── canceller.py
│   │   │   ├── janitor.py
│   │   │   └── manager.py
│   │   │
│   │   └── visual/        # Charting
│   │       └── chart.py
│   │
│   └── resources/         # Static resources
│       ├── config.default.json
│       └── docs/
│           ├── START_HERE.txt
│           ├── SETUP_CHECKLIST.txt
│           └── README.txt
│
├── scripts/               # Build scripts (NEW! separated from artifacts)
│   ├── build_exe.bat     # PyInstaller build script
│   ├── ibkrbot.spec      # PyInstaller spec file
│   └── make_release_zip.bat
│
├── build_artifacts/       # PyInstaller temp files (gitignored)
└── dist/                  # Final executable output (gitignored)
```

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'ibkrbot'`

**Solution**: You're running from the wrong directory or haven't installed the package.

```bash
# Option A: Install the package
pip install -e .

# Option B: Ensure you're in the project root
cd /path/to/IBKRBot_v2_FIXED
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

## Development

### Running Tests

```bash
# Import smoke test
python -m ibkrbot.smoke_test

# Full compile check
python -m compileall ibkrbot
```

### Cleaning Build Artifacts

```bash
# Windows
rmdir /s /q build_artifacts
rmdir /s /q dist

# Note: scripts/ folder is preserved!
```

## Requirements

- Python 3.11+
- PySide6 (Qt6)
- yfinance
- pandas
- numpy
- ibapi (Interactive Brokers API)
- matplotlib
- PyInstaller (for building exe)

## License

MIT License - see [LICENSE](LICENSE) file for details.

**IMPORTANT**: This software is for educational purposes only. Trading involves substantial risk of loss. See the trading disclaimer in the LICENSE file and in the application's About dialog.

## Support

For issues or questions, please open an issue on GitHub: https://github.com/JrCheesey/IBKRBot/issues
