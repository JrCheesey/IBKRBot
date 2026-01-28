# Quick Start Guide - IBKRBot v2

Get up and running in 5 minutes.

## Prerequisites

- Windows 10+ (for building .exe)
- Python 3.11+ installed
- Conda or venv recommended
- IB Gateway installed (for actual trading)

---

## Installation

### Step 1: Clone/Extract Project

```bash
cd /path/to/IBKRBot_v2_FIXED
```

### Step 2: Install Package

```bash
# Install in editable mode
pip install -e .

# Or with dev dependencies (includes PyInstaller)
pip install -e ".[dev]"
```

**That's it!** The package is now installed.

---

## Running the Application

### From Anywhere (After Installation)

```bash
# Method 1: Command
ibkrbot

# Method 2: Module
python -m ibkrbot.main
```

### Without Installation (Must be in project root)

```bash
cd /path/to/IBKRBot_v2_FIXED
python -m ibkrbot.main
```

---

## Verify Installation

```bash
# Quick smoke test (30 seconds)
python -m ibkrbot.smoke_test

# Should output:
# ✅ Smoke test passed! All imports successful.
```

---

## First Run

1. **Launch the application:**
   ```bash
   python -m ibkrbot.main
   ```

2. **The GUI will open** - you should see:
   - Connection controls at the top
   - Workflow panel on the left
   - Proposal preview in the center
   - Log output at the bottom

3. **Connect to IB Gateway** (if available):
   - Start IB Gateway with API enabled
   - Click "Connect" button
   - NetLiq should display

4. **Test a proposal** (paper trading):
   - Select a symbol (e.g., SPY)
   - Click "Propose + Save Draft"
   - Review the bracket plan
   - (Don't place unless you're ready!)

---

## Building Windows Executable

### Quick Build

```batch
scripts\build_exe.bat
```

Output: `dist\IBKRBot\IBKRBot.exe`

### Create Release ZIP

```batch
scripts\make_release_zip.bat
```

Output: `dist\IBKRBot_v2_release_YYYYMMDD_HHMMSS.zip`

---

## Troubleshooting

### Can't import ibkrbot?

```bash
# Install the package
pip install -e .

# Verify
python -c "import ibkrbot; print('OK')"
```

### Application won't launch?

```bash
# Check dependencies
pip list | grep -i pyside

# Should show PySide6
```

### Build fails?

```bash
# Clean and rebuild
rmdir /s /q build_artifacts
rmdir /s /q dist
scripts\build_exe.bat
```

**For more help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## Configuration

Configuration file: `ibkrbot/resources/config.default.json`

After first run, user config: `ibkrbot_data/config.json`

Key settings:
- **IBKR mode**: "paper" or "live" (BE CAREFUL!)
- **Port**: 7497 (paper) or 7496 (live)
- **Risk limits**: Max notional, max loss per trade

---

## File Locations

| Item | Location | Purpose |
|------|----------|---------|
| User data | `ibkrbot_data/` | Your plans and config |
| Logs | `logs/` | Debug information |
| Charts | `ibkrbot_data/charts/` | Saved chart images |
| Executable | `dist/IBKRBot/` | Built Windows app |

---

## Next Steps

1. ✅ **Read the README** - [README.md](README.md)
2. ✅ **Configure settings** - Edit config.json after first run
3. ✅ **Connect IB Gateway** - Enable API, use correct port
4. ✅ **Test in paper mode** - ALWAYS test before live trading
5. ✅ **Review troubleshooting** - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Safety Reminders

⚠️ **PAPER TRADING FIRST** - Always test thoroughly in paper mode

⚠️ **RISK LIMITS** - Set appropriate limits in config.json

⚠️ **MANUAL REVIEW** - Always review trades before placing

⚠️ **IB GATEWAY** - Keep it running while application is active

---

## Support

- See [README.md](README.md) for detailed documentation
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [HANDOFF_TO_CLAUDE_CODE.md](HANDOFF_TO_CLAUDE_CODE.md) for technical details

---

**Enjoy trading with IBKRBot v2! 🚀**
