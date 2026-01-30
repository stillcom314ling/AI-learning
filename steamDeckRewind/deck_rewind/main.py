#!/usr/bin/env python3
"""Main entry point for Deck Rewind CLI."""

import argparse
import sys
import signal
import os
from pathlib import Path

from .config import Config
from .daemon import DeckRewindDaemon
from .snapshot import SnapshotManager
from .game_monitor import GameMonitor


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="deck-rewind",
        description="Save-state functionality for Steam Deck games",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the daemon")
    start_parser.add_argument(
        "--foreground", "-f", action="store_true", help="Run in foreground"
    )

    # Stop command
    subparsers.add_parser("stop", help="Stop the daemon")

    # Status command
    subparsers.add_parser("status", help="Check daemon status")

    # List command
    list_parser = subparsers.add_parser("list", help="List snapshots for active game")
    list_parser.add_argument(
        "--game-id", "-g", help="Specific game ID to list snapshots for"
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a specific snapshot")
    restore_parser.add_argument("snapshot_id", help="Snapshot ID to restore")

    # Config command
    config_parser = subparsers.add_parser("config", help="Configure settings")
    config_parser.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set a configuration value"
    )
    config_parser.add_argument("--get", metavar="KEY", help="Get a configuration value")
    config_parser.add_argument(
        "--list", action="store_true", help="List all configuration"
    )

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View daemon logs")
    logs_parser.add_argument(
        "--follow", "-f", action="store_true", help="Follow log output"
    )
    logs_parser.add_argument(
        "--lines", "-n", type=int, default=50, help="Number of lines to show"
    )

    # Uninstall command
    subparsers.add_parser("uninstall", help="Uninstall Deck Rewind")

    # Version command
    subparsers.add_parser("version", help="Show version")

    return parser


def get_pid_file() -> Path:
    """Get the path to the PID file."""
    return Path("~/.local/share/deck-rewind/daemon.pid").expanduser()


def get_log_file() -> Path:
    """Get the path to the log file."""
    return Path("~/.local/share/deck-rewind/daemon.log").expanduser()


