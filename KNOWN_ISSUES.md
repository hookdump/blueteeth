# Known Issues

## Current Issues
None yet - project just started.

## Potential Issues to Watch
Based on research and system analysis:

1. **Profile Switching Delays**
   - Some devices take time to switch from HFP to A2DP
   - May need retry logic or delays

2. **Trust Persistence**
   - Device trust settings might not survive reboots
   - May need to re-trust on each connection

3. **PipeWire Node Detection**
   - Bluetooth audio nodes may appear with delay
   - Need to poll or wait for node availability

4. **Multiple Bluetooth Adapters**
   - System might have multiple adapters
   - Need to handle adapter selection

5. **Power Management**
   - Bluetooth might be powered off after suspend
   - Need to check and enable power state

## Workarounds
Will be documented as issues are encountered and resolved.