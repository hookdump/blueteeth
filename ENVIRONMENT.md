# System Environment Configuration

## Audio Stack
- **PipeWire**: Active and running (systemd service)
- **WirePlumber**: Active session manager for PipeWire
- **PulseAudio**: Not available (pactl not installed, using PipeWire as replacement)
- **Audio Control**: Using `pw-cli` for PipeWire control

## Bluetooth Stack
- **Controller**: 00:E0:4C:23:99:87
- **Bluetooth Service**: Active (not blocked by rfkill)
- **BlueZ**: Running (bluetoothctl available)
- **Adapter Features**: 
  - A2DP Audio Source/Sink
  - Handsfree profiles
  - Central and peripheral roles

## Paired Devices
- **Sony WH-1000XM4** (14:3F:A6:27:0E:DD)
  - Status: Paired and bonded but not connected
  - Profiles: A2DP, Headset, Handsfree
  - Not trusted (may need to be set for auto-reconnect)

## Window Manager
- **Awesome WM** (non-GNOME environment)

## Key Findings
1. PipeWire is the main audio server (no PulseAudio)
2. WirePlumber manages PipeWire sessions
3. Bluetooth adapter is functional
4. Headphones are paired but need connection management
5. No desktop environment Bluetooth management (no GNOME/KDE)