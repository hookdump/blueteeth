# Blueteeth Development Plan

## Project Overview
A robust CLI tool for managing Bluetooth audio devices on Linux with PipeWire, designed for non-desktop environments like Awesome WM.

## Technical Architecture

### Core Components
1. **Bluetooth Control**: Using bluetoothctl via subprocess/D-Bus
2. **Audio Routing**: PipeWire control via pw-cli/D-Bus
3. **Configuration**: JSON-based persistent device storage
4. **CLI Interface**: Command-line tool with subcommands

### Technology Stack
- **Language**: Python 3 (chosen for rapid development and good D-Bus support)
- **Dependencies**:
  - `python-dbus` or `pydbus` for D-Bus communication
  - `click` for CLI interface
  - Standard library for JSON config and subprocess

## Implementation Phases

### Phase 1: MVP CLI (Week 1)
1. **Core functionality**
   - `blueteeth connect [device]` - Connect to headphones
   - `blueteeth disconnect` - Disconnect current device
   - `blueteeth status` - Show connection status
   - `blueteeth list` - List paired devices
   - `blueteeth fix` - Reconnect and reset audio

2. **Features**
   - Auto-trust devices on first connect
   - Set A2DP profile automatically
   - Switch PipeWire output to Bluetooth
   - Store last connected device

3. **Config Management**
   - Store in `~/.config/blueteeth/config.json`
   - Track paired devices and preferences
   - Remember last connected device

### Phase 2: Enhanced Reliability (Week 2)
1. **Connection Management**
   - Retry logic for failed connections
   - Profile switching fallbacks
   - Service restart capabilities
   
2. **Audio Routing**
   - Ensure proper sink switching
   - Handle multiple audio streams
   - Volume preservation

### Phase 3: GUI/Tray (Optional - Week 3)
1. **Simple GUI**
   - System tray icon
   - Quick connect/disconnect
   - Status indicators

## File Structure
```
blueteeth/
├── README.md
├── PLAN.md (this file)
├── ENVIRONMENT.md
├── EXPERIMENTS.md
├── AGENTS.md
├── KNOWN_ISSUES.md
├── blueteeth.py (main CLI)
├── requirements.txt
└── config/
    └── example-config.json
```

## Development Tasks
1. Set up Python project structure
2. Implement bluetoothctl wrapper
3. Implement PipeWire control
4. Create CLI interface
5. Add config management
6. Test with WH-1000XM4
7. Package and document

## Success Criteria
- One-command connection to headphones
- Survives reboots (easy reconnect)
- No manual profile switching needed
- Works reliably in Awesome WM
- Clear error messages

## Timeline
- Week 1: MVP CLI implementation
- Week 2: Testing and reliability improvements
- Week 3: Optional GUI and polish