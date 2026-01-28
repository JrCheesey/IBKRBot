@echo off
REM ============================================================================
REM IBKRBot v2 - Release ZIP Creator
REM ============================================================================
REM
REM This script creates a release ZIP file containing the built executable
REM and documentation.
REM
REM Prerequisites:
REM   - dist\IBKRBot\ folder must exist (run build_exe.bat first)
REM   - PowerShell available (for Compress-Archive)
REM
REM Output:
REM   - dist\IBKRBot_v2_release_YYYYMMDD_HHMMSS.zip
REM
REM Usage:
REM   Run from project root: scripts\make_release_zip.bat
REM
REM ============================================================================

echo.
echo ============================================================================
echo  IBKRBot v2 - Creating Release ZIP
echo ============================================================================
echo.

REM Change to project root
cd /d "%~dp0.."
echo Current directory: %CD%
echo.

REM Check if dist\IBKRBot exists
if not exist "dist\IBKRBot" (
    echo ERROR: dist\IBKRBot folder not found!
    echo Please run build_exe.bat first to create the executable.
    echo.
    pause
    exit /b 1
)

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found!
    echo This script requires PowerShell for creating ZIP files.
    echo.
    pause
    exit /b 1
)

REM Generate timestamp for filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

set RELEASE_NAME=IBKRBot_v2_release_%timestamp%
set ZIP_PATH=dist\%RELEASE_NAME%.zip

echo [1/2] Creating release ZIP file...
echo       Source: dist\IBKRBot\
echo       Output: %ZIP_PATH%
echo.

REM Use PowerShell to create ZIP
powershell -Command "Compress-Archive -Path 'dist\IBKRBot\*' -DestinationPath '%ZIP_PATH%' -Force"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create ZIP file!
    echo.
    pause
    exit /b 1
)

echo [2/2] Verifying ZIP file...

if not exist "%ZIP_PATH%" (
    echo ERROR: ZIP file was not created!
    echo.
    pause
    exit /b 1
)

REM Get file size
for %%A in ("%ZIP_PATH%") do set size=%%~zA
echo       ✓ ZIP file created
echo       Size: %size% bytes
echo.

echo ============================================================================
echo  Release ZIP created successfully!
echo ============================================================================
echo.
echo ZIP file location:
echo   %CD%\%ZIP_PATH%
echo.
echo This ZIP contains the complete IBKRBot application.
echo You can distribute this file to end users.
echo.
echo To install:
echo   1. Extract the ZIP to any folder
echo   2. Run IBKRBot.exe
echo.
echo ============================================================================
echo.
pause
