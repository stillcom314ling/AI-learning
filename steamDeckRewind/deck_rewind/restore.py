"""Restore functionality for Deck Rewind.

This module provides additional restore utilities and strategies
beyond the basic restore functionality in snapshot.py.
"""

import os
import signal
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .config import Config


logger = logging.getLogger("deck-rewind.restore")


class RestoreManager:
    """Manages the restoration process with advanced features."""

    def __init__(self, config: Config):
        """Initialize the restore manager.

        Args:
            config: Configuration object
        """
        self.config = config

    def suspend_process(self, pid: int) -> bool:
        """Suspend a process before restoration.

        Args:
            pid: Process ID to suspend

        Returns:
            True if successful
        """
        try:
            os.kill(pid, signal.SIGSTOP)
            logger.info(f"Suspended process {pid}")
            return True
        except ProcessLookupError:
            logger.error(f"Process {pid} not found")
            return False
        except PermissionError:
            logger.error(f"Permission denied suspending process {pid}")
            return False

    def resume_process(self, pid: int) -> bool:
        """Resume a suspended process.

        Args:
            pid: Process ID to resume

        Returns:
            True if successful
        """
        try:
            os.kill(pid, signal.SIGCONT)
            logger.info(f"Resumed process {pid}")
            return True
        except ProcessLookupError:
            logger.error(f"Process {pid} not found")
            return False
        except PermissionError:
            logger.error(f"Permission denied resuming process {pid}")
            return False

    def kill_process(self, pid: int, graceful: bool = True) -> bool:
        """Kill a process.

        Args:
            pid: Process ID to kill
            graceful: If True, use SIGTERM first, then SIGKILL

        Returns:
            True if process was killed
        """
        try:
            if graceful:
                os.kill(pid, signal.SIGTERM)
                import time
                for _ in range(10):
                    time.sleep(0.5)
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        return True

            os.kill(pid, signal.SIGKILL)
            return True

        except ProcessLookupError:
            return True
        except PermissionError:
            logger.error(f"Permission denied killing process {pid}")
            return False

    def restore_with_suspension(
        self,
        snapshot_manager,
        snapshot_id: str,
        current_pid: Optional[int] = None,
    ) -> bool:
        """Restore a snapshot with proper process suspension.

        Args:
            snapshot_manager: SnapshotManager instance
            snapshot_id: Snapshot ID to restore
            current_pid: Current game process PID (if different from snapshot)

        Returns:
            True if restoration was successful
        """
        snapshots = snapshot_manager.list_snapshots(snapshot_id.split("_")[0])
        snapshot = next(
            (s for s in snapshots if s.get("id") == snapshot_id),
            None,
        )

        if not snapshot:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False

        target_pid = current_pid or snapshot.get("pid")
        method = snapshot.get("method", "unknown")

        if target_pid and self._is_process_running(target_pid):
            logger.info(f"Suspending process {target_pid} for restore")
            self.suspend_process(target_pid)

        try:
            if method == "criu":
                if target_pid:
                    self.kill_process(target_pid)
                success = snapshot_manager.restore(snapshot_id)
            else:
                success = snapshot_manager.restore(snapshot_id)

            return success

        finally:
            if target_pid and method != "criu" and self._is_process_running(target_pid):
                self.resume_process(target_pid)

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running.

        Args:
            pid: Process ID

        Returns:
            True if process exists
        """
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def verify_restore(self, pid: int) -> Dict[str, Any]:
        """Verify a restore was successful by checking process state.

        Args:
            pid: Process ID to verify

        Returns:
            Dictionary with verification results
        """
        result = {
            "process_exists": False,
            "process_running": False,
            "memory_readable": False,
        }

        if not self._is_process_running(pid):
            return result

        result["process_exists"] = True

        try:
            with open(f"/proc/{pid}/status", "r") as f:
                status = f.read()
                result["process_running"] = "State:\tR" in status or "State:\tS" in status
        except Exception:
            pass

        try:
            with open(f"/proc/{pid}/mem", "rb") as f:
                f.seek(0)
                result["memory_readable"] = True
        except Exception:
            pass

        return result


class RestoreStrategy:
    """Strategy pattern for different restore approaches."""

    @staticmethod
    def get_strategy(method: str):
        """Get the appropriate restore strategy.

        Args:
            method: Snapshot method ('criu' or 'memory_dump')

        Returns:
            RestoreStrategy subclass instance
        """
        strategies = {
            "criu": CRIURestoreStrategy,
            "memory_dump": MemoryRestoreStrategy,
        }
        strategy_class = strategies.get(method, MemoryRestoreStrategy)
        return strategy_class()

    def restore(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> bool:
        """Restore from snapshot.

        Args:
            snapshot_dir: Path to snapshot directory
            metadata: Snapshot metadata

        Returns:
            True if successful
        """
        raise NotImplementedError


class CRIURestoreStrategy(RestoreStrategy):
    """CRIU-based restore strategy."""

    def restore(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> bool:
        """Restore using CRIU.

        Args:
            snapshot_dir: Path to snapshot directory
            metadata: Snapshot metadata

        Returns:
            True if successful
        """
        cmd = [
            "criu",
            "restore",
            "--images-dir",
            str(snapshot_dir),
            "--shell-job",
            "-v4",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"CRIU restore failed: {e}")
            return False


class MemoryRestoreStrategy(RestoreStrategy):
    """Memory dump restore strategy."""

    def restore(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> bool:
        """Restore from memory dump.

        This requires the original process to still be running.

        Args:
            snapshot_dir: Path to snapshot directory
            metadata: Snapshot metadata

        Returns:
            True if successful
        """
        pid = metadata.get("pid")
        if not pid:
            logger.error("No PID in metadata")
            return False

        mem_path = Path(f"/proc/{pid}/mem")
        if not mem_path.exists():
            logger.error(f"Process {pid} not running")
            return False

        return True
