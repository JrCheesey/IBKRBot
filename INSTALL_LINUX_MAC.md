# Installing IBKRBot on Linux and macOS

**⚠️ IMPORTANT**: Linux and macOS builds are **currently untested** as the developer does not have access to these platforms. These instructions are provided for community testing and contributions. Please report any issues on [GitHub Issues](https://github.com/JrCheesey/IBKRBot/issues).

---

## Prerequisites

### All Platforms
- Python 3.11 or higher (tested with 3.14 on Windows)
- IB Gateway or Trader Workstation (TWS) installed
- Interactive Brokers account (paper or live)

### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Fedora/RHEL
sudo dnf install python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git
```

### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11 git
```

---

## Installation Methods

### Option 1: Install from Source (Recommended)

This is the most reliable method since prebuilt binaries are untested.

#### 1. Clone the repository

```bash
git clone https://github.com/JrCheesey/IBKRBot.git
cd IBKRBot
```

#### 2. Create a virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# Linux:
source venv/bin/activate
# macOS:
source venv/bin/activate
```

#### 3. Install dependencies

```bash
# Install IBKRBot in editable mode with all dependencies
pip install -e .
```

#### 4. Run IBKRBot

```bash
# From the project root directory
python -m ibkrbot.main

# Or use the installed command
ibkrbot
```

---

### Option 2: Build Standalone Executable (Experimental)

If you want to create a standalone application without needing to activate a virtual environment:

#### 1. Clone and install (as above)

Follow steps 1-3 from Option 1.

#### 2. Install PyInstaller

```bash
pip install pyinstaller
```

#### 3. Build the executable

```bash
# Make the build script executable
chmod +x scripts/build_exe.sh

# Run the build script
./scripts/build_exe.sh
```

#### 4. Run the built application

**Linux:**
```bash
./dist/IBKRBot/IBKRBot
```

**macOS:**
```bash
open dist/IBKRBot.app
```

Or double-click `IBKRBot.app` in Finder.

---

## IB Gateway Setup

### Linux

1. Download IB Gateway for Linux from [Interactive Brokers](https://www.interactivebrokers.com/en/index.php?f=16457)
2. Install IB Gateway:
   ```bash
   chmod +x ibgateway-*.sh
   ./ibgateway-*.sh
   ```
3. Launch IB Gateway and log in
4. Configure API settings:
   - Enable "Enable ActiveX and Socket Clients"
   - Socket port: **4002** (paper) or **4001** (live)
   - Trusted IP: `127.0.0.1`

### macOS

1. Download IB Gateway for macOS from [Interactive Brokers](https://www.interactivebrokers.com/en/index.php?f=16457)
2. Open the `.dmg` file and drag IB Gateway to Applications
3. Launch IB Gateway from Applications
4. Configure API settings (same as Linux above)

**macOS Security Note**: You may need to allow IB Gateway in System Preferences → Security & Privacy if macOS blocks it.

---

## Configuration

IBKRBot stores configuration and data in platform-specific locations:

- **Linux**: `~/.config/IBKRBot/`
- **macOS**: `~/Library/Application Support/IBKRBot/`

### Directory Structure
```
IBKRBot/
├── config.json          # User settings
├── plans/              # Trading plans
├── logs/               # Application logs
└── thumbs/             # Chart thumbnails
```

On first run, IBKRBot will create these directories automatically.

---

## Troubleshooting

### Linux

**Issue: Qt platform plugin error**
```
qt.qpa.plugin: Could not find the Qt platform plugin "xcb"
```

Solution:
```bash
# Ubuntu/Debian
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Or try
sudo apt install python3-pyqt6 python3-pyqt6.qtcore
```

**Issue: Permission denied when running IB Gateway**
```bash
chmod +x path/to/ibgateway
```

### macOS

**Issue: "IBKRBot.app is damaged and can't be opened"**

This is a Gatekeeper issue with unsigned apps.

Solution:
```bash
# Remove quarantine attribute
xattr -cr dist/IBKRBot.app

# Or allow in System Preferences
# System Preferences → Security & Privacy → General
# Click "Open Anyway" next to the IBKRBot message
```

**Issue: IB Gateway not connecting**

Make sure you've allowed incoming connections for IB Gateway in:
- System Preferences → Security & Privacy → Firewall → Firewall Options

### All Platforms

**Issue: Module not found errors**

Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # Linux/macOS
```

**Issue: Can't connect to IBKR**

1. Verify IB Gateway is running
2. Check the correct port:
   - Paper trading: **4002**
   - Live trading: **4001**
3. Ensure `127.0.0.1` is in IB Gateway's trusted IPs
4. Check IBKRBot settings (Help → Settings)

---

## Running on Startup (Optional)

### Linux (systemd)

Create a systemd user service:

```bash
# Create service file
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/ibkrbot.service
```

Add:
```ini
[Unit]
Description=IBKRBot Trading Assistant
After=network.target

[Service]
Type=simple
ExecStart=/path/to/IBKRBot/venv/bin/python -m ibkrbot.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Enable:
```bash
systemctl --user enable ibkrbot.service
systemctl --user start ibkrbot.service
```

### macOS (launchd)

Create a launch agent:

```bash
# Create plist file
nano ~/Library/LaunchAgents/com.jrcheesey.ibkrbot.plist
```

Add:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jrcheesey.ibkrbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/IBKRBot/venv/bin/python</string>
        <string>-m</string>
        <string>ibkrbot.main</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.jrcheesey.ibkrbot.plist
```

---

## Uninstall

### From Source Install
```bash
# Deactivate virtual environment
deactivate

# Remove cloned repository
rm -rf /path/to/IBKRBot

# Remove user data (optional)
# Linux:
rm -rf ~/.config/IBKRBot
# macOS:
rm -rf ~/Library/Application\ Support/IBKRBot
```

### From Built App
```bash
# Linux
rm -rf dist/IBKRBot

# macOS
rm -rf dist/IBKRBot.app

# Remove user data (optional, same as above)
```

---

## Testing & Feedback

Since these builds are **untested**, we need your help!

### Please test and report:
1. Does the installation work?
2. Does the application launch?
3. Can you connect to IB Gateway?
4. Do all features work correctly?
5. Any errors or crashes?

### Report issues at:
https://github.com/JrCheesey/IBKRBot/issues

Please include:
- Operating system and version
- Python version (`python3 --version`)
- Complete error messages
- Steps to reproduce

---

## Known Limitations

- **Untested**: No testing has been done on Linux or macOS
- **IB Gateway**: You must install IB Gateway separately
- **UI Scaling**: May need adjustment on high-DPI displays
- **Keyboard Shortcuts**: May differ on macOS (Cmd vs Ctrl)

---

## Contributing

Want to help make IBKRBot work better on Linux/macOS?

1. Fork the repository
2. Test on your platform
3. Fix any issues you find
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- **Documentation**: [README.md](README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/JrCheesey/IBKRBot/issues)

---

## License

MIT License - See [LICENSE](LICENSE) for details.

**EDUCATIONAL USE ONLY**: Trading involves substantial risk. See disclaimer in LICENSE file.
