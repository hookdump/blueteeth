<p align="center">
  <img alt="header" src="https://github.com/user-attachments/assets/5c47df6e-a3b6-499a-ad76-03888baba138" width="500" />
</p>

**Blueteeth** is a robust CLI tool for managing Bluetooth audio devices on **Linux** with **PipeWire**.

<p align="center">
  <img width="300" height="300" alt="pipewire_small" src="https://github.com/user-attachments/assets/aa329152-ca24-4690-9883-06e1d35296b1" />
</p>


## Problem
Managing Bluetooth headphones on Linux without a full desktop environment is painful:
- Devices need re-pairing after reboot
- Manual profile switching required
- Inconsistent audio routing
- No simple "just connect" solution

## Solution
`blueteeth` provides simple, reliable Bluetooth audio management:
```bash
# Connect to your headphones
blueteeth connect

# Check status
blueteeth status

# Fix audio issues
blueteeth fix
```

## Features
- One-command connection to Bluetooth headphones
- Automatic A2DP profile selection
- PipeWire audio routing management
- Persistent device memory
- Works great with window managers like Awesome WM

## Requirements
- Linux with PipeWire audio
- BlueZ Bluetooth stack
- Python 3.8+
- No desktop environment required

## Installation
```bash
# Clone the repository
git clone https://github.com/hookdump/blueteeth
cd blueteeth

# Install dependencies
pip install -r requirements.txt

# Run directly
./blueteeth.py --help
```

## Usage
```bash
# List paired devices
blueteeth list

# Connect to last used device
blueteeth connect

# Connect to specific device
blueteeth connect "WH-1000XM4"

# Check connection status
blueteeth status

# Disconnect
blueteeth disconnect

# Fix audio issues (reconnect + reset)
blueteeth fix
```

## Configuration
Config stored in `~/.config/blueteeth/config.json`

## Development
See [PLAN.md](PLAN.md) for development roadmap.

## License
MIT

<img width="1024" height="1024" alt="logo" src="https://github.com/user-attachments/assets/cfb9e908-72db-4f19-a838-3279c3d2a492" />
