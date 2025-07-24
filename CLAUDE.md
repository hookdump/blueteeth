You are tasked with building a robust, consistent, and user-friendly tool named blueteeth to manage Bluetooth audio devices — especially headphones — on Linux systems using PipeWire, outside of full desktop environments like GNOME. The system currently uses Awesome WM as the window manager, and the user is tired of unreliable audio experiences, including:

Needing to repair headphones after reboot

Manual fiddling with PulseAudio/PipeWire settings

Inconsistencies between sessions

Your mission:

🛠 PROJECT GOAL
Build a CLI (optional GUI later) application called blueteeth that:

Provides a consistent and reliable way to connect and switch to Bluetooth headphones.

Uses PipeWire, WirePlumber, or related tools.

Works in non-GNOME environments, specifically Awesome WM.

Does not need auto-detection — manual connect/disconnect is fine.

Must survive reboots, or help recover from them gracefully.

Push all code to GitHub under hookdump/blueteeth using the gh CLI.

✅ EXPECTATIONS
Easy to use: One-liner or button to "connect and use my headphones."

Reliable: No need to repair/re-pair constantly.

Minimal UI: CLI or GTK/dialog-based GUI if needed.

Persistent: It should remember the trusted devices or make reconnection easy.

📁 ORGANIZATION & TRACKING
Use Git for all work. Initial commit should include a basic README and plan.

Push all progress to GitHub: hookdump/blueteeth

Create the following documentation files:

PLAN.md: High-level plan with tasks, timeline, tools/libraries explored

EXPERIMENTS.md: Tests with PipeWire, bluetoothctl, pactl, etc.

AGENTS.md: If you spawn sub-agents, list their role and progress here

KNOWN_ISSUES.md: Problems with reconnection, bugs, glitches

🧠 RESEARCH & SETUP (DO FIRST)
Investigate existing tools: blueman, bluetoothctl, btmgmt, bluetuith, bluez, D-Bus interfaces, PipeWire APIs.

Determine which components are active (e.g. BlueZ vs PipeWire for Bluetooth).

Run diagnostic commands to check what system is using:

systemctl --user status wireplumber

pactl info

bluetoothctl show

rfkill list

Document the system config in ENVIRONMENT.md.

🔧 IMPLEMENTATION PHASES
Phase 1: MVP CLI
Command: blueteeth connect

Pairs, connects, sets profile to A2DP, switches output to the headphones

Command: blueteeth status

Shows whether connected, profile in use, current sink

Command: blueteeth fix

Attempts to reconnect and reset profile if audio is broken

Phase 2: GUI / Tray
Optional: Minimal GUI using zenity, yad, gtk-rs, or tauri.

Could expose connect/disconnect buttons.

🧬 TECH STACK
Language: Rust / Python / Shell (AI may choose)

Tools/APIs: D-Bus, bluetoothctl, pactl, PipeWire, BlueZ, wireplumber-cli

Store paired device info in config file (~/.config/blueteeth/config.json)

🔁 ALLOWED ACTIONS
Use gh CLI to push commits to hookdump/blueteeth

Spawn sub-agents as needed (e.g. pipewire-agent, dbus-agent, cli-agent)

Update .md files to track work and sub-agent responsibilities

Prompt the user if sudo or Bluetooth re-pairing is needed

Run diagnostics to detect broken configs or restart services

🧭 GUIDING PRINCIPLES
Prioritize robustness and clarity

Design as if for a power user who still wants plug-and-play reliability

Avoid overengineering: CLI first, GUI optional

If unsure, Google or check Arch Wiki

Now begin by creating the repo, analyzing the current system state, and writing PLAN.md. You may proceed.
