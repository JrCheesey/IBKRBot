# Troubleshooting Guide - IBKRBot v2

This guide addresses common issues and their solutions.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Import Errors](#import-errors)
- [Build Issues](#build-issues)
- [Runtime Issues](#runtime-issues)
- [Performance Issues](#performance-issues)

---

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'ibkrbot'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'ibkrbot'
```

**Causes:**
1. Package not installed
2. Running from wrong directory
3. Wrong Python environment active

**Solutions:**

**Option A: Install the package (Recommended)**
```bash
# From project root (folder containing pyproject.toml)
pip install -e .

# Verify installation
python -c "import ibkrbot; print(ibkrbot.__version__)"
```

**Option B: Run from correct directory**
```bash
# Must be in project root (contains ibkrbot/ folder)
cd /path/to/IBKRBot_v2_FIXED
python -m ibkrbot.main
```

**Option C: Check Python environment**
```bash
# Verify you're in the right conda/venv environment
conda activate ibkrbot  # or your environment name
which python  # Linux/Mac
where python  # Windows
```

---

## Import Errors

### Issue: `ImportError: cannot import name 'QAction' from 'PySide6.QtWidgets'`

**Status:** ✅ **FIXED in this rebuild**

**Explanation:**
- In PySide6, `QAction` is in `QtGui`, not `QtWidgets`
- This has been corrected in the fixed main_window.py

**If you still see this:**
```bash
# Verify you're using the fixed version
grep "from PySide6.QtGui import.*QAction" ibkrbot/ui/main_window.py

# Should show: from PySide6.QtGui import QDesktopServices, QFont, QPixmap, QAction
```

### Issue: `NameError: name 'orders' is not defined` at import time

**Status:** ✅ **FIXED in this rebuild**

**Explanation:**
- UI modules had runtime code executing at import time
- All methods are now properly indented as class methods

**Verification:**
```bash
# This should complete without errors
python -c "import ibkrbot.ui.main_window; print('Import successful')"
```

### Issue: `AttributeError: 'MainWindow' object has no attribute '_on_copy_ticket'`

**Status:** ✅ **FIXED in this rebuild**

**Explanation:**
- Method indentation was incorrect (module-level instead of class method)
- All button handlers are now properly implemented

**Verification:**
```bash
# Run smoke test
python -m ibkrbot.smoke_test
```

---

## Build Issues

### Issue: Build scripts deleted when cleaning artifacts

**Status:** ✅ **FIXED in this rebuild**

**New Structure:**
```
scripts/            # Build scripts (preserved)
  ├── build_exe.bat
  ├── ibkrbot.spec
  └── make_release_zip.bat

build_artifacts/    # Temporary files (can delete)
dist/               # Output executables (can delete)
```

**Safe cleaning:**
```batch
rmdir /s /q build_artifacts
rmdir /s /q dist
REM scripts/ folder is preserved!
```

### Issue: PyInstaller fails with "cannot find module"

**Solutions:**

**1. Verify package is installed:**
```bash
pip install -e .
python -m ibkrbot.smoke_test
```

**2. Clean rebuild:**
```batch
rmdir /s /q build_artifacts
rmdir /s /q dist
scripts\build_exe.bat
```

**3. Check spec file paths:**
```bash
# Verify spec file is using correct paths
python scripts/ibkrbot.spec  # Should show detected paths
```

**4. Manual hiddenimports:**
If a specific module is missing, add it to `scripts/ibkrbot.spec`:
```python
hiddenimports = [
    'your.missing.module',
    # ... existing imports
]
```

### Issue: "The system cannot find the path specified" during build

**Cause:** Running from wrong directory

**Solution:**
```batch
REM Always run from project root
cd C:\path\to\IBKRBot_v2_FIXED
scripts\build_exe.bat
```

---

## Runtime Issues

### Issue: Executable launches but immediately closes

**Diagnosis:**
```batch
REM Run from command line to see error messages
cd dist\IBKRBot
IBKRBot.exe

REM Or build with console enabled temporarily
REM Edit scripts\ibkrbot.spec: console=True instead of console=False
```

**Common causes:**
1. Missing dependencies → Check if all required DLLs are in dist folder
2. Resource files not found → Verify config.default.json is in dist/ibkrbot/resources/
3. Python runtime error → Check console output

### Issue: "Cannot connect to IB Gateway"

**Not a build issue** - this is a runtime configuration problem.

**Checklist:**
1. IB Gateway is running
2. API connections enabled in Gateway settings
3. Correct port configured (default: 7497 for paper, 7496 for live)
4. Socket client ID is unique
5. Firewall not blocking connection

### Issue: Charts not displaying

**Solution:**
Matplotlib backend issue. The spec file forces Agg backend (headless).

For GUI charts, you may need to adjust the spec file:
```python
# In scripts/ibkrbot.spec, remove or adjust:
hooksconfig={
    "matplotlib": {"backends": ["Agg"]}
},
```

---

## Performance Issues

### Issue: Build takes a very long time

**Expected:** First build takes 5-15 minutes (normal for PyInstaller)

**Optimization:**
1. Use `--clean` only when needed (removes cached files)
2. Exclude unnecessary packages in spec file
3. Use UPX compression (already enabled)

**If consistently slow:**
```batch
REM Try without UPX (faster build, larger exe)
REM Edit scripts\ibkrbot.spec: upx=False
```

### Issue: Executable is very large (>500 MB)

**Expected:** 200-400 MB is typical for PySide6 + pandas + matplotlib apps

**Reduction strategies:**
1. Check if test packages are excluded (already done in spec)
2. Consider excluding unused matplotlib backends
3. Use UPX compression (already enabled)

**Not recommended:**
- Removing pandas/numpy (core dependencies)
- Aggressive upx settings (can cause issues)

---

## Debugging Tips

### Enable verbose logging

```python
# In ibkrbot/core/logging_setup.py
# Change logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)
```

### Test imports before building

```bash
# Run comprehensive smoke test
python -m ibkrbot.smoke_test

# Test specific import
python -c "from ibkrbot.ui.main_window import MainWindow; print('OK')"

# Check for syntax errors
python -m compileall ibkrbot
```

### Verify package structure

```bash
# After pip install -e .
python -c "import ibkrbot; print(ibkrbot.__file__)"
# Should show path to your project

python -c "from ibkrbot.ui import main_window; print(main_window.__file__)"
# Should show path inside your project
```

### PyInstaller verbose output

```batch
REM Build with verbose logging
pyinstaller --clean --log-level DEBUG scripts\ibkrbot.spec
```

---

## Getting Help

If you're still experiencing issues:

1. **Run smoke test:** `python -m ibkrbot.smoke_test`
2. **Check logs:** Look in `logs/` directory for application logs
3. **Verify environment:**
   ```bash
   python --version  # Should be 3.11+
   pip list | grep -i pyside  # Should show PySide6
   ```
4. **Clean reinstall:**
   ```bash
   pip uninstall ibkrbot
   pip install -e .
   python -m ibkrbot.smoke_test
   ```

---

## Appendix: Quick Reference

### Correct workflow

```bash
# 1. Setup
cd /path/to/IBKRBot_v2_FIXED
pip install -e ".[dev]"

# 2. Test
python -m ibkrbot.smoke_test
python -m compileall ibkrbot

# 3. Run from source
python -m ibkrbot.main

# 4. Build executable
scripts\build_exe.bat

# 5. Test executable
dist\IBKRBot\IBKRBot.exe

# 6. Create release
scripts\make_release_zip.bat
```

### File locations

| Item | Location | Can Delete? |
|------|----------|-------------|
| Source code | `ibkrbot/` | ❌ No |
| Build scripts | `scripts/` | ❌ No |
| Temp build files | `build_artifacts/` | ✅ Yes |
| Built executable | `dist/` | ✅ Yes |
| User data | `ibkrbot_data/` | ⚠️ Contains user plans/config |
| Logs | `logs/` | ⚠️ Contains debugging info |

### Environment check

```bash
# Should all pass
python -m ibkrbot.smoke_test
python -m compileall ibkrbot
python -c "import PySide6; print(PySide6.__version__)"
python -c "from PySide6.QtGui import QAction; print('OK')"
```