def is_daemon_running() -> bool:
    """Check if the daemon is currently running."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        pid_file.unlink(missing_ok=True)
        return False


def start_daemon(foreground: bool = False) -> int:
    """Start the daemon."""
    if is_daemon_running():
        print("Daemon is already running")
        return 1

    config = Config()
    daemon = DeckRewindDaemon(config)

    if foreground:
        print("Starting Deck Rewind daemon in foreground...")
        daemon.run()
    else:
        print("Starting Deck Rewind daemon...")
        daemon.daemonize()
        print("Daemon started successfully")

    return 0


def stop_daemon() -> int:
    """Stop the daemon."""
    pid_file = get_pid_file()

    if not is_daemon_running():
        print("Daemon is not running")
        return 1

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        print(f"Stopping daemon (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)

        import time
        for _ in range(10):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break

        pid_file.unlink(missing_ok=True)
        print("Daemon stopped successfully")
        return 0
    except Exception as e:
        print(f"Error stopping daemon: {e}")
        return 1


def show_status() -> int:
    """Show daemon status."""
    if is_daemon_running():
        pid_file = get_pid_file()
        with open(pid_file, "r") as f:
            pid = f.read().strip()
        print(f"Deck Rewind daemon is running (PID: {pid})")

        config = Config()
        game_monitor = GameMonitor(config)
        active_game = game_monitor.get_active_game()

        if active_game:
            print(f"Active game: {active_game.get('name', 'Unknown')} (ID: {active_game.get('id', 'Unknown')})")
            print(f"Game PID: {active_game.get('pid', 'Unknown')}")
        else:
            print("No active game detected")

        snapshot_manager = SnapshotManager(config)
        if active_game:
            snapshots = snapshot_manager.list_snapshots(active_game.get("id"))
            print(f"Available snapshots: {len(snapshots)}")
    else:
        print("Deck Rewind daemon is not running")

    return 0


def list_snapshots(game_id: str = None) -> int:
    """List snapshots for a game."""
    config = Config()
    snapshot_manager = SnapshotManager(config)

    if not game_id:
        game_monitor = GameMonitor(config)
        active_game = game_monitor.get_active_game()
        if active_game:
            game_id = active_game.get("id")
        else:
            print("No active game. Use --game-id to specify a game.")
            return 1

    snapshots = snapshot_manager.list_snapshots(game_id)

    if not snapshots:
        print(f"No snapshots found for game {game_id}")
        return 0

    print(f"Snapshots for game {game_id}:")
    print("-" * 60)
    for i, snapshot in enumerate(snapshots):
        named = " [NAMED]" if snapshot.get("named") else ""
        method = snapshot.get("method", "unknown")
        timestamp = snapshot.get("timestamp", "Unknown")
        size = snapshot.get("size_mb", 0)
        print(f"  {i + 1}. {snapshot['id']}{named}")
        print(f"     Time: {timestamp} | Method: {method} | Size: {size:.1f} MB")

    return 0


def restore_snapshot(snapshot_id: str) -> int:
    """Restore a specific snapshot."""
    config = Config()
    snapshot_manager = SnapshotManager(config)

    print(f"Restoring snapshot {snapshot_id}...")
    success = snapshot_manager.restore(snapshot_id)

    if success:
        print("Snapshot restored successfully")
        return 0
    else:
        print("Failed to restore snapshot")
        return 1


def handle_config(args) -> int:
    """Handle configuration commands."""
    config = Config()

    if args.set:
        key, value = args.set
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        config.set(key, value)
        print(f"Set {key} = {value}")
    elif args.get:
        value = config.get(args.get)
        if value is not None:
            print(f"{args.get} = {value}")
        else:
            print(f"Configuration key '{args.get}' not found")
            return 1
    elif args.list:
        import yaml
        print(yaml.dump(config.config, default_flow_style=False))

    return 0


def show_logs(follow: bool = False, lines: int = 50) -> int:
    """Show daemon logs."""
    log_file = get_log_file()

    if not log_file.exists():
        print("No log file found")
        return 1

    if follow:
        import subprocess
        subprocess.run(["tail", "-f", "-n", str(lines), str(log_file)])
    else:
        with open(log_file, "r") as f:
            log_lines = f.readlines()
            for line in log_lines[-lines:]:
                print(line.rstrip())

    return 0


def uninstall() -> int:
    """Uninstall Deck Rewind."""
    print("Uninstalling Deck Rewind...")

    stop_daemon()

    import subprocess

    subprocess.run(
        ["systemctl", "--user", "stop", "deck-rewind.service"],
        capture_output=True,
    )
    subprocess.run(
        ["systemctl", "--user", "disable", "deck-rewind.service"],
        capture_output=True,
    )

    paths_to_remove = [
        Path("~/.config/deck-rewind").expanduser(),
        Path("~/.local/share/deck-rewind").expanduser(),
        Path("~/.config/systemd/user/deck-rewind.service").expanduser(),
    ]

    for path in paths_to_remove:
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed: {path}")

    print("\nUninstall complete!")
    print("Note: Run 'pip uninstall deck-rewind' to remove the Python package")

    return 0


def show_version() -> int:
    """Show version information."""
    from . import __version__
    print(f"Deck Rewind v{__version__}")
    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "start": lambda: start_daemon(args.foreground),
        "stop": stop_daemon,
        "status": show_status,
        "list": lambda: list_snapshots(getattr(args, "game_id", None)),
        "restore": lambda: restore_snapshot(args.snapshot_id),
        "config": lambda: handle_config(args),
        "logs": lambda: show_logs(args.follow, args.lines),
        "uninstall": uninstall,
        "version": show_version,
    }

    handler = commands.get(args.command)
    if handler:
        return handler()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
