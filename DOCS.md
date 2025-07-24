# Blueteeth Documentation

Blueteeth is a command-line tool for managing Bluetooth audio devices on Linux systems using PipeWire. It provides reliable connectivity and easy switching between audio outputs.

## Table of Contents

- [Installation](#installation)
- [Commands](#commands)
  - [connect](#connect)
  - [disconnect](#disconnect)
  - [status](#status)
  - [list](#list)
  - [switch](#switch)
  - [pair](#pair)
  - [remove](#remove)
  - [fix](#fix)
  - [diagnose](#diagnose)
- [Common Workflows](#common-workflows)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation

```bash
# Clone the repository
git clone https://github.com/hookdump/blueteeth.git
cd blueteeth

# Install dependencies
pip install -r requirements.txt

# Make executable
chmod +x blueteeth.py

# Optionally, create a system-wide symlink
sudo ln -s $(pwd)/blueteeth.py /usr/local/bin/blueteeth
```

## Commands

### connect

Connect to a Bluetooth audio device and set it as the default audio output.

```bash
# Connect to the last used device or first available paired device
./blueteeth.py connect

# Connect to a specific device by name (partial match supported)
./blueteeth.py connect "Sony WH-1000XM4"
./blueteeth.py connect sony
```

**What it does:**
1. Searches for the specified device (or uses last connected/first available)
2. Establishes Bluetooth connection
3. Waits for PipeWire to detect the audio sink
4. Automatically switches audio output to the Bluetooth device

### disconnect

Disconnect the currently connected Bluetooth audio device.

```bash
./blueteeth.py disconnect
```

**What it does:**
1. Finds the currently connected device
2. Disconnects it via bluetoothctl
3. Audio output will fall back to the next available sink

### status

Show the current connection status and audio configuration.

```bash
./blueteeth.py status
```

**Output includes:**
- Currently connected device (if any)
- MAC address
- Trust status
- Audio sink information
- Whether the device is set as default audio output
- Last connected device (stored in config)

**Example output:**
```
Connected to: Sony WH-1000XM4
MAC: 00:18:09:A1:B2:C3
Trusted: yes
Audio sink: bluez_output.00_18_09_A1_B2_C3.1 (ID: 45)
Audio output: ✓ Active
```

### list

List all paired Bluetooth devices.

```bash
./blueteeth.py list
```

**Output includes:**
- Device name
- MAC address
- Connection status
- Trust status

**Example output:**
```
Paired devices:
  • Sony WH-1000XM4 - 00:18:09:A1:B2:C3 (connected, trusted)
  • JBL Flip 5 - AA:BB:CC:DD:EE:FF (trusted)
```

### switch

Switch audio output to a different sink (useful for switching away from Bluetooth).

```bash
# Interactive mode - shows all available sinks and lets you choose
./blueteeth.py switch

# Direct mode - switch to a specific sink by ID
./blueteeth.py switch 32
```

**What it does:**
1. Lists all available audio sinks (both Bluetooth and non-Bluetooth)
2. Shows which sink is currently active
3. Allows selection by sink ID
4. Switches the default audio output to the selected sink

**Example interactive output:**
```
Available audio outputs:

Bluetooth sinks:
  45. bluez_output.00_18_09_A1_B2_C3.1 * (current)

Other audio outputs:
  32. Samsung Monitor HDMI

Select sink ID number (or 'c' to cancel): 32

Switching audio output to: Samsung Monitor HDMI
✓ Audio output switched successfully

Tip: To reconnect Bluetooth audio, run 'blueteeth connect'
```

### pair

Pair a new Bluetooth device interactively.

```bash
# Interactive pairing with device selection
./blueteeth.py pair

# Search for devices with specific name
./blueteeth.py pair "Sony"
```

**Pairing process:**
1. Prompts you to put device in pairing mode
2. Scans for available devices (10 seconds)
3. Shows list of discovered devices
4. Allows selection of device to pair
5. Performs pairing and trust operations
6. Attempts to connect and set up audio

**Example output:**
```
🎧 Bluetooth Device Pairing

Please put your Bluetooth device in pairing mode:
  • For most headphones: Hold power button for 5-7 seconds
  • Look for blinking blue/red LED
  • You may hear 'Bluetooth pairing' announcement

Is your device in pairing mode? [y/N]: y

🔍 Scanning for devices...

Found 2 new device(s):

  1. Sony WH-1000XM4 (00:18:09:A1:B2:C3)
  2. Unknown (11:22:33:44:55:66)

Select device number (or 'c' to cancel): 1

📡 Pairing with Sony WH-1000XM4...
✅ Pairing successful

🔌 Connecting...
✅ Connected successfully
⏳ Waiting for audio device...
✅ Audio output switched to bluez_output.00_18_09_A1_B2_C3.1

🎉 Setup complete! Your device is ready to use.
```

### remove

Remove a paired Bluetooth device.

```bash
# Interactive removal with device selection
./blueteeth.py remove

# Remove specific device by name
./blueteeth.py remove "JBL Flip"
```

**What it does:**
1. Shows list of paired devices (if interactive)
2. Confirms removal
3. Disconnects device if currently connected
4. Removes device from system
5. Cleans up configuration

### fix

Attempt to fix common Bluetooth audio issues.

```bash
./blueteeth.py fix
```

**Troubleshooting steps:**
1. Checks current connection and audio sink status
2. Attempts to set correct default audio output
3. Offers to reconnect device if needed
4. Can perform advanced troubleshooting:
   - Power cycle Bluetooth adapter
   - Restart PipeWire services
   - Reconnect device

**When to use:**
- Audio is not working despite device being connected
- Wrong audio profile is selected
- Audio sink not detected by PipeWire
- After system sleep/resume issues

### diagnose

Run comprehensive diagnostics on Bluetooth and audio system.

```bash
./blueteeth.py diagnose
```

**Diagnostic information:**
- Bluetooth adapter status (name, power, discovery mode)
- List of paired devices and their status
- PipeWire service status
- Available Bluetooth audio sinks
- Common issues detection

**Example output:**
```
🔍 Running Bluetooth & Audio Diagnostics

Bluetooth Adapter:
  Name: hci0
  Powered: yes
  Discovering: no
  Pairable: yes

Paired Devices:
  • Sony WH-1000XM4 (00:18:09:A1:B2:C3) - connected

Audio System:
  ✓ PipeWire is running
  ✓ Bluetooth audio sink found: bluez_output.00_18_09_A1_B2_C3.1

Common Issues Check:
  ✓ All systems operational
```

## Common Workflows

### First Time Setup

```bash
# 1. Put your headphones in pairing mode
# 2. Pair the device
./blueteeth.py pair

# Device is now paired, trusted, and connected
```

### Daily Use

```bash
# Morning: Turn on headphones and connect
./blueteeth.py connect

# Evening: Disconnect when done
./blueteeth.py disconnect
```

### Switching Audio Outputs

```bash
# Switch from Bluetooth to speakers
./blueteeth.py switch

# Later, reconnect to Bluetooth
./blueteeth.py connect
```

### After System Reboot

```bash
# Bluetooth devices often need reconnection after reboot
./blueteeth.py connect

# If that doesn't work
./blueteeth.py fix
```

### Managing Multiple Devices

```bash
# List all devices
./blueteeth.py list

# Connect to specific device
./blueteeth.py connect "Office Headphones"

# Remove old device
./blueteeth.py remove "Old Earbuds"
```

## Configuration

Blueteeth stores its configuration in `~/.config/blueteeth/config.json`.

**Configuration includes:**
- `last_device`: MAC address of the last connected device
- `trusted_devices`: List of trusted device MAC addresses
- `default_profile`: Audio profile preference (default: "a2dp_sink")

**Example config:**
```json
{
  "last_device": "00:18:09:A1:B2:C3",
  "trusted_devices": [
    "00:18:09:A1:B2:C3",
    "AA:BB:CC:DD:EE:FF"
  ],
  "default_profile": "a2dp_sink"
}
```

## Troubleshooting

### Device won't connect

1. Ensure device is in pairing mode
2. Check if already connected to another device
3. Try removing and re-pairing:
   ```bash
   ./blueteeth.py remove "Device Name"
   ./blueteeth.py pair
   ```

### No audio after connection

1. Run the fix command:
   ```bash
   ./blueteeth.py fix
   ```
2. Check audio sink status:
   ```bash
   ./blueteeth.py status
   ```
3. Manually switch audio:
   ```bash
   ./blueteeth.py switch
   ```

### Connection drops frequently

1. Check for interference from other devices
2. Ensure device firmware is updated
3. Run diagnostics:
   ```bash
   ./blueteeth.py diagnose
   ```

### "Connection refused" errors

This usually means:
- Device is already connected to another host
- Device is not in connectable mode
- Need to delete and re-pair the device

### After system sleep/suspend

Bluetooth connections often break after suspend. Simply reconnect:
```bash
./blueteeth.py connect
```

### PipeWire not detecting device

1. Restart PipeWire services:
   ```bash
   systemctl --user restart pipewire pipewire-pulse
   ```
2. Use the fix command:
   ```bash
   ./blueteeth.py fix
   ```