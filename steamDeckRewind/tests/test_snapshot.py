"""Tests for snapshot functionality."""

import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest import TestCase, mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from deck_rewind.config import Config
from deck_rewind.snapshot import SnapshotManager


class TestSnapshotManager(TestCase):
    """Test cases for SnapshotManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"
        self.storage_path = Path(self.temp_dir) / "snapshots"

        with open(self.config_path, "w") as f:
            f.write(f"""
snapshots:
  storage_path: "{self.storage_path}"
  interval_seconds: 30
  max_rolling_snapshots: 5
  compression: "zstd"
  compression_level: 3
snapshot_method:
  prefer_criu: false
  fallback_to_memory_dump: true
""")

        self.config = Config(str(self.config_path))
        self.snapshot_manager = SnapshotManager(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_storage_path_creation(self):
        """Test that storage path is created."""
        self.assertTrue(self.storage_path.exists())

    def test_criu_availability_check(self):
        """Test CRIU availability detection."""
        result = self.snapshot_manager._check_criu_available()
        self.assertIsInstance(result, bool)

    def test_snapshot_dir_creation(self):
        """Test snapshot directory path generation."""
        snapshot_dir = self.snapshot_manager._get_snapshot_dir("game123", "20240101_120000")
        expected = self.storage_path / "game123" / "20240101_120000"
        self.assertEqual(snapshot_dir, expected)

    def test_list_empty_snapshots(self):
        """Test listing snapshots when none exist."""
        snapshots = self.snapshot_manager.list_snapshots("nonexistent_game")
        self.assertEqual(snapshots, [])

    def test_metadata_save_load(self):
        """Test metadata saving and loading."""
        snapshot_dir = self.storage_path / "test_game" / "20240101_120000"
        snapshot_dir.mkdir(parents=True)

        metadata = {
            "id": "test_game_20240101_120000",
            "game_id": "test_game",
            "pid": 12345,
            "method": "memory_dump",
            "named": False,
        }

        self.snapshot_manager._save_metadata(snapshot_dir, metadata)
        loaded = self.snapshot_manager._load_metadata(snapshot_dir)

        self.assertEqual(loaded["id"], metadata["id"])
        self.assertEqual(loaded["game_id"], metadata["game_id"])
        self.assertEqual(loaded["method"], metadata["method"])

    def test_list_snapshots_with_data(self):
        """Test listing snapshots with actual data."""
        game_dir = self.storage_path / "test_game"

        for i in range(3):
            timestamp = f"2024010{i}_120000"
            snapshot_dir = game_dir / timestamp
            snapshot_dir.mkdir(parents=True)

            metadata = {
                "id": f"test_game_{timestamp}",
                "game_id": "test_game",
                "timestamp": timestamp,
                "method": "memory_dump",
                "named": i == 0,
            }
            self.snapshot_manager._save_metadata(snapshot_dir, metadata)

        snapshots = self.snapshot_manager.list_snapshots("test_game")

        self.assertEqual(len(snapshots), 3)
        self.assertEqual(snapshots[0]["timestamp"], "20240102_120000")

    def test_cleanup_old_snapshots(self):
        """Test cleanup of old rolling snapshots."""
        game_dir = self.storage_path / "test_game"

        for i in range(7):
            timestamp = f"2024010{i}_120000"
            snapshot_dir = game_dir / timestamp
            snapshot_dir.mkdir(parents=True)

            metadata = {
                "id": f"test_game_{timestamp}",
                "game_id": "test_game",
                "timestamp": timestamp,
                "method": "memory_dump",
                "named": False,
            }
            self.snapshot_manager._save_metadata(snapshot_dir, metadata)

        self.snapshot_manager.cleanup_old_snapshots("test_game", max_snapshots=3)

        remaining = self.snapshot_manager.list_snapshots("test_game")
        self.assertEqual(len(remaining), 3)

    def test_named_snapshots_not_cleaned(self):
        """Test that named snapshots are preserved during cleanup."""
        game_dir = self.storage_path / "test_game"

        for i in range(5):
            timestamp = f"2024010{i}_120000"
            snapshot_dir = game_dir / timestamp
            snapshot_dir.mkdir(parents=True)

            metadata = {
                "id": f"test_game_{timestamp}",
                "game_id": "test_game",
                "timestamp": timestamp,
                "method": "memory_dump",
                "named": i < 2,
            }
            self.snapshot_manager._save_metadata(snapshot_dir, metadata)

        self.snapshot_manager.cleanup_old_snapshots("test_game", max_snapshots=2)

        remaining = self.snapshot_manager.list_snapshots("test_game")
        named_count = sum(1 for s in remaining if s.get("named"))
        self.assertEqual(named_count, 2)

    def test_delete_snapshot(self):
        """Test deleting a specific snapshot."""
        game_dir = self.storage_path / "test_game"
        timestamp = "20240101_120000"
        snapshot_dir = game_dir / timestamp
        snapshot_dir.mkdir(parents=True)

        metadata = {
            "id": f"test_game_{timestamp}",
            "game_id": "test_game",
            "timestamp": timestamp,
            "method": "memory_dump",
            "named": False,
        }
        self.snapshot_manager._save_metadata(snapshot_dir, metadata)

        self.assertTrue(snapshot_dir.exists())

        result = self.snapshot_manager.delete_snapshot(f"test_game_{timestamp}")

        self.assertTrue(result)
        self.assertFalse(snapshot_dir.exists())


class TestConfig(TestCase):
    """Test cases for Config."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config_creation(self):
        """Test that default config is created when none exists."""
        config = Config(str(self.config_path))
        self.assertTrue(self.config_path.exists())

    def test_config_get(self):
        """Test getting config values."""
        config = Config(str(self.config_path))

        interval = config.get("snapshots.interval_seconds")
        self.assertEqual(interval, 30)

    def test_config_set(self):
        """Test setting config values."""
        config = Config(str(self.config_path))

        config.set("snapshots.interval_seconds", 60)
        new_value = config.get("snapshots.interval_seconds")
        self.assertEqual(new_value, 60)

    def test_config_properties(self):
        """Test config property accessors."""
        config = Config(str(self.config_path))

        self.assertIsInstance(config.snapshot_interval, int)
        self.assertIsInstance(config.max_snapshots, int)
        self.assertIsInstance(config.prefer_criu, bool)
        self.assertIsInstance(config.storage_path, Path)


