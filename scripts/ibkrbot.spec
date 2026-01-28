# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for IBKRBot v2.

This spec file packages the IBKRBot application for Windows, Linux, and macOS.

Key improvements in this version:
- Uses project root detection that works in all contexts
- Includes all ibkrbot submodules via collect_submodules
- Properly packages resources (config, docs)
- Excludes test packages to reduce size
- Forces Agg backend for matplotlib (headless)
"""
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Detect project root
# SPECPATH is defined by PyInstaller and points to the directory containing this spec file.
# This spec is in scripts/, so project root is SPECPATH/..
try:
    spec_dir = Path(SPECPATH).resolve()  # type: ignore[name-defined]
    project_root = spec_dir.parent
except NameError:
    # Fallback if executed outside PyInstaller context
    project_root = Path.cwd().resolve()
    if not (project_root / "ibkrbot").exists():
        # Try parent directory
        project_root = project_root.parent

print(f"[SPEC] Project root: {project_root}")
print(f"[SPEC] Spec directory: {spec_dir if 'spec_dir' in locals() else 'N/A'}")

# Entry point
entry = project_root / "run_ibkrbot.py"
if not entry.exists():
    raise FileNotFoundError(f"Entry point not found: {entry}")

# Hidden imports - keep minimal to reduce build size
hiddenimports = [
    # Explicitly include UI module (sometimes missed by auto-detection)
    'ibkrbot.ui.main_window',
    'ibkrbot.ui.dialogs',
    'ibkrbot.ui.logging_handler',
    'ibkrbot.ui.theme',

    # Core modules (ensure new modules are included)
    'ibkrbot.core.constants',
    'ibkrbot.core.ibkr.error_codes',

    # yfinance and its dependencies
    "yfinance",

    # Matplotlib backend (force Agg for headless)
    "matplotlib.backends.backend_agg",
]

# Collect all IB API submodules (small package, safe to collect all)
hiddenimports += collect_submodules("ibapi")

# Collect all ibkrbot submodules to ensure nothing is missed
hiddenimports += collect_submodules("ibkrbot")

# Exclude test packages and optional dependencies to reduce size
excludes = [
    # Testing frameworks (keep unittest - pyparsing needs it)
    "pytest",
    "hypothesis",

    # Test packages from dependencies
    "pandas.tests",
    "numpy.tests",
    "matplotlib.tests",
    "matplotlib.testing",
    "numpy.f2py.tests",

    # Optional/heavy dependencies we don't use
    "pyarrow",
    "IPython",
    "jupyter",
    "notebook",

    # Development tools
    "pylint",
    "black",
    "mypy",
]

# Data files to include in the build
datas = [
    # Default configuration file
    (str(project_root / "ibkrbot" / "resources" / "config.default.json"), "ibkrbot/resources"),
    
    # Documentation files
    (str(project_root / "ibkrbot" / "resources" / "docs"), "ibkrbot/resources/docs"),
]

print(f"[SPEC] Entry point: {entry}")
print(f"[SPEC] Data files: {len(datas)} items")
print(f"[SPEC] Hidden imports: {len(hiddenimports)} modules")

a = Analysis(
    [str(entry)],
    pathex=[str(project_root), str(project_root / 'ibkrbot')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={
        # Force matplotlib to use Agg backend (headless, no GUI)
        "matplotlib": {"backends": ["Agg"]}
    },
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IBKRBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed mode (no console window)
    icon=None,  # Add icon path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IBKRBot",
)

# macOS: Create .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="IBKRBot.app",
        icon=None,  # Add .icns icon here if available
        bundle_identifier="com.jrcheesey.ibkrbot",
        info_plist={
            "CFBundleName": "IBKRBot",
            "CFBundleDisplayName": "IBKRBot",
            "CFBundleVersion": "1.0.1",
            "CFBundleShortVersionString": "1.0.1",
            "NSHighResolutionCapable": "True",
            "LSMinimumSystemVersion": "10.13.0",
        },
    )
