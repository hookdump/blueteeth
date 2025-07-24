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
    
    def run_bluetoothctl(self, *commands) -> Tuple[int, str, str]:
        """Run bluetoothctl command(s)"""
        cmd_input = '\n'.join(commands) + '\n'
        process = subprocess.Popen(
            ['bluetoothctl'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=cmd_input)
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
    
    def connect_device(self, mac: str) -> bool:
        """Connect to a Bluetooth device"""
        # First trust the device
        self.run_bluetoothctl(f'trust {mac}')
        
        # Add to trusted devices in config
        if mac not in self.config['trusted_devices']:
            self.config['trusted_devices'].append(mac)
            self.save_config()
        
        # Connect
        returncode, stdout, stderr = self.run_bluetoothctl(f'connect {mac}')
        success = 'Connection successful' in stdout
        
        if success:
            # Update last device
            self.config['last_device'] = mac
            self.save_config()
            
            # Wait a bit for audio profile to settle
            time.sleep(2)
            
            # Try to set A2DP profile
            self.set_audio_profile(mac)
        
        return success
    
    def disconnect_device(self, mac: str) -> bool:
        """Disconnect from a Bluetooth device"""
        returncode, stdout, stderr = self.run_bluetoothctl(f'disconnect {mac}')
        return 'Successful disconnected' in stdout
    
    def set_audio_profile(self, mac: str):
        """Attempt to set A2DP audio profile"""
        # This is device-specific and may need adjustment
        # For now, we'll rely on PipeWire to handle it
        pass


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
                elif in_sinks and line:
                    # Parse sink line
                    parts = line.split()
                    if len(parts) >= 2:
                        sink_id = parts[0].strip('*.')
                        sink_name = ' '.join(parts[1:])
                        sinks.append({
                            'id': sink_id,
                            'name': sink_name,
                            'default': line.startswith('*')
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
        if self.bt.connect_device(target_device['mac']):
            click.echo("✓ Connected successfully")
            
            # Wait for PipeWire to detect the device
            time.sleep(2)
            
            # Try to switch audio output
            bt_sink = self.pw.find_bluetooth_sink()
            if bt_sink:
                if self.pw.set_default_sink(bt_sink['id']):
                    click.echo(f"✓ Audio output switched to {bt_sink['name']}")
                else:
                    click.echo("⚠ Failed to switch audio output automatically")
            else:
                click.echo("⚠ Bluetooth audio sink not found in PipeWire")
            
            return True
        else:
            click.echo("✗ Connection failed")
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
        click.echo("Attempting to fix audio connection...")
        
        # First disconnect if connected
        info = self.get_connected_device()
        if info:
            self.disconnect()
            time.sleep(2)
        
        # Reconnect
        if self.connect():
            click.echo("✓ Fix completed")
            return True
        else:
            click.echo("✗ Fix failed")
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


if __name__ == '__main__':
    cli()