#!/bin/bash
# Cross-platform build script for IBKRBot (Linux/macOS)

set -e  # Exit on error

echo "========================================="
echo "Building IBKRBot for $(uname -s)"
echo "========================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller not found"
    echo "Install with: pip install pyinstaller"
    exit 1
fi

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# Run PyInstaller
echo "Running PyInstaller..."
pyinstaller scripts/ibkrbot.spec --noconfirm

echo ""
echo "========================================="
echo "Build complete!"
echo "========================================="

if [ "$(uname -s)" = "Darwin" ]; then
    echo "Output: dist/IBKRBot.app (macOS Application Bundle)"
    echo ""
    echo "To run: open dist/IBKRBot.app"
else
    echo "Output: dist/IBKRBot/IBKRBot (Linux Executable)"
    echo ""
    echo "To run: ./dist/IBKRBot/IBKRBot"
fi

echo ""
echo "Note: This is an untested build for $(uname -s)."
echo "Please report any issues at:"
echo "https://github.com/JrCheesey/IBKRBot/issues"
