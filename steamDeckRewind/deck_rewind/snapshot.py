"""Snapshot management for Deck Rewind."""

import os
import subprocess
import time
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import Config


logger = logging.getLogger("deck-rewind.snapshot")


class SnapshotManager:
    """Manages game state snapshots using CRIU or memory dump fallback."""

    def __init__(self, config: Config):
        """Initialize the snapshot manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.storage_path = config.storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._criu_available: Optional[bool] = None

    def _check_criu_available(self) -> bool:
        """Check if CRIU is available on the system.

        Returns:
            True if CRIU is available, False otherwise
        """
        if self._criu_available is not None:
            return self._criu_available

        try:
            result = subprocess.run(
                ["criu", "--version"],
                capture_output=True,
                timeout=5,
            )
            self._criu_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._criu_available = False

        return self._criu_available

    def _get_snapshot_dir(self, game_id: str, timestamp: str) -> Path:
        """Get the directory path for a snapshot.

        Args:
            game_id: Game identifier
            timestamp: Snapshot timestamp

        Returns:
            Path to snapshot directory
        """
        return self.storage_path / game_id / timestamp

    def _get_game_snapshot_dir(self, game_id: str) -> Path:
        """Get the base directory for a game's snapshots.

        Args:
            game_id: Game identifier

        Returns:
            Path to game's snapshot directory
        """
        return self.storage_path / game_id

    def create(self, pid: int, game_id: str, named: bool = False) -> bool:
        """Create a snapshot of a game process.

        Args:
            pid: Process ID of the game
            game_id: Game identifier
            named: Whether this is a named (persistent) snapshot

        Returns:
            True if snapshot was created successfully
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = self._get_snapshot_dir(game_id, timestamp)
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        method = "unknown"
        success = False

        if self.config.prefer_criu and self._check_criu_available():
            logger.info(f"Attempting CRIU snapshot for PID {pid}")
            success = self._create_criu_snapshot(pid, snapshot_dir)
            if success:
                method = "criu"

        if not success and self.config.fallback_to_memory_dump:
            logger.info(f"Using memory dump fallback for PID {pid}")
            success = self._create_memory_snapshot(pid, snapshot_dir)
            if success:
                method = "memory_dump"

        if success:
            metadata = {
                "id": f"{game_id}_{timestamp}",
                "game_id": game_id,
                "pid": pid,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "method": method,
                "named": named,
            }
            self._save_metadata(snapshot_dir, metadata)
            logger.info(f"Snapshot created: {metadata['id']} using {method}")
        else:
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            logger.error(f"Failed to create snapshot for PID {pid}")

        return success

    def _create_criu_snapshot(self, pid: int, snapshot_dir: Path) -> bool:
        """Create a snapshot using CRIU.

        Args:
            pid: Process ID to snapshot
            snapshot_dir: Directory to store snapshot

        Returns:
            True if successful
        """
        cmd = [
            "criu",
            "dump",
            "-t",
            str(pid),
            "--shell-job",
            "--leave-running",
            "--images-dir",
            str(snapshot_dir),
            "-v4",
            "--log-file",
            str(snapshot_dir / "criu.log"),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.warning(f"CRIU dump failed: {result.stderr.decode()}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.warning("CRIU dump timed out")
            return False
        except Exception as e:
            logger.warning(f"CRIU dump error: {e}")
            return False

    def _create_memory_snapshot(self, pid: int, snapshot_dir: Path) -> bool:
        """Create a snapshot using direct memory dump.

        Args:
            pid: Process ID to snapshot
            snapshot_dir: Directory to store snapshot

        Returns:
            True if successful
        """
        try:
            maps_file = Path(f"/proc/{pid}/maps")
            mem_file = Path(f"/proc/{pid}/mem")

            if not maps_file.exists():
                logger.error(f"Process {pid} not found")
                return False

            with open(maps_file, "r") as f:
                maps_content = f.readlines()

            with open(snapshot_dir / "maps.txt", "w") as f:
                f.writelines(maps_content)

            regions_saved = 0

            try:
                import zstd
                use_zstd = True
            except ImportError:
                use_zstd = False
                logger.warning("zstd not available, using uncompressed storage")

            with open(mem_file, "rb") as mem:
                for line in maps_content:
                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    addr_range = parts[0]
                    perms = parts[1]

                    if "r" not in perms:
                        continue

                    try:
                        start_str, end_str = addr_range.split("-")
                        start = int(start_str, 16)
                        end = int(end_str, 16)

                        size = end - start
                        if size > 100 * 1024 * 1024:
                            continue

                        mem.seek(start)
                        data = mem.read(size)

                        filename = f"{start:016x}-{end:016x}"

                        if use_zstd:
                            compressed = zstd.compress(
                                data, self.config.get("snapshots.compression_level", 3)
                            )
                            with open(snapshot_dir / f"{filename}.bin.zst", "wb") as f:
                                f.write(compressed)
                        else:
                            with open(snapshot_dir / f"{filename}.bin", "wb") as f:
                                f.write(data)

                        regions_saved += 1

                    except (ValueError, OSError) as e:
                        continue

            if regions_saved == 0:
                logger.error("No memory regions could be saved")
                return False

            logger.info(f"Saved {regions_saved} memory regions")

            self._save_process_state(pid, snapshot_dir)

            return True

        except PermissionError:
            logger.error(f"Permission denied reading process {pid} memory")
            return False
        except Exception as e:
            logger.error(f"Memory snapshot error: {e}")
            return False

    def _save_process_state(self, pid: int, snapshot_dir: Path) -> None:
        """Save additional process state information.

        Args:
            pid: Process ID
            snapshot_dir: Directory to store state
        """
        state = {
            "pid": pid,
            "cmdline": "",
            "cwd": "",
            "environ": {},
        }

        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                state["cmdline"] = f.read().decode(errors="replace").replace("\0", " ")
        except Exception:
            pass

        try:
            state["cwd"] = os.readlink(f"/proc/{pid}/cwd")
        except Exception:
            pass

        try:
            with open(f"/proc/{pid}/environ", "rb") as f:
                environ_raw = f.read().decode(errors="replace")
                for item in environ_raw.split("\0"):
                    if "=" in item:
                        key, value = item.split("=", 1)
                        state["environ"][key] = value
        except Exception:
            pass

        with open(snapshot_dir / "process_state.json", "w") as f:
            json.dump(state, f, indent=2)

    def _save_metadata(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> None:
        """Save snapshot metadata.

        Args:
            snapshot_dir: Snapshot directory
            metadata: Metadata dictionary
        """
        with open(snapshot_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, snapshot_dir: Path) -> Optional[Dict[str, Any]]:
        """Load snapshot metadata.

        Args:
            snapshot_dir: Snapshot directory

        Returns:
            Metadata dictionary or None if not found
        """
        metadata_file = snapshot_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def list_snapshots(self, game_id: str) -> List[Dict[str, Any]]:
        """List all snapshots for a game.

        Args:
            game_id: Game identifier

        Returns:
            List of snapshot metadata, sorted by timestamp (newest first)
        """
        game_dir = self._get_game_snapshot_dir(game_id)
        if not game_dir.exists():
            return []

        snapshots = []
        for snapshot_dir in game_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            metadata = self._load_metadata(snapshot_dir)
            if metadata:
                size_mb = sum(
                    f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file()
                ) / (1024 * 1024)
                metadata["size_mb"] = size_mb
                metadata["path"] = str(snapshot_dir)
                snapshots.append(metadata)

        snapshots.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return snapshots

    def restore(self, snapshot_id: str) -> bool:
        """Restore a snapshot.

        Args:
            snapshot_id: Snapshot identifier (format: game_id_timestamp)

        Returns:
            True if restore was successful
        """
        parts = snapshot_id.rsplit("_", 2)
        if len(parts) < 3:
            logger.error(f"Invalid snapshot ID: {snapshot_id}")
            return False

        game_id = "_".join(parts[:-2])
        timestamp = "_".join(parts[-2:])

        snapshot_dir = self._get_snapshot_dir(game_id, timestamp)
        if not snapshot_dir.exists():
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False

        metadata = self._load_metadata(snapshot_dir)
        if not metadata:
            logger.error(f"Snapshot metadata not found: {snapshot_id}")
            return False

        method = metadata.get("method", "unknown")

        if method == "criu":
            return self._restore_criu(snapshot_dir, metadata)
        elif method == "memory_dump":
            return self._restore_memory(snapshot_dir, metadata)
        else:
            logger.error(f"Unknown snapshot method: {method}")
            return False

    def _restore_criu(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> bool:
        """Restore a CRIU snapshot.

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
            "--log-file",
            str(snapshot_dir / "criu_restore.log"),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(f"CRIU restore failed: {result.stderr.decode()}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error("CRIU restore timed out")
            return False
        except Exception as e:
            logger.error(f"CRIU restore error: {e}")
            return False

    def _restore_memory(self, snapshot_dir: Path, metadata: Dict[str, Any]) -> bool:
        """Restore a memory dump snapshot.

        This is a best-effort restoration that attempts to restore memory
        to a running process. Full restoration requires the original process
        to still be running.

        Args:
            snapshot_dir: Path to snapshot directory
            metadata: Snapshot metadata

        Returns:
            True if successful
        """
        pid = metadata.get("pid")
        if not pid:
            logger.error("No PID in snapshot metadata")
            return False

        if not Path(f"/proc/{pid}").exists():
            logger.error(f"Process {pid} is no longer running")
            logger.info("Memory dump restore requires the process to be running")
            return False

        try:
            import zstd
            use_zstd = True
        except ImportError:
            use_zstd = False

        maps_file = snapshot_dir / "maps.txt"
        if not maps_file.exists():
            logger.error("Memory maps file not found")
            return False

        mem_file = Path(f"/proc/{pid}/mem")
        regions_restored = 0

        try:
            with open(mem_file, "r+b") as mem:
                for data_file in snapshot_dir.glob("*.bin*"):
                    filename = data_file.stem
                    if filename.endswith(".bin"):
                        filename = filename[:-4]

                    try:
                        parts = filename.replace(".bin", "").split("-")
                        start = int(parts[0], 16)

                        if str(data_file).endswith(".zst") and use_zstd:
                            with open(data_file, "rb") as f:
                                compressed = f.read()
                            data = zstd.decompress(compressed)
                        else:
                            with open(data_file, "rb") as f:
                                data = f.read()

                        mem.seek(start)
                        mem.write(data)
                        regions_restored += 1

                    except Exception as e:
                        logger.debug(f"Could not restore region {filename}: {e}")
                        continue

            logger.info(f"Restored {regions_restored} memory regions")
            return regions_restored > 0

        except PermissionError:
            logger.error(f"Permission denied writing to process {pid} memory")
            return False
        except Exception as e:
            logger.error(f"Memory restore error: {e}")
            return False

    def cleanup_old_snapshots(self, game_id: str, max_snapshots: int) -> None:
        """Clean up old rolling snapshots.

        Keeps named snapshots and only removes unnamed ones beyond the limit.

        Args:
            game_id: Game identifier
            max_snapshots: Maximum number of rolling snapshots to keep
        """
        snapshots = self.list_snapshots(game_id)

        rolling_snapshots = [s for s in snapshots if not s.get("named", False)]

        if len(rolling_snapshots) <= max_snapshots:
            return

        to_delete = rolling_snapshots[max_snapshots:]

        for snapshot in to_delete:
            snapshot_path = Path(snapshot.get("path", ""))
            if snapshot_path.exists():
                logger.info(f"Deleting old snapshot: {snapshot.get('id')}")
                shutil.rmtree(snapshot_path, ignore_errors=True)

    def cleanup_by_size(self, max_size_gb: float) -> None:
        """Clean up snapshots to stay within storage limits.

        Args:
            max_size_gb: Maximum total storage size in GB
        """
        total_size = 0
        all_snapshots = []

        for game_dir in self.storage_path.iterdir():
            if not game_dir.is_dir():
                continue

            for snapshot_dir in game_dir.iterdir():
                if not snapshot_dir.is_dir():
                    continue

                metadata = self._load_metadata(snapshot_dir)
                if not metadata:
                    continue

                size = sum(
                    f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file()
                )
                total_size += size
                all_snapshots.append({
                    "path": snapshot_dir,
                    "size": size,
                    "timestamp": metadata.get("timestamp", ""),
                    "named": metadata.get("named", False),
                })

        max_size_bytes = max_size_gb * 1024 * 1024 * 1024

        if total_size <= max_size_bytes:
            return

        unnamed = [s for s in all_snapshots if not s["named"]]
        unnamed.sort(key=lambda x: x["timestamp"])

        for snapshot in unnamed:
            if total_size <= max_size_bytes:
                break

            logger.info(f"Deleting snapshot due to size limit: {snapshot['path']}")
            shutil.rmtree(snapshot["path"], ignore_errors=True)
            total_size -= snapshot["size"]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a specific snapshot.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            True if deletion was successful
        """
        parts = snapshot_id.rsplit("_", 2)
        if len(parts) < 3:
            return False

        game_id = "_".join(parts[:-2])
        timestamp = "_".join(parts[-2:])

        snapshot_dir = self._get_snapshot_dir(game_id, timestamp)
        if not snapshot_dir.exists():
            return False

        shutil.rmtree(snapshot_dir, ignore_errors=True)
        logger.info(f"Deleted snapshot: {snapshot_id}")
        return True
