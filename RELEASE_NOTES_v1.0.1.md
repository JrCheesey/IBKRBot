# IBKRBot v1.0.1 - Initial Public Release

Windows desktop application for Interactive Brokers swing trading with full paper and live trading support.

## ⚠️ IMPORTANT DISCLAIMER

**This software is for EDUCATIONAL PURPOSES ONLY.** Trading involves substantial risk of loss. You are solely responsible for your trading decisions. See the [LICENSE](https://github.com/JrCheesey/IBKRBot/blob/main/LICENSE) file for full disclaimer.

---

## 🎯 What's New in v1.0.1

### Paper & Live Trading Mode Selector
- **Dropdown selector** in toolbar to switch between paper and live trading modes
- **Multi-step confirmation** when switching to live mode:
  - Comprehensive warning about real money risks
  - Requires typing "LIVE" to confirm
  - Final yes/no confirmation dialog
- **Visual indicators** throughout UI showing current mode:
  - Color-coded dropdown (gray for paper, light red for live)
  - Mode displayed in window title
  - Connection status shows current mode
  - Mode-specific warning labels

### Enhanced Safety Features
- Live mode protection prevents accidental real trading
- Mode-aware connection workflow with reconnection prompts
- Immediate visual feedback when switching modes

---

## ✨ Core Features

### Trading Capabilities
- **ATR-Based Swing Strategy**: Automated plan generation using ATR pullback methodology
- **Free Market Data**: Yahoo Finance integration (no paid data feeds required)
- **Bracket Orders**: Automated entry, stop-loss, and take-profit placement
- **Draft Plan System**: Review and approve plans before placing orders
- **Position Management**: View orders, positions, and manage risk in real-time
- **Automated Janitor**: Auto-cancel orders before market close
- **Manager Loop**: Automated position monitoring and management

### User Experience
- **First-Run Wizard**: Welcome screen with setup guidance
- **Market Hours Awareness**: Warnings when market is closed
- **Keyboard Shortcuts**: F1 for help, quick navigation
- **Enhanced Error Messages**: 25+ IBKR error codes with clear explanations
- **Visual Charting**: Price chart thumbnails with trade levels
- **Risk Gauges**: Real-time position size and risk visualization

### Safety & Compliance
- **Input Validation**: Prevents invalid configurations
- **Comprehensive Logging**: File-based logs with rotation
- **MIT License**: Open source with full trading disclaimers
- **About Dialog**: Legal disclaimers and risk warnings

---

## 💻 System Requirements

- **Operating System**: Windows 10 or Windows 11
- **IB Gateway**: TWS or IB Gateway installed and running
- **Memory**: 4 GB RAM minimum (8 GB recommended)
- **Disk Space**: 200 MB free space
- **Account**: Interactive Brokers account (paper or live)

---

## 📥 Installation

### Option 1: Download Executable (Easiest)

1. **Download** `IBKRBot-v1.0.1-Windows.zip` from this release
2. **Extract** the ZIP file to a folder (e.g., `C:\IBKRBot`)
3. **Run** `IBKRBot.exe` from the extracted folder
4. **Configure** IB Gateway connection on first launch

**Note**: Windows may show a SmartScreen warning for unsigned applications. Click "More info" → "Run anyway" to proceed.

### Option 2: Install from Source

See the [README](https://github.com/JrCheesey/IBKRBot#installation--setup) for detailed installation instructions from source code.

---

## 🚀 Quick Start

1. **Start IB Gateway** or TWS and log in
   - Paper trading: Use port **4002**
   - Live trading: Use port **4001**

2. **Launch IBKRBot.exe**
   - First run shows welcome wizard with setup instructions

3. **Configure Settings** (Help → Settings)
   - Set paper/live mode
   - Configure risk limits (max position size, max loss per trade)
   - Adjust strategy parameters (ATR period, pullback %, etc.)

4. **Connect to IBKR**
   - Click "Connect" button
   - Grant permissions in IB Gateway when prompted

5. **Generate a Trading Plan**
   - Select a symbol from the dropdown
   - Click "Propose + Save Draft"
   - Review the generated plan with entry, stop, and take profit levels

6. **Place Orders** (after review)
   - Click "Place Bracket (Draft)" to submit orders to IBKR
   - Orders appear in the "Orders & Positions" table

---

## 📖 Documentation

- **README**: [Full documentation](https://github.com/JrCheesey/IBKRBot/blob/main/README.md)
- **Quick Start**: [QUICKSTART.md](https://github.com/JrCheesey/IBKRBot/blob/main/QUICKSTART.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](https://github.com/JrCheesey/IBKRBot/blob/main/TROUBLESHOOTING.md)
- **Changelog**: [CHANGELOG.md](https://github.com/JrCheesey/IBKRBot/blob/main/CHANGELOG.md)

---

## ⚙️ Default Configuration

**Risk Management** (can be adjusted in Settings):
- Max position size: 5% of net liquidation value
- Max loss per trade: 0.5% of net liquidation value
- R-multiple for take profit: 2.0

**Strategy Parameters**:
- ATR period: 14 bars
- Pullback: 50% of ATR
- Stop loss: 2.0 × ATR below entry
- Limit offset: 0.1 × ATR below calculated entry

---

## 🐛 Known Issues

- **Paper Account NetLiq**: Paper accounts may show $1,000,000 net liquidation value (this is normal for IBKR paper accounts)
- **Market Hours**: Market hours check is simplified and doesn't account for early closes or holidays
- **Windows Only**: Currently only supports Windows (Linux/Mac support planned for future releases)

---

## 🔧 Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/JrCheesey/IBKRBot/issues)
- **Documentation**: See the [README](https://github.com/JrCheesey/IBKRBot) for detailed guides
- **License**: [MIT License](https://github.com/JrCheesey/IBKRBot/blob/main/LICENSE) with trading disclaimers

---

## 📝 Changelog

See [CHANGELOG.md](https://github.com/JrCheesey/IBKRBot/blob/main/CHANGELOG.md) for complete version history.

### v1.0.1 Highlights
- Added paper/live mode selector with safety confirmations
- Enhanced visual indicators for current trading mode
- Fixed QLineEdit import bug in confirmation dialog
- Updated repository URL

### v1.0.0 Highlights
- Initial public release
- MIT License with comprehensive disclaimers
- Full ATR-based swing trading strategy
- Enhanced UI with keyboard shortcuts and first-run wizard
- 25+ error code mappings with clear explanations

---

## ⚖️ License

MIT License - See [LICENSE](https://github.com/JrCheesey/IBKRBot/blob/main/LICENSE) for details.

**EDUCATIONAL USE ONLY**: This software does not provide investment advice. All trading decisions are your responsibility. You may lose money. The author is not liable for any losses.

---

**Built with**: Python 3.14, PySide6 (Qt6), Interactive Brokers API, Yahoo Finance

**Author**: Joshua Metcalf ([@JrCheesey](https://github.com/JrCheesey))

**Repository**: https://github.com/JrCheesey/IBKRBot
