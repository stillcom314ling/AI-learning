"""Tests for hotkey listener functionality."""

import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from deck_rewind.config import Config
from deck_rewind.hotkey_listener import HotkeyListener, SimulatedHotkeyListener


class TestHotkeyListener(TestCase):
    """Test cases for HotkeyListener."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        with open(self.config_path, "w") as f:
            f.write("""
hotkeys:
  rewind_previous: "steam+l2"
  manual_snapshot: "steam+l1"
""")

        self.config = Config(str(self.config_path))
        self.hotkey_listener = HotkeyListener(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_hotkey(self):
        """Test hotkey normalization."""
        test_cases = [
            ("Steam+L2", "l2+steam"),
            ("steam + l2", "l2+steam"),
            ("L1+Steam", "l1+steam"),
            ("dpad_up+steam", "dpad_up+steam"),
        ]

        for input_key, expected in test_cases:
            result = self.hotkey_listener._normalize_hotkey(input_key)
            self.assertEqual(result, expected, f"Failed for {input_key}")

    def test_register_handler(self):
        """Test handler registration."""
        handler_called = [False]

        def test_handler():
            handler_called[0] = True

        self.hotkey_listener.register_handler("steam+l2", test_handler)

        self.assertIn("l2+steam", self.hotkey_listener.handlers)

    def test_unregister_handler(self):
        """Test handler unregistration."""
        def test_handler():
            pass

        self.hotkey_listener.register_handler("steam+l2", test_handler)
        self.hotkey_listener.unregister_handler("steam+l2")

        self.assertNotIn("l2+steam", self.hotkey_listener.handlers)

    def test_button_name_from_code(self):
        """Test button code to name mapping."""
        test_cases = [
            (316, "steam"),
            (310, "l1"),
            (312, "l2"),
            (544, "dpad_up"),
            (999, None),
        ]

        for code, expected in test_cases:
            result = self.hotkey_listener._button_name_from_code(code)
            self.assertEqual(result, expected, f"Failed for code {code}")

    def test_get_pressed_hotkey_empty(self):
        """Test getting pressed hotkey when nothing is pressed."""
        result = self.hotkey_listener._get_pressed_hotkey()
        self.assertEqual(result, "")

    def test_get_pressed_hotkey_single(self):
        """Test getting pressed hotkey with single button."""
        self.hotkey_listener.pressed_buttons.add("steam")
        result = self.hotkey_listener._get_pressed_hotkey()
        self.assertEqual(result, "steam")

    def test_get_pressed_hotkey_combo(self):
        """Test getting pressed hotkey with button combo."""
        self.hotkey_listener.pressed_buttons.add("steam")
        self.hotkey_listener.pressed_buttons.add("l2")
        result = self.hotkey_listener._get_pressed_hotkey()
        self.assertEqual(result, "l2+steam")

    def test_is_button_pressed(self):
        """Test button press checking."""
        self.hotkey_listener.pressed_buttons.add("steam")

        self.assertTrue(self.hotkey_listener.is_button_pressed("steam"))
        self.assertTrue(self.hotkey_listener.is_button_pressed("STEAM"))
        self.assertFalse(self.hotkey_listener.is_button_pressed("l2"))


class TestSimulatedHotkeyListener(TestCase):
    """Test cases for SimulatedHotkeyListener."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        with open(self.config_path, "w") as f:
            f.write("""
hotkeys:
  rewind_previous: "steam+l2"
""")

        self.config = Config(str(self.config_path))
        self.listener = SimulatedHotkeyListener(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_simulate_hotkey_triggers_handler(self):
        """Test that simulated hotkey triggers registered handler."""
        handler_called = [False]

        def test_handler():
            handler_called[0] = True

        self.listener.register_handler("steam+l2", test_handler)
        result = self.listener.simulate_hotkey("steam+l2")

        self.assertTrue(result)
        self.assertTrue(handler_called[0])

    def test_simulate_hotkey_no_handler(self):
        """Test simulating hotkey with no registered handler."""
        result = self.listener.simulate_hotkey("steam+l2")
        self.assertFalse(result)

    def test_start_stop(self):
        """Test that start/stop don't raise errors."""
        self.listener.start()
        self.listener.stop()


class TestButtonCodes(TestCase):
    """Test cases for button code mappings."""

    def test_all_buttons_have_codes(self):
        """Test that all expected buttons have codes defined."""
        expected_buttons = [
            "steam", "l1", "l2", "r1", "r2",
            "dpad_up", "dpad_down", "dpad_left", "dpad_right",
            "a", "b", "x", "y", "start", "select",
        ]

        for button in expected_buttons:
            self.assertIn(button, HotkeyListener.BUTTON_CODES, f"Missing code for {button}")

    def test_button_codes_are_integers(self):
        """Test that all button codes are integers."""
        for button, code in HotkeyListener.BUTTON_CODES.items():
            self.assertIsInstance(code, int, f"Non-integer code for {button}")


if __name__ == "__main__":
    import unittest
    unittest.main()