class TestMemorySnapshot(TestCase):
    """Test cases for memory snapshot functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"
        self.storage_path = Path(self.temp_dir) / "snapshots"

        with open(self.config_path, "w") as f:
            f.write(f"""
snapshots:
  storage_path: "{self.storage_path}"
snapshot_method:
  prefer_criu: false
  fallback_to_memory_dump: true
""")

        self.config = Config(str(self.config_path))
        self.snapshot_manager = SnapshotManager(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch("builtins.open", mock.mock_open(read_data=""))
    def test_memory_snapshot_nonexistent_process(self):
        """Test memory snapshot of non-existent process."""
        result = self.snapshot_manager._create_memory_snapshot(
            99999999,
            self.storage_path / "test" / "snapshot1",
        )
        self.assertFalse(result)

    def test_process_state_saving(self):
        """Test that process state info is saved."""
        snapshot_dir = self.storage_path / "test_process"
        snapshot_dir.mkdir(parents=True)

        current_pid = os.getpid()
        self.snapshot_manager._save_process_state(current_pid, snapshot_dir)

        state_file = snapshot_dir / "process_state.json"
        self.assertTrue(state_file.exists())

        with open(state_file, "r") as f:
            state = json.load(f)

        self.assertEqual(state["pid"], current_pid)
        self.assertIn("cmdline", state)
        self.assertIn("cwd", state)


if __name__ == "__main__":
    import unittest
    unittest.main()
