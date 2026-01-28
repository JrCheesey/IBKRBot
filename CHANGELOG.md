# Changelog

All notable changes to IBKRBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-27

### Added
- **Paper and Live Trading Mode Selector**: Dropdown in toolbar to switch between paper and live trading modes
- **Live Mode Protection**: Multi-step confirmation dialog when switching to live trading
  - Requires typing "LIVE" to enable confirmation button
  - Final yes/no confirmation after initial dialog
  - Comprehensive warning about real money risks
- **Visual Mode Indicators**: Color-coded UI elements showing current trading mode
  - Subtle gray styling for paper mode dropdown
  - Light red styling for live mode dropdown with bold text
  - Mode displayed in window title (e.g., "IBKRBot v1.0.1 - PAPER")
  - Connection status shows mode (e.g., "Connected (LIVE)")
  - Paper/Live note label updates immediately when mode changes
- **Mode-Aware Connection Status**: Enhanced status display showing current mode and connection state

### Changed
- Updated application description to reflect live trading support
- Enhanced connection workflow to handle mode changes with reconnection prompts
- Improved visual feedback throughout UI for current trading mode
- Updated GitHub repository URL to https://github.com/JrCheesey/IBKRBot

### Fixed
- Missing QLineEdit import that caused confirmation dialog to fail silently
- Paper note label not updating when switching modes (now updates immediately)

## [1.0.0] - 2026-01-27

### Added
- **Initial Public Release** with comprehensive trading features
- **MIT License**: Open source license with educational trading disclaimer
- **Enhanced About Dialog**:
  - Full application information with version number
  - Comprehensive legal disclaimers about trading risks
  - Link to GitHub repository
  - Author and copyright information
- **First-Run Welcome Wizard**:
  - Welcome screen on first launch
  - Setup guidance and quick start instructions
  - IB Gateway setup checklist
  - "Don't show again" option
- **Market Hours Awareness**:
  - Automatic market hours checking (9:30 AM - 4:00 PM ET)
  - Warning dialog when attempting to connect outside market hours
  - Bypass option for extended hours trading
- **Keyboard Shortcuts**:
  - F1: Opens comprehensive keyboard shortcuts help dialog
  - Quick navigation and productivity enhancements
- **Enhanced Error Handling**:
  - 25+ IBKR error code mappings with clear explanations
  - Actionable error messages with suggested solutions
  - Detailed error descriptions for common issues
  - Algorithm-specific error messages (e.g., zero quantity calculations)
- **Input Validation**:
  - Validation for all user inputs in settings dialog
  - Clear error messages for invalid values
  - Prevents invalid configurations from being saved

### Core Trading Features
- **ATR-Based Swing Strategy**: Automated swing trading plan generation using ATR pullback methodology
- **Free Data Integration**: Yahoo Finance (yfinance) for historical price data
- **Draft Plan System**: Save and review trading plans before placement
- **Bracket Orders**: Automated entry, stop-loss, and take-profit order placement
- **Order Management**:
  - View all orders and positions
  - Refresh current positions
  - Cancel individual symbol brackets
  - Cancel all open orders
- **Automated Janitor**: Auto-cancel orders 20 minutes before market close
- **Position Manager**: Automated position monitoring and management loop with start/stop controls
- **Risk Management**:
  - Configurable position size limits (% of net liquidation)
  - Maximum loss per trade limits
  - R-multiple take profit targets
  - Visual risk gauges and warnings
- **Visual Charting**: Price chart thumbnails with entry, stop, and take profit levels

### Technical Implementation
- **Clean Architecture**: Modular package structure with core business logic separated from UI
- **PySide6/Qt6 GUI**: Modern, responsive desktop interface
- **IBKR API Integration**: Full integration with Interactive Brokers API via IB Gateway
- **Task Runner System**: Asynchronous task execution with progress reporting
- **Comprehensive Logging**: File-based logging with rotation and UI log viewer
- **Configuration Management**: JSON-based configuration with user settings persistence
- **PyInstaller Build**: Windows executable build system with proper resource bundling

### Documentation
- **README.md**: Comprehensive project documentation with installation instructions
- **QUICKSTART.md**: Quick start guide for new users
- **TROUBLESHOOTING.md**: Common issues and solutions
- **BUILD_SUMMARY.md**: Build process documentation
- **In-App Documentation**: START_HERE.txt, SETUP_CHECKLIST.txt, README.txt in resources

### Package Structure
- Proper Python package with `pyproject.toml`
- Editable installation support (`pip install -e .`)
- Smoke test for verifying imports
- Separated build scripts from source code
- Comprehensive `.gitignore` for clean repository

## [Unreleased]

### Planned Features
- Dark theme support (color palette already defined)
- Multi-symbol portfolio management
- Advanced charting with technical indicators
- Trade history and performance analytics
- Automated strategy backtesting
- Email/SMS notifications for order fills
- Custom strategy plugins

---

## Version History Summary

- **v1.0.1** (2026-01-27): Added paper/live mode selector with safety confirmations
- **v1.0.0** (2026-01-27): Initial public release with full feature set

---

## Links

- [GitHub Repository](https://github.com/JrCheesey/IBKRBot)
- [Issue Tracker](https://github.com/JrCheesey/IBKRBot/issues)
- [License](LICENSE)
