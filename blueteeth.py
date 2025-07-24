#!/usr/bin/env python3
"""
blueteeth - Bluetooth audio device manager for Linux
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import re

import click


class BluetoothManager:
    """Manages Bluetooth device connections via bluetoothctl"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "blueteeth"
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "last_device": None,
            "trusted_devices": [],
            "default_profile": "a2dp_sink"
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def run_bluetoothctl(self, *commands, timeout=10) -> Tuple[int, str, str]:
        """Run bluetoothctl command(s)"""
        cmd_input = '\n'.join(commands) + '\nquit\n'
        process = subprocess.Popen(
            ['bluetoothctl'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = process.communicate(input=cmd_input, timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    
    def get_devices(self) -> List[Dict[str, str]]:
        """Get list of paired devices"""
        _, stdout, _ = self.run_bluetoothctl('devices')
        devices = []
        for line in stdout.splitlines():
            if line.startswith('Device'):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    devices.append({
                        'mac': parts[1],
                        'name': parts[2]
                    })
        return devices
    
    def get_device_info(self, mac: str) -> Dict[str, str]:
        """Get detailed info about a device"""
        _, stdout, _ = self.run_bluetoothctl(f'info {mac}')
        info = {'mac': mac}
        for line in stdout.splitlines():
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info
    
    def connect_device(self, mac: str) -> Tuple[bool, str]:
        """Connect to a Bluetooth device. Returns (success, message)"""
        # First trust the device
        self.run_bluetoothctl(f'trust {mac}')
        
        # Add to trusted devices in config
        if mac not in self.config['trusted_devices']:
            self.config['trusted_devices'].append(mac)
            self.save_config()
        
        # Connect (give it more time to complete)
        returncode, stdout, stderr = self.run_bluetoothctl(f'connect {mac}', timeout=20)
        
        # Check for connection refused first
        if 'br-connection-refused' in stdout or 'br-connection-refused' in stderr:
            return False, "Connection refused - ensure device is powered on, in pairing mode, and not connected to another device"
        
        # Check if we got a "Connected: yes" message followed by failure
        connected_yes = False
        connection_failed = False
        
        for line in stdout.splitlines():
            if 'Connected: yes' in line:
                connected_yes = True
            if 'Failed to connect' in line:
                connection_failed = True
        
        # If we saw Connected: yes but then failed, it's a specific issue
        if connected_yes and connection_failed:
            # Double-check current connection status
            time.sleep(1)
            info = self.get_device_info(mac)
            if info.get('Connected') == 'yes':
                # Actually connected despite the error
                self.config['last_device'] = mac
                self.save_config()
                time.sleep(2)
                self.set_audio_profile(mac)
                return True, "Connected successfully"
            else:
                return False, "Connection was established but immediately lost - device may have rejected the connection"
        
        # Check other success patterns
        if 'Connection successful' in stdout and not connection_failed:
            # Update last device
            self.config['last_device'] = mac
            self.save_config()
            
            # Wait a bit for audio profile to settle
            time.sleep(2)
            
            # Try to set A2DP profile
            self.set_audio_profile(mac)
            
            return True, "Connected successfully"
        elif 'Failed to connect' in stdout:
            # Extract more specific error if available
            error_msg = "Connection failed"
            if 'org.bluez.Error' in stdout:
                # Try to extract the specific bluez error
                for line in stdout.splitlines():
                    if 'org.bluez.Error' in line:
                        error_msg = line.strip()
                        break
            return False, error_msg
        else:
            # Sometimes bluetoothctl doesn't give clear success/failure
            # Check if device is actually connected
            time.sleep(1)
            info = self.get_device_info(mac)
            if info.get('Connected') == 'yes':
                self.config['last_device'] = mac
                self.save_config()
                time.sleep(2)
                self.set_audio_profile(mac)
                return True, "Connected successfully"
            else:
                return False, "Connection failed - no response from device"
    
    def disconnect_device(self, mac: str) -> bool:
        """Disconnect from a Bluetooth device"""
        returncode, stdout, stderr = self.run_bluetoothctl(f'disconnect {mac}')
        return 'Successful disconnected' in stdout or 'Disconnected' in stdout
    
    def remove_device(self, mac: str) -> bool:
        """Remove a paired device"""
        returncode, stdout, stderr = self.run_bluetoothctl(f'remove {mac}')
        return 'Device has been removed' in stdout or returncode == 0
    
    def scan_devices(self, duration: int = 10) -> List[Dict[str, str]]:
        """Scan for Bluetooth devices for specified duration"""
        # Start scanning
        self.run_bluetoothctl('scan on')
        
        # Wait for devices to appear
        time.sleep(duration)
        
        # Get all devices (including newly discovered)
        _, stdout, _ = self.run_bluetoothctl('devices')
        
        # Stop scanning
        self.run_bluetoothctl('scan off')
        
        devices = []
        for line in stdout.splitlines():
            if line.startswith('Device'):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    devices.append({
                        'mac': parts[1],
                        'name': parts[2]
                    })
        return devices
    
    def pair_device(self, mac: str) -> Tuple[bool, str]:
        """Pair with a Bluetooth device"""
        returncode, stdout, stderr = self.run_bluetoothctl(f'pair {mac}', timeout=30)
        
        if 'Pairing successful' in stdout:
            return True, "Pairing successful"
        elif 'Already Paired' in stdout:
            return True, "Device already paired"
        elif 'Device not available' in stdout:
            return False, "Device not found - make sure it's in pairing mode and in range"
        elif 'Failed to pair' in stdout:
            # Extract specific error
            error_match = re.search(r'org\.bluez\.Error\.(\w+)', stdout)
            if error_match:
                error_type = error_match.group(1)
                if error_type == 'AuthenticationFailed':
                    return False, "Authentication failed - check PIN or try again"
                elif error_type == 'AuthenticationCanceled':
                    return False, "Pairing cancelled on device"
                else:
                    return False, f"Pairing failed: {error_type}"
            return False, "Pairing failed"
        else:
            return False, "Pairing failed - unknown error"
    
    def set_audio_profile(self, mac: str):
        """Attempt to set A2DP audio profile"""
        # This is device-specific and may need adjustment
        # For now, we'll rely on PipeWire to handle it
        pass
    
    def power_cycle_adapter(self):
        """Power cycle the Bluetooth adapter"""
        click.echo("Power cycling Bluetooth adapter...")
        self.run_bluetoothctl('power off')
        time.sleep(2)
        self.run_bluetoothctl('power on')
        time.sleep(1)


class PipeWireManager:
    """Manages PipeWire audio routing"""
    
    def get_sinks(self) -> List[Dict[str, str]]:
        """Get list of audio sinks"""
        try:
            result = subprocess.run(
                ['wpctl', 'status'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse wpctl output to find sinks
            sinks = []
            in_sinks = False
            for line in result.stdout.splitlines():
                line = line.strip()
                if 'Sinks:' in line:
                    in_sinks = True
                    continue
                elif 'Sources:' in line:
                    in_sinks = False
                elif in_sinks and line.strip():
                    # Parse sink line - format can include tree characters like "│  *   32. Samsung Monitor HDMI [vol: 0.75]"
                    # Strip tree characters and parse
                    clean_line = line.replace('│', '').replace('├', '').replace('└', '').strip()
                    if clean_line:
                        # Look for pattern like "* 32. Samsung Monitor HDMI [vol: 0.75]"
                        match = re.match(r'^(\*)?\s*(\d+)\.\s+(.+?)(?:\s+\[.*\])?$', clean_line)
                        if match:
                            is_default = bool(match.group(1))
                            sink_id = match.group(2)
                            sink_name = match.group(3).strip()
                            sinks.append({
                                'id': sink_id,
                                'name': sink_name,
                                'default': is_default
                            })
            return sinks
        except subprocess.CalledProcessError:
            return []
    
    def set_default_sink(self, sink_id: str) -> bool:
        """Set default audio sink"""
        try:
            subprocess.run(
                ['wpctl', 'set-default', sink_id],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def find_bluetooth_sink(self) -> Optional[Dict[str, str]]:
        """Find Bluetooth audio sink"""
        sinks = self.get_sinks()
        for sink in sinks:
            if 'bluetooth' in sink['name'].lower() or 'bluez' in sink['name'].lower():
                return sink
        return None


class Blueteeth:
    """Main application class"""
    
    def __init__(self):
        self.bt = BluetoothManager()
        self.pw = PipeWireManager()
    
    def connect(self, device_name: Optional[str] = None):
        """Connect to Bluetooth device"""
        devices = self.bt.get_devices()
        
        if not devices:
            click.echo("No paired devices found. Please pair your device first using bluetoothctl.")
            return False
        
        # Find target device
        target_device = None
        
        if device_name:
            # Search by name
            for device in devices:
                if device_name.lower() in device['name'].lower():
                    target_device = device
                    break
        else:
            # Use last device or first available
            if self.bt.config['last_device']:
                for device in devices:
                    if device['mac'] == self.bt.config['last_device']:
                        target_device = device
                        break
            
            if not target_device and devices:
                target_device = devices[0]
        
        if not target_device:
            click.echo(f"Device '{device_name}' not found.")
            return False
        
        # Connect
        click.echo(f"Connecting to {target_device['name']} ({target_device['mac']})...")
        success, message = self.bt.connect_device(target_device['mac'])
        
        if success:
            click.echo(f"✓ {message}")
            
            # Wait for PipeWire to detect the device, with retries
            click.echo("⏳ Waiting for audio device to appear...")
            bt_sink = None
            for attempt in range(5):  # Try for up to 10 seconds
                time.sleep(2)
                bt_sink = self.pw.find_bluetooth_sink()
                if bt_sink:
                    break
                    
            if bt_sink:
                if self.pw.set_default_sink(bt_sink['id']):
                    click.echo(f"✓ Audio output switched to {bt_sink['name']}")
                else:
                    click.echo("⚠ Failed to switch audio output automatically")
            else:
                click.echo("⚠ Bluetooth audio sink not found in PipeWire")
                click.echo("  Try running 'blueteeth fix' if audio is not working")
            
            return True
        else:
            click.echo(f"✗ {message}")
            return False
    
    def disconnect(self):
        """Disconnect current device"""
        info = self.get_connected_device()
        if info:
            mac = info['mac']
            name = info.get('Name', 'Unknown')
            click.echo(f"Disconnecting from {name}...")
            if self.bt.disconnect_device(mac):
                click.echo("✓ Disconnected successfully")
                return True
        else:
            click.echo("No device connected")
        return False
    
    def get_connected_device(self) -> Optional[Dict[str, str]]:
        """Get currently connected device"""
        devices = self.bt.get_devices()
        for device in devices:
            info = self.bt.get_device_info(device['mac'])
            if info.get('Connected') == 'yes':
                return info
        return None
    
    def status(self):
        """Show connection status"""
        info = self.get_connected_device()
        if info:
            click.echo(f"Connected to: {info.get('Name', 'Unknown')}")
            click.echo(f"MAC: {info['mac']}")
            click.echo(f"Trusted: {info.get('Trusted', 'no')}")
            
            # Show audio sink status
            bt_sink = self.pw.find_bluetooth_sink()
            if bt_sink:
                click.echo(f"Audio sink: {bt_sink['name']} (ID: {bt_sink['id']})")
                if bt_sink['default']:
                    click.echo("Audio output: ✓ Active")
                else:
                    click.echo("Audio output: ✗ Not default")
        else:
            click.echo("Status: Not connected")
            
            # Show last device
            if self.bt.config['last_device']:
                click.echo(f"Last device: {self.bt.config['last_device']}")
    
    def list_devices(self):
        """List paired devices"""
        devices = self.bt.get_devices()
        if devices:
            click.echo("Paired devices:")
            for device in devices:
                info = self.bt.get_device_info(device['mac'])
                connected = info.get('Connected') == 'yes'
                trusted = info.get('Trusted') == 'yes'
                status = []
                if connected:
                    status.append('connected')
                if trusted:
                    status.append('trusted')
                status_str = f" ({', '.join(status)})" if status else ""
                click.echo(f"  • {device['name']} - {device['mac']}{status_str}")
        else:
            click.echo("No paired devices found")
    
    def fix(self):
        """Try to fix audio issues"""
        return self.enhanced_fix()
    
    def diagnose(self):
        """Run diagnostics on Bluetooth and audio system"""
        click.echo("🔍 Running Bluetooth & Audio Diagnostics\n")
        
        # Check Bluetooth adapter
        click.echo("Bluetooth Adapter:")
        _, stdout, _ = self.bt.run_bluetoothctl('show')
        for line in stdout.splitlines():
            if any(key in line for key in ['Name:', 'Powered:', 'Discovering:', 'Pairable:']):
                click.echo(f"  {line.strip()}")
        
        # Check paired devices
        click.echo("\nPaired Devices:")
        devices = self.bt.get_devices()
        if devices:
            for device in devices:
                info = self.bt.get_device_info(device['mac'])
                connected = info.get('Connected') == 'yes'
                status = "connected" if connected else "disconnected"
                click.echo(f"  • {device['name']} ({device['mac']}) - {status}")
        else:
            click.echo("  No paired devices")
        
        # Check PipeWire status
        click.echo("\nAudio System:")
        try:
            result = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                click.echo("  ✓ PipeWire is running")
                # Check for Bluetooth sinks
                bt_sink = self.pw.find_bluetooth_sink()
                if bt_sink:
                    click.echo(f"  ✓ Bluetooth audio sink found: {bt_sink['name']}")
                else:
                    click.echo("  ✗ No Bluetooth audio sink found")
            else:
                click.echo("  ✗ PipeWire not responding")
        except FileNotFoundError:
            click.echo("  ✗ wpctl not found - is PipeWire installed?")
        
        # Check for common issues
        click.echo("\nCommon Issues Check:")
        if not devices:
            click.echo("  ⚠ No paired devices - run 'blueteeth pair' to add a device")
        
        connected_device = self.get_connected_device()
        if connected_device and not self.pw.find_bluetooth_sink():
            click.echo("  ⚠ Device connected but no audio sink - try 'blueteeth fix'")
    
    def pair_new_device(self, device_name: Optional[str] = None):
        """Interactive pairing process"""
        click.echo("🎧 Bluetooth Device Pairing\n")
        
        # Instructions
        click.echo("Please put your Bluetooth device in pairing mode:")
        click.echo("  • For most headphones: Hold power button for 5-7 seconds")
        click.echo("  • Look for blinking blue/red LED")
        click.echo("  • You may hear 'Bluetooth pairing' announcement\n")
        
        if not click.confirm("Is your device in pairing mode?"):
            click.echo("\nPairing cancelled. Please put device in pairing mode and try again.")
            return False
        
        click.echo("\n🔍 Scanning for devices...")
        
        # Scan for devices
        devices = self.bt.scan_devices(duration=10)
        
        # Filter by name if provided
        if device_name:
            devices = [d for d in devices if device_name.lower() in d['name'].lower()]
        
        # Remove already paired devices
        paired_macs = [d['mac'] for d in self.bt.get_devices()]
        new_devices = [d for d in devices if d['mac'] not in paired_macs]
        
        if not new_devices:
            click.echo("\n❌ No new devices found.")
            click.echo("\nTroubleshooting:")
            click.echo("  1. Make sure device is in pairing mode")
            click.echo("  2. Move device closer to computer")
            click.echo("  3. Turn device off and on, then try again")
            click.echo("  4. Check if device is already paired (run 'blueteeth list')")
            return False
        
        # Show found devices
        click.echo(f"\nFound {len(new_devices)} new device(s):\n")
        for i, device in enumerate(new_devices, 1):
            click.echo(f"  {i}. {device['name']} ({device['mac']})")
        
        # Select device
        if len(new_devices) == 1:
            selected = new_devices[0]
            if click.confirm(f"\nPair with {selected['name']}?"):
                target_device = selected
            else:
                click.echo("Pairing cancelled.")
                return False
        else:
            while True:
                choice = click.prompt("\nSelect device number (or 'c' to cancel)", type=str)
                if choice.lower() == 'c':
                    click.echo("Pairing cancelled.")
                    return False
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(new_devices):
                        target_device = new_devices[idx]
                        break
                    else:
                        click.echo("Invalid selection. Please try again.")
                except ValueError:
                    click.echo("Invalid selection. Please enter a number or 'c'.")
        
        # Pair device
        click.echo(f"\n📡 Pairing with {target_device['name']}...")
        success, message = self.bt.pair_device(target_device['mac'])
        
        if success:
            click.echo(f"✅ {message}")
            
            # Trust device
            self.bt.run_bluetoothctl(f"trust {target_device['mac']}")
            
            # Try to connect
            click.echo("\n🔌 Connecting...")
            success, message = self.bt.connect_device(target_device['mac'])
            
            if success:
                click.echo(f"✅ {message}")
                
                # Wait for audio sink
                click.echo("⏳ Waiting for audio device...")
                bt_sink = None
                for attempt in range(5):
                    time.sleep(2)
                    bt_sink = self.pw.find_bluetooth_sink()
                    if bt_sink:
                        break
                
                if bt_sink:
                    if self.pw.set_default_sink(bt_sink['id']):
                        click.echo(f"✅ Audio output switched to {bt_sink['name']}")
                        click.echo("\n🎉 Setup complete! Your device is ready to use.")
                    else:
                        click.echo("⚠️  Failed to switch audio automatically")
                        click.echo("   Run 'blueteeth status' to check audio setup")
                else:
                    click.echo("⚠️  Audio device not detected by PipeWire")
                    click.echo("   Try 'blueteeth fix' if audio isn't working")
                
                return True
            else:
                click.echo(f"⚠️  {message}")
                click.echo("   Device paired but not connected. Try 'blueteeth connect'")
                return True
        else:
            click.echo(f"❌ {message}")
            return False
    
    def remove_device_interactive(self, device_name: Optional[str] = None):
        """Remove a paired device with confirmation"""
        devices = self.bt.get_devices()
        
        if not devices:
            click.echo("No paired devices to remove.")
            return False
        
        # Find target device
        target_device = None
        
        if device_name:
            # Search by name
            for device in devices:
                if device_name.lower() in device['name'].lower():
                    target_device = device
                    break
            
            if not target_device:
                click.echo(f"Device '{device_name}' not found.")
                return False
        else:
            # Show device list
            click.echo("Paired devices:\n")
            for i, device in enumerate(devices, 1):
                info = self.bt.get_device_info(device['mac'])
                connected = info.get('Connected') == 'yes'
                status = " (connected)" if connected else ""
                click.echo(f"  {i}. {device['name']} ({device['mac']}){status}")
            
            # Select device
            while True:
                choice = click.prompt("\nSelect device number to remove (or 'c' to cancel)", type=str)
                if choice.lower() == 'c':
                    click.echo("Removal cancelled.")
                    return False
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(devices):
                        target_device = devices[idx]
                        break
                    else:
                        click.echo("Invalid selection. Please try again.")
                except ValueError:
                    click.echo("Invalid selection. Please enter a number or 'c'.")
        
        # Confirm removal
        info = self.bt.get_device_info(target_device['mac'])
        connected = info.get('Connected') == 'yes'
        
        if connected:
            click.echo(f"\n⚠️  {target_device['name']} is currently connected.")
        
        if not click.confirm(f"Remove {target_device['name']} ({target_device['mac']})?"):
            click.echo("Removal cancelled.")
            return False
        
        # Disconnect if connected
        if connected:
            click.echo("Disconnecting...")
            self.bt.disconnect_device(target_device['mac'])
            time.sleep(1)
        
        # Remove device
        click.echo("Removing device...")
        if self.bt.remove_device(target_device['mac']):
            click.echo(f"✅ {target_device['name']} has been removed.")
            
            # Clean up config
            if target_device['mac'] in self.bt.config['trusted_devices']:
                self.bt.config['trusted_devices'].remove(target_device['mac'])
            if self.bt.config['last_device'] == target_device['mac']:
                self.bt.config['last_device'] = None
            self.bt.save_config()
            
            return True
        else:
            click.echo("❌ Failed to remove device.")
            return False
    
    def enhanced_fix(self):
        """Enhanced fix with full troubleshooting"""
        click.echo("🔧 Bluetooth Audio Troubleshooter\n")
        
        # Check current state
        connected_device = self.get_connected_device()
        bt_sink = self.pw.find_bluetooth_sink()
        
        if connected_device and bt_sink:
            click.echo(f"✓ {connected_device.get('Name')} is connected")
            click.echo(f"✓ Audio sink detected: {bt_sink['name']}")
            
            if not bt_sink['default']:
                click.echo("⚠️  Audio sink not set as default")
                if click.confirm("Set as default audio output?"):
                    if self.pw.set_default_sink(bt_sink['id']):
                        click.echo("✅ Audio output switched successfully")
                        return True
            else:
                click.echo("✓ Audio is properly configured")
                
                if click.confirm("\nAudio still not working. Try reconnecting?"):
                    # Reconnect
                    mac = connected_device['mac']
                    name = connected_device.get('Name', 'device')
                    
                    click.echo(f"\nReconnecting {name}...")
                    self.bt.disconnect_device(mac)
                    time.sleep(2)
                    
                    success, message = self.bt.connect_device(mac)
                    if success:
                        click.echo(f"✅ {message}")
                        return True
                    else:
                        click.echo(f"❌ {message}")
                return True
        
        elif connected_device and not bt_sink:
            click.echo(f"⚠️  {connected_device.get('Name')} is connected but no audio sink found")
            
            if click.confirm("Try reconnecting?"):
                mac = connected_device['mac']
                self.disconnect()
                time.sleep(2)
                return self.connect()
            
        else:
            click.echo("❌ No Bluetooth device connected")
            
            # Check if we have paired devices
            devices = self.bt.get_devices()
            if devices:
                click.echo("\nPaired devices found. Try connecting?")
                return self.connect()
            else:
                click.echo("\nNo paired devices found.")
                if click.confirm("Pair a new device?"):
                    return self.pair_new_device()
        
        # Advanced troubleshooting
        if click.confirm("\nTry advanced troubleshooting?"):
            click.echo("\n1️⃣  Power cycling Bluetooth adapter...")
            self.bt.power_cycle_adapter()
            
            click.echo("2️⃣  Restarting PipeWire...")
            subprocess.run(['systemctl', '--user', 'restart', 'pipewire'], capture_output=True)
            subprocess.run(['systemctl', '--user', 'restart', 'pipewire-pulse'], capture_output=True)
            time.sleep(3)
            
            click.echo("3️⃣  Attempting connection...")
            if connected_device:
                return self.connect()
            else:
                click.echo("\nNo device to reconnect. Run 'blueteeth connect' when ready.")
        
        return False
    
    def switch_sink(self, sink_id: Optional[str] = None):
        """Switch audio output to a different sink"""
        sinks = self.pw.get_sinks()
        
        if not sinks:
            click.echo("No audio sinks found.")
            return False
        
        # Filter out Bluetooth sinks for non-Bluetooth options
        non_bt_sinks = [s for s in sinks if 'bluetooth' not in s['name'].lower() and 'bluez' not in s['name'].lower()]
        
        if not sink_id:
            # Show available sinks
            click.echo("Available audio outputs:\n")
            click.echo("Bluetooth sinks:")
            bt_sinks = [s for s in sinks if 'bluetooth' in s['name'].lower() or 'bluez' in s['name'].lower()]
            if bt_sinks:
                for sink in bt_sinks:
                    default_marker = " * (current)" if sink['default'] else ""
                    click.echo(f"  {sink['id']}. {sink['name']}{default_marker}")
            else:
                click.echo("  None")
            
            click.echo("\nOther audio outputs:")
            if non_bt_sinks:
                for sink in non_bt_sinks:
                    default_marker = " * (current)" if sink['default'] else ""
                    click.echo(f"  {sink['id']}. {sink['name']}{default_marker}")
            else:
                click.echo("  None")
            
            if not non_bt_sinks and not bt_sinks:
                return False
            
            # Prompt for selection
            while True:
                choice = click.prompt("\nSelect sink ID number (or 'c' to cancel)", type=str)
                if choice.lower() == 'c':
                    click.echo("Cancelled.")
                    return False
                
                # Check if valid sink ID
                for sink in sinks:
                    if sink['id'] == choice:
                        sink_id = choice
                        break
                
                if sink_id:
                    break
                else:
                    click.echo("Invalid sink ID. Please try again.")
        
        # Find the selected sink
        selected_sink = None
        for sink in sinks:
            if sink['id'] == sink_id:
                selected_sink = sink
                break
        
        if not selected_sink:
            click.echo(f"Sink ID {sink_id} not found.")
            return False
        
        # Switch to the selected sink
        click.echo(f"\nSwitching audio output to: {selected_sink['name']}")
        if self.pw.set_default_sink(sink_id):
            click.echo(f"✓ Audio output switched successfully")
            
            # Show tip if switching away from Bluetooth
            if any(kw in selected_sink['name'].lower() for kw in ['bluetooth', 'bluez']):
                click.echo("\nTip: To switch back to regular audio, run 'blueteeth switch' again")
            else:
                click.echo("\nTip: To reconnect Bluetooth audio, run 'blueteeth connect'")
            
            return True
        else:
            click.echo("✗ Failed to switch audio output")
            return False


@click.group()
def cli():
    """blueteeth - Bluetooth audio device manager"""
    pass


@cli.command()
@click.argument('device', required=False)
def connect(device):
    """Connect to Bluetooth device"""
    app = Blueteeth()
    sys.exit(0 if app.connect(device) else 1)


@cli.command()
def disconnect():
    """Disconnect current device"""
    app = Blueteeth()
    sys.exit(0 if app.disconnect() else 1)


@cli.command()
def status():
    """Show connection status"""
    app = Blueteeth()
    app.status()


@cli.command('list')
def list_devices():
    """List paired devices"""
    app = Blueteeth()
    app.list_devices()


@cli.command()
def fix():
    """Fix audio connection"""
    app = Blueteeth()
    sys.exit(0 if app.fix() else 1)


@cli.command()
def diagnose():
    """Diagnose Bluetooth and audio issues"""
    app = Blueteeth()
    app.diagnose()


@cli.command()
@click.argument('device', required=False)
def pair(device):
    """Pair a new Bluetooth device"""
    app = Blueteeth()
    sys.exit(0 if app.pair_new_device(device) else 1)


@cli.command()
@click.argument('device', required=False)
def remove(device):
    """Remove a paired device"""
    app = Blueteeth()
    sys.exit(0 if app.remove_device_interactive(device) else 1)


@cli.command()
@click.argument('sink_id', required=False)
def switch(sink_id):
    """Switch audio output to a different sink (away from Bluetooth)"""
    app = Blueteeth()
    sys.exit(0 if app.switch_sink(sink_id) else 1)


if __name__ == '__main__':
    cli()