"""Tests for game monitoring functionality."""

import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from deck_rewind.config import Config
from deck_rewind.game_monitor import GameMonitor


class TestGameMonitor(TestCase):
    """Test cases for GameMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        with open(self.config_path, "w") as f:
            f.write("""
snapshots:
  storage_path: "/tmp/test_snapshots"
games:
  blacklist: []
  whitelist: []
""")

        self.config = Config(str(self.config_path))
        self.game_monitor = GameMonitor(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_game_name(self):
        """Test game name cleaning."""
        test_cases = [
            ("game.exe", "Game"),
            ("my_awesome_game.x86_64", "My Awesome Game"),
            ("GAME-NAME.x86", "Game Name"),
            ("SimpleGame", "Simplegame"),
        ]

        for input_name, expected in test_cases:
            result = self.game_monitor._clean_game_name(input_name)
            self.assertEqual(result, expected, f"Failed for {input_name}")

    def test_extract_app_id_from_path(self):
        """Test Steam App ID extraction from paths."""
        test_cases = [
            ("/home/user/.steam/steam/steamapps/compatdata/413150/pfx", "413150"),
            ("/steamapps/common/Stardew Valley/game.exe", "Stardew Valley"),
            ("/some/random/path", None),
            ("compatdata/123456/something", "123456"),
        ]

        for path, expected in test_cases:
            result = self.game_monitor._extract_app_id_from_path(path)
            self.assertEqual(result, expected, f"Failed for {path}")

    def test_excluded_processes(self):
        """Test that system processes are properly excluded."""
        excluded = [
            "steam",
            "steamwebhelper",
            "wineserver",
            "proton",
        ]

        for proc in excluded:
            self.assertIn(proc, self.game_monitor.EXCLUDED_PROCESSES)

    def test_game_extensions(self):
        """Test recognized game file extensions."""
        extensions = [".exe", ".x86_64", ".x86", ".sh"]

        for ext in extensions:
            self.assertIn(ext, self.game_monitor.GAME_EXTENSIONS)

    @mock.patch("psutil.process_iter")
    def test_get_active_game_no_games(self, mock_process_iter):
        """Test get_active_game when no games are running."""
        mock_process_iter.return_value = []
        result = self.game_monitor.get_active_game()
        self.assertIsNone(result)

    @mock.patch("psutil.process_iter")
    def test_detect_via_steam_reaper_no_match(self, mock_process_iter):
        """Test Steam reaper detection with no matching processes."""
        mock_process_iter.return_value = []
        result = self.game_monitor._detect_via_steam_reaper()
        self.assertIsNone(result)

    def test_is_game_running_no_game(self):
        """Test is_game_running when no game is active."""
        result = self.game_monitor.is_game_running("some_game_id")
        self.assertFalse(result)


class TestGameMonitorIntegration(TestCase):
    """Integration tests for GameMonitor (may require specific environment)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        with open(self.config_path, "w") as f:
            f.write("""
snapshots:
  storage_path: "/tmp/test_snapshots"
""")

        self.config = Config(str(self.config_path))
        self.game_monitor = GameMonitor(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_all_running_games(self):
        """Test getting all running games (returns empty or actual games)."""
        result = self.game_monitor.get_all_running_games()
        self.assertIsInstance(result, list)

    def test_find_steam_path(self):
        """Test Steam path finding."""
        result = self.game_monitor._find_steam_path()
        self.assertTrue(result is None or isinstance(result, Path))


if __name__ == "__main__":
    import unittest
    unittest.main()
