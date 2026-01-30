"""Background daemon for Deck Rewind."""

import os
import sys
import time
import signal
import logging
import atexit
from pathlib import Path
from typing import Optional

from .config import Config
from .snapshot import SnapshotManager
from .game_monitor import GameMonitor
from .hotkey_listener import HotkeyListener
from .ui import NotificationManager


class DeckRewindDaemon:
    """Background daemon that monitors games and manages snapshots."""

    def __init__(self, config: Config):
        """Initialize the daemon.

        Args:
            config: Configuration object
        """
        self.config = config
        self.running = False
        self.pid_file = Path("~/.local/share/deck-rewind/daemon.pid").expanduser()
        self.log_file = Path("~/.local/share/deck-rewind/daemon.log").expanduser()

        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        self._setup_logging()

        self.snapshot_manager = SnapshotManager(config)
        self.game_monitor = GameMonitor(config)
        self.hotkey_listener = HotkeyListener(config)
        self.notification_manager = NotificationManager(config)

        self.current_game: Optional[dict] = None
        self.last_snapshot_time: float = 0
        self.snapshot_index: int = 0

    def _setup_logging(self) -> None:
        """Configure logging for the daemon."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("deck-rewind")

    def daemonize(self) -> None:
        """Daemonize the process using double-fork."""
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            self.logger.error(f"First fork failed: {e}")
            sys.exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            self.logger.error(f"Second fork failed: {e}")
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()

        with open("/dev/null", "r") as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        with open(self.log_file, "a+") as log:
            os.dup2(log.fileno(), sys.stdout.fileno())
            os.dup2(log.fileno(), sys.stderr.fileno())

        atexit.register(self._cleanup)

        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        self.run()

    def _cleanup(self) -> None:
        """Clean up PID file on exit."""
        self.pid_file.unlink(missing_ok=True)

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGHUP, self._reload_config)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _reload_config(self, signum: int, frame) -> None:
        """Reload configuration on SIGHUP."""
        self.logger.info("Reloading configuration...")
        self.config.load()

    def _setup_hotkey_handlers(self) -> None:
        """Set up hotkey handlers."""
        self.hotkey_listener.register_handler(
            self.config.get("hotkeys.rewind_previous"),
            self._on_rewind_previous,
        )
        self.hotkey_listener.register_handler(
            self.config.get("hotkeys.rewind_back"),
            self._on_rewind_back,
        )
        self.hotkey_listener.register_handler(
            self.config.get("hotkeys.rewind_forward"),
            self._on_rewind_forward,
        )
        self.hotkey_listener.register_handler(
            self.config.get("hotkeys.list_snapshots"),
            self._on_list_snapshots,
        )
        self.hotkey_listener.register_handler(
            self.config.get("hotkeys.manual_snapshot"),
            self._on_manual_snapshot,
        )

    def _on_rewind_previous(self) -> None:
        """Handle rewind to previous snapshot."""
        if not self.current_game:
            self.notification_manager.show("No active game")
            return

        snapshots = self.snapshot_manager.list_snapshots(self.current_game["id"])
        if not snapshots:
            self.notification_manager.show("No snapshots available")
            return

        self.notification_manager.show("Rewinding to previous snapshot...")
        latest = snapshots[0]
        success = self.snapshot_manager.restore(latest["id"])

        if success:
            self.notification_manager.show("Restored successfully")
        else:
            self.notification_manager.show("Restore failed")

    def _on_rewind_back(self) -> None:
        """Handle rewind one snapshot back."""
        if not self.current_game:
            return

        snapshots = self.snapshot_manager.list_snapshots(self.current_game["id"])
        if not snapshots:
            return

        self.snapshot_index = min(self.snapshot_index + 1, len(snapshots) - 1)
        snapshot = snapshots[self.snapshot_index]

        self.notification_manager.show(f"Rewinding to snapshot {self.snapshot_index + 1}...")
        success = self.snapshot_manager.restore(snapshot["id"])

        if success:
            self.notification_manager.show(f"Restored to snapshot {self.snapshot_index + 1}")

    def _on_rewind_forward(self) -> None:
        """Handle forward one snapshot."""
        if not self.current_game:
            return

        snapshots = self.snapshot_manager.list_snapshots(self.current_game["id"])
        if not snapshots:
            return

        self.snapshot_index = max(self.snapshot_index - 1, 0)
        snapshot = snapshots[self.snapshot_index]

        self.notification_manager.show(f"Restoring to snapshot {self.snapshot_index + 1}...")
        self.snapshot_manager.restore(snapshot["id"])

    def _on_list_snapshots(self) -> None:
        """Handle list snapshots request."""
        if not self.current_game:
            self.notification_manager.show("No active game")
            return

        snapshots = self.snapshot_manager.list_snapshots(self.current_game["id"])
        count = len(snapshots)
        self.notification_manager.show(f"{count} snapshots available")

    def _on_manual_snapshot(self) -> None:
        """Handle manual snapshot request."""
        if not self.current_game:
            self.notification_manager.show("No active game")
            return

        self.notification_manager.show("Creating snapshot...")
        success = self.snapshot_manager.create(
            self.current_game["pid"],
            self.current_game["id"],
            named=True,
        )

        if success:
            self.notification_manager.show("Snapshot saved")
        else:
            self.notification_manager.show("Snapshot failed")

    def _check_disk_space(self) -> bool:
        """Check if there's enough disk space for snapshots.

        Returns:
            True if there's enough space, False otherwise
        """
        storage_path = self.config.storage_path
        storage_path.mkdir(parents=True, exist_ok=True)

        stat = os.statvfs(storage_path)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

        if free_gb < 2:
            self.logger.warning(f"Low disk space: {free_gb:.1f} GB free")
            return False

        return True

    def _auto_snapshot(self) -> None:
        """Create automatic rolling snapshot if conditions are met."""
        if not self.current_game:
            return

        current_time = time.time()
        interval = self.config.snapshot_interval

        if current_time - self.last_snapshot_time < interval:
            return

        if not self._check_disk_space():
            return

        game_id = self.current_game["id"]
        if game_id in self.config.game_blacklist:
            return

        whitelist = self.config.game_whitelist
        if whitelist and game_id not in whitelist:
            return

        self.logger.info(f"Creating auto-snapshot for {self.current_game['name']}")
        success = self.snapshot_manager.create(
            self.current_game["pid"],
            game_id,
            named=False,
        )

        if success:
            self.last_snapshot_time = current_time
            self.snapshot_manager.cleanup_old_snapshots(
                game_id, self.config.max_snapshots
            )

    def run(self) -> None:
        """Main daemon loop."""
        self.logger.info("Deck Rewind daemon starting...")

        self._setup_signal_handlers()
        self._setup_hotkey_handlers()

        self.hotkey_listener.start()

        self.running = True
        self.logger.info("Daemon started successfully")

        try:
            while self.running:
                new_game = self.game_monitor.get_active_game()

                if new_game != self.current_game:
                    if new_game:
                        self.logger.info(
                            f"Game detected: {new_game.get('name', 'Unknown')} "
                            f"(PID: {new_game.get('pid')})"
                        )
                        self.notification_manager.show(
                            f"Tracking: {new_game.get('name', 'Unknown')}"
                        )
                    elif self.current_game:
                        self.logger.info(
                            f"Game ended: {self.current_game.get('name', 'Unknown')}"
                        )

                    self.current_game = new_game
                    self.last_snapshot_time = 0
                    self.snapshot_index = 0

                if self.current_game:
                    self._auto_snapshot()

                self.hotkey_listener.process_events()

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Daemon error: {e}", exc_info=True)
        finally:
            self.hotkey_listener.stop()
            self.logger.info("Daemon stopped")
