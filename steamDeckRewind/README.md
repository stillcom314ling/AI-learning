# Deck Rewind

Save-state functionality for Steam Deck games. Take memory snapshots of any game and rewind time with hotkeys.

## Features

- **Automatic Snapshots**: Background daemon takes periodic snapshots while you play
- **Hotkey Rewind**: Press Steam + L2 to rewind to the last snapshot
- **Rolling History**: Navigate through multiple snapshots with D-pad
- **Named Snapshots**: Create permanent save points that won't auto-delete
- **Smart Detection**: Automatically detects and tracks running games
- **Minimal Footprint**: Configurable storage limits with automatic cleanup

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/[USER]/deck-rewind/main/install.sh | bash
```

Or clone and install manually:

```bash
git clone https://github.com/[USER]/deck-rewind.git
cd deck-rewind
./install.sh
```

## Hotkeys

| Hotkey | Action |
|--------|--------|
| Steam + L2 | Rewind to previous snapshot |
| Steam + D-pad Left | Go back one snapshot |
| Steam + D-pad Right | Go forward one snapshot |
| Steam + D-pad Up | Show snapshot count |
| Steam + L1 | Create named snapshot |

## Commands

```bash
# Start the daemon (runs automatically after install)
deck-rewind start

# Stop the daemon
deck-rewind stop

# Check status and current game
deck-rewind status

# List available snapshots
deck-rewind list

# Restore a specific snapshot
deck-rewind restore <snapshot_id>

# Configure settings
deck-rewind config --set snapshots.interval_seconds 60
deck-rewind config --get snapshots.interval_seconds
deck-rewind config --list

# View daemon logs
deck-rewind logs
deck-rewind logs -f  # Follow mode

# Uninstall
deck-rewind uninstall
```

## Configuration

Configuration file: `~/.config/deck-rewind/config.yaml`

```yaml
snapshots:
  interval_seconds: 30        # How often to take snapshots
  max_rolling_snapshots: 10   # Max auto-snapshots per game
  storage_path: "~/.local/share/deck-rewind/snapshots"
  compression: "zstd"
  compression_level: 3

snapshot_method:
  prefer_criu: true           # Use CRIU if available
  fallback_to_memory_dump: true

storage:
  max_total_size_gb: 10       # Total storage limit
  auto_cleanup: true

hotkeys:
  rewind_previous: "steam+l2"
  rewind_back: "steam+dpad_left"
  rewind_forward: "steam+dpad_right"
  list_snapshots: "steam+dpad_up"
  manual_snapshot: "steam+l1"

ui:
  show_notifications: true
  notification_duration_seconds: 3
  overlay_position: "top-right"

games:
  blacklist: []               # Games to never snapshot
  whitelist: []               # If set, only snapshot these games
```

## How It Works

### Snapshot Methods

**CRIU (Checkpoint/Restore In Userspace)** - Primary method
- Full process checkpoint including memory, file descriptors, and state
- Best restore fidelity
- Requires `criu` package installed

**Memory Dump** - Fallback method
- Direct reading of process memory via `/proc/<pid>/mem`
- Works without special permissions
- Less complete than CRIU but still effective

### Storage

Snapshots are stored in `~/.local/share/deck-rewind/snapshots/`:
```
snapshots/
├── <game_id>/
│   ├── 20240101_120000/      # Auto snapshot
│   │   ├── metadata.json
│   │   ├── maps.txt
│   │   └── *.bin.zst         # Compressed memory regions
│   └── 20240101_130000/      # Named snapshot (preserved)
└── <another_game>/
```

## Tested Games

| Game | Status | Notes |
|------|--------|-------|
| Stardew Valley | ✅ Working | |
| Celeste | ✅ Working | |
| Hades | ✅ Working | |
| Vampire Survivors | ✅ Working | |
| Portal | ⚠️ Partial | Some graphical glitches on restore |
| Native Linux games | ✅ Working | Generally work well |
| Proton games | ⚠️ Varies | Success depends on game complexity |

## Troubleshooting

### Daemon won't start
```bash
# Check if already running
deck-rewind status

# View logs for errors
deck-rewind logs

# Try running in foreground for debugging
deck-rewind start --foreground
```

### Hotkeys not working
1. Make sure daemon is running: `deck-rewind status`
2. Check you're in the `input` group: `groups`
3. Log out and back in after install for permissions
4. Verify controller is detected: `ls /dev/input/event*`

### Snapshots not being created
1. Check disk space: `df -h`
2. Verify game is detected: `deck-rewind status`
3. Check if game is blacklisted in config
4. View logs: `deck-rewind logs`

### Restore fails
1. Game must still be running for memory dump restores
2. CRIU restores may fail on complex games
3. Check logs for specific error messages

### High disk usage
```bash
# Check current usage
du -sh ~/.local/share/deck-rewind/snapshots/

# Reduce snapshot frequency
deck-rewind config --set snapshots.interval_seconds 60

# Reduce max snapshots
deck-rewind config --set snapshots.max_rolling_snapshots 5

# Reduce total storage limit
deck-rewind config --set storage.max_total_size_gb 5
```

## System Requirements

- Steam Deck (SteamOS) or Linux
- Python 3.10+
- CRIU (optional, for better snapshots)
- 2GB+ free disk space

## Dependencies

**System packages:**
- criu
- python3
- python3-pip
- zstd
- libnotify

**Python packages:**
- pyyaml
- psutil
- evdev
- notify2
- zstandard

## Development

```bash
# Clone the repository
git clone https://github.com/[USER]/deck-rewind.git
cd deck-rewind

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_snapshot.py -v
```

## Architecture

```
deck_rewind/
├── main.py           # CLI entry point
├── daemon.py         # Background service
├── snapshot.py       # Snapshot creation (CRIU + memory dump)
├── restore.py        # Restore functionality
├── game_monitor.py   # Game process detection
├── hotkey_listener.py # Controller input handling
├── config.py         # Configuration management
└── ui.py             # Notifications and overlay
```

## Known Limitations

- **Online games**: Rewinding won't affect server state
- **Anti-cheat**: Some games with anti-cheat may detect/block memory operations
- **GPU state**: Graphics state isn't fully captured
- **Audio**: Sound state may desync after restore
- **File changes**: Game saves written to disk aren't reverted

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- CRIU project for checkpoint/restore technology
- Steam Deck community for testing and feedback
- Inspired by emulator save states
