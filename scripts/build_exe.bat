@echo off
REM ============================================================================
REM IBKRBot v2 - PyInstaller Build Script
REM ============================================================================
REM
REM This script builds the Windows executable for IBKRBot.
REM
REM Prerequisites:
REM   - Python 3.11+ with conda/venv activated
REM   - PyInstaller installed (pip install pyinstaller)
REM   - All dependencies installed (pip install -e .)
REM
REM Output:
REM   - dist\IBKRBot\IBKRBot.exe (main executable)
REM   - build_artifacts\ (temporary build files, can be deleted)
REM
REM Usage:
REM   Run from project root: scripts\build_exe.bat
REM
REM ============================================================================

echo.
echo ============================================================================
echo  IBKRBot v2 - Building Windows Executable
echo ============================================================================
echo.

REM Change to project root (parent of scripts directory)
cd /d "%~dp0.."
echo Current directory: %CD%
echo.

REM Check if pyinstaller is available
where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller not found!
    echo Please install it: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Check if ibkrbot package exists
if not exist "ibkrbot" (
    echo ERROR: ibkrbot package not found in current directory!
    echo Make sure you're running this from the project root.
    echo.
    pause
    exit /b 1
)

echo [1/4] Cleaning previous build artifacts...
if exist "build_artifacts" rmdir /s /q "build_artifacts"
if exist "dist" rmdir /s /q "dist"
echo       Cleaned.
echo.

echo [2/4] Running PyInstaller...
echo       This may take several minutes...
echo.

pyinstaller --clean ^
    --workpath build_artifacts\build ^
    --distpath dist ^
    scripts\ibkrbot.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Check the error messages above for details.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] Verifying build output...

if not exist "dist\IBKRBot\IBKRBot.exe" (
    echo ERROR: IBKRBot.exe not found in dist\IBKRBot\
    echo Build may have failed silently.
    echo.
    pause
    exit /b 1
)

echo       ✓ IBKRBot.exe found
echo.

REM Get file size
for %%A in ("dist\IBKRBot\IBKRBot.exe") do set size=%%~zA
echo       Size: %size% bytes
echo.

echo [4/4] Build complete!
echo.
echo ============================================================================
echo  Build successful!
echo ============================================================================
echo.
echo Executable location:
echo   %CD%\dist\IBKRBot\IBKRBot.exe
echo.
echo You can now:
echo   1. Test the executable by running: dist\IBKRBot\IBKRBot.exe
echo   2. Distribute the entire dist\IBKRBot\ folder
echo   3. Create a release zip: scripts\make_release_zip.bat
echo.
echo Temporary build files are in: build_artifacts\
echo (You can safely delete this folder)
echo.
echo ============================================================================
echo.
pause
