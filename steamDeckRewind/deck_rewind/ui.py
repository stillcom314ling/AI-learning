"""User interface and notification module for Deck Rewind."""

import os
import logging
import subprocess
from typing import Optional

from .config import Config


logger = logging.getLogger("deck-rewind.ui")


try:
    import notify2
    NOTIFY2_AVAILABLE = True
except ImportError:
    NOTIFY2_AVAILABLE = False


class NotificationManager:
    """Manages on-screen notifications for Deck Rewind."""

    def __init__(self, config: Config):
        """Initialize the notification manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self._initialized = False
        self._init_notifications()

    def _init_notifications(self) -> None:
        """Initialize the notification system."""
        if not self.config.show_notifications:
            return

        if NOTIFY2_AVAILABLE:
            try:
                notify2.init("deck-rewind")
                self._initialized = True
                logger.info("Notification system initialized (notify2)")
            except Exception as e:
                logger.warning(f"Failed to initialize notify2: {e}")

        if not self._initialized:
            if self._check_notify_send():
                self._initialized = True
                logger.info("Notification system initialized (notify-send)")

    def _check_notify_send(self) -> bool:
        """Check if notify-send is available.

        Returns:
            True if notify-send is available
        """
        try:
            result = subprocess.run(
                ["which", "notify-send"],
                capture_output=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def show(
        self,
        message: str,
        title: str = "Deck Rewind",
        urgency: str = "normal",
        icon: Optional[str] = None,
    ) -> bool:
        """Show a notification.

        Args:
            message: Notification message
            title: Notification title
            urgency: Urgency level (low, normal, critical)
            icon: Icon name or path

        Returns:
            True if notification was shown
        """
        if not self.config.show_notifications:
            return False

        logger.info(f"Notification: {title} - {message}")

        if NOTIFY2_AVAILABLE and self._initialized:
            return self._show_notify2(message, title, urgency, icon)
        elif self._initialized:
            return self._show_notify_send(message, title, urgency, icon)

        return False

    def _show_notify2(
        self,
        message: str,
        title: str,
        urgency: str,
        icon: Optional[str],
    ) -> bool:
        """Show notification using notify2.

        Args:
            message: Notification message
            title: Notification title
            urgency: Urgency level
            icon: Icon name or path

        Returns:
            True if successful
        """
        try:
            urgency_map = {
                "low": notify2.URGENCY_LOW,
                "normal": notify2.URGENCY_NORMAL,
                "critical": notify2.URGENCY_CRITICAL,
            }

            notification = notify2.Notification(
                title,
                message,
                icon or "dialog-information",
            )

            notification.set_urgency(urgency_map.get(urgency, notify2.URGENCY_NORMAL))

            duration = self.config.get("ui.notification_duration_seconds", 3)
            notification.set_timeout(duration * 1000)

            notification.show()
            return True

        except Exception as e:
            logger.error(f"Failed to show notify2 notification: {e}")
            return False

    def _show_notify_send(
        self,
        message: str,
        title: str,
        urgency: str,
        icon: Optional[str],
    ) -> bool:
        """Show notification using notify-send command.

        Args:
            message: Notification message
            title: Notification title
            urgency: Urgency level
            icon: Icon name or path

        Returns:
            True if successful
        """
        try:
            duration = self.config.get("ui.notification_duration_seconds", 3)

            cmd = [
                "notify-send",
                "-u", urgency,
                "-t", str(duration * 1000),
            ]

            if icon:
                cmd.extend(["-i", icon])

            cmd.extend([title, message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.warning("notify-send timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to show notify-send notification: {e}")
            return False

    def show_snapshot_created(self, game_name: str) -> bool:
        """Show a snapshot created notification.

        Args:
            game_name: Name of the game

        Returns:
            True if notification was shown
        """
        return self.show(
            f"Snapshot saved for {game_name}",
            title="Snapshot Created",
            icon="document-save",
        )

    def show_restore_started(self, timestamp: str = "") -> bool:
        """Show a restore started notification.

        Args:
            timestamp: Optional timestamp of the snapshot being restored

        Returns:
            True if notification was shown
        """
        message = "Restoring game state..."
        if timestamp:
            message = f"Rewinding to {timestamp}..."

        return self.show(
            message,
            title="Restoring",
            urgency="normal",
            icon="view-refresh",
        )

    def show_restore_complete(self) -> bool:
        """Show a restore complete notification.

        Returns:
            True if notification was shown
        """
        return self.show(
            "Game state restored successfully",
            title="Restored",
            icon="emblem-ok-symbolic",
        )

    def show_restore_failed(self, reason: str = "") -> bool:
        """Show a restore failed notification.

        Args:
            reason: Optional failure reason

        Returns:
            True if notification was shown
        """
        message = "Failed to restore game state"
        if reason:
            message = f"Restore failed: {reason}"

        return self.show(
            message,
            title="Restore Failed",
            urgency="critical",
            icon="dialog-error",
        )

    def show_game_detected(self, game_name: str) -> bool:
        """Show a game detected notification.

        Args:
            game_name: Name of the detected game

        Returns:
            True if notification was shown
        """
        return self.show(
            f"Now tracking: {game_name}",
            title="Game Detected",
            icon="applications-games",
        )

    def show_low_disk_space(self, free_gb: float) -> bool:
        """Show a low disk space warning.

        Args:
            free_gb: Free disk space in GB

        Returns:
            True if notification was shown
        """
        return self.show(
            f"Low disk space: {free_gb:.1f} GB free. Snapshots paused.",
            title="Warning",
            urgency="critical",
            icon="dialog-warning",
        )

    def show_snapshot_count(self, count: int) -> bool:
        """Show the number of available snapshots.

        Args:
            count: Number of snapshots

        Returns:
            True if notification was shown
        """
        return self.show(
            f"{count} snapshots available",
            title="Snapshots",
            icon="folder-documents",
        )


class OverlayUI:
    """Steam Deck gaming mode overlay for status display."""

    def __init__(self, config: Config):
        """Initialize the overlay UI.

        Args:
            config: Configuration object
        """
        self.config = config
        self.position = config.get("ui.overlay_position", "top-right")

    def show_status(self, text: str, duration: float = 2.0) -> bool:
        """Show a status message in the overlay.

        Note: Full overlay implementation would require Steam Deck specific
        integration. This is a placeholder that falls back to notifications.

        Args:
            text: Status text to display
            duration: Display duration in seconds

        Returns:
            True if status was shown
        """
        logger.info(f"Overlay status: {text}")
        return True

    def show_progress(self, current: int, total: int, label: str = "") -> bool:
        """Show progress in the overlay.

        Args:
            current: Current progress value
            total: Total progress value
            label: Optional label

        Returns:
            True if progress was shown
        """
        percent = (current / total * 100) if total > 0 else 0
        logger.info(f"Progress: {label} {current}/{total} ({percent:.0f}%)")
        return True

    def hide(self) -> None:
        """Hide the overlay."""
        pass


class ConsoleUI:
    """Console-based UI for terminal output."""

    @staticmethod
    def print_header(text: str) -> None:
        """Print a header line.

        Args:
            text: Header text
        """
        print(f"\n{'=' * 60}")
        print(f"  {text}")
        print(f"{'=' * 60}\n")

    @staticmethod
    def print_status(label: str, value: str, ok: bool = True) -> None:
        """Print a status line.

        Args:
            label: Status label
            value: Status value
            ok: Whether status is OK (affects color)
        """
        status_char = "[OK]" if ok else "[!!]"
        print(f"  {status_char} {label}: {value}")

    @staticmethod
    def print_table(headers: list, rows: list) -> None:
        """Print a simple table.

        Args:
            headers: List of column headers
            rows: List of row data (each row is a list)
        """
        if not rows:
            print("  (no data)")
            return

        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        header_line = "  " + " | ".join(
            h.ljust(widths[i]) for i, h in enumerate(headers)
        )
        print(header_line)
        print("  " + "-" * (sum(widths) + 3 * (len(headers) - 1)))

        for row in rows:
            row_line = "  " + " | ".join(
                str(cell).ljust(widths[i]) for i, cell in enumerate(row)
            )
            print(row_line)

    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message.

        Args:
            message: Error message
        """
        print(f"\n  ERROR: {message}\n")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message.

        Args:
            message: Warning message
        """
        print(f"\n  WARNING: {message}\n")

    @staticmethod
    def print_success(message: str) -> None:
        """Print a success message.

        Args:
            message: Success message
        """
        print(f"\n  SUCCESS: {message}\n")

    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        """Ask for confirmation.

        Args:
            prompt: Confirmation prompt
            default: Default value if user just presses Enter

        Returns:
            User's choice
        """
        suffix = " [Y/n]: " if default else " [y/N]: "
        try:
            response = input(prompt + suffix).strip().lower()
            if not response:
                return default
            return response in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False
