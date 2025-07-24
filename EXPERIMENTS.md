# Bluetooth and PipeWire Experiments

## Bluetooth Control Methods

### bluetoothctl
Primary method for Bluetooth device management.

Commands tested:
- `bluetoothctl devices` - Lists paired devices
- `bluetoothctl info <MAC>` - Shows device details
- `bluetoothctl connect <MAC>` - Connects to device
- `bluetoothctl disconnect <MAC>` - Disconnects device
- `bluetoothctl trust <MAC>` - Trusts device for auto-reconnect

### D-Bus Interface
Alternative programmatic access:
- Service: `org.bluez`
- Interface: `org.bluez.Device1`
- Methods: Connect(), Disconnect(), etc.

## PipeWire Control Methods

### pw-cli
PipeWire's native CLI tool.

Commands to explore:
- `pw-cli ls Node` - List all nodes
- `pw-cli set-default <node>` - Set default sink
- `pw-cli info <id>` - Get node info

### WirePlumber
Session manager for PipeWire.
- `wpctl status` - Show devices and streams
- `wpctl set-default <id>` - Set default sink

## Audio Profile Management

### A2DP vs HFP/HSP
- A2DP: High quality audio playback (what we want)
- HFP/HSP: Lower quality with microphone support

Profile switching approaches:
1. Via bluetoothctl after connection
2. Via PipeWire node properties
3. Via WirePlumber policies

## Connection Workflow
1. Check if device is paired
2. Trust device if not trusted
3. Connect via bluetoothctl
4. Wait for PipeWire to detect
5. Switch to A2DP profile
6. Set as default audio sink

## Known Challenges
- Profile auto-selection varies by device
- PipeWire node appearance can be delayed
- Some devices need power-on before connect
- Trust settings may not persist properly