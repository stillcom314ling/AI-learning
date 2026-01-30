"""Hotkey listener for Steam Deck controller input."""

import os
import glob
import logging
import threading
from typing import Callable, Dict, List, Optional, Set

from .config import Config


logger = logging.getLogger("deck-rewind.hotkey")


try:
    from evdev import InputDevice, categorize, ecodes, list_devices
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    logger.warning("evdev not available, hotkey support disabled")


class HotkeyListener:
    """Listens for controller hotkey combinations on Steam Deck."""

    STEAM_DECK_CONTROLLER_NAMES = [
        "Steam Deck",
        "Steam Controller",
        "Valve Software Steam Controller",
        "Steam Virtual Gamepad",
    ]

    BUTTON_CODES = {
        "steam": 316,
        "l1": 310,
        "l2": 312,
        "r1": 311,
        "r2": 313,
        "dpad_up": 544,
        "dpad_down": 545,
        "dpad_left": 546,
        "dpad_right": 547,
        "a": 304,
        "b": 305,
        "x": 307,
        "y": 308,
        "start": 315,
        "select": 314,
    }

    AXIS_CODES = {
        "l2_axis": 2,
        "r2_axis": 5,
    }

    def __init__(self, config: Config):
        """Initialize the hotkey listener.

        Args:
            config: Configuration object
        """
        self.config = config
        self.handlers: Dict[str, Callable] = {}
        self.pressed_buttons: Set[str] = set()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._devices: List = []
        self._trigger_threshold = 200

    def _find_controller_devices(self) -> List:
        """Find Steam Deck controller input devices.

        Returns:
            List of InputDevice objects
        """
        if not EVDEV_AVAILABLE:
            return []

        devices = []

        try:
            for device_path in list_devices():
                try:
                    device = InputDevice(device_path)

                    if any(
                        name.lower() in device.name.lower()
                        for name in self.STEAM_DECK_CONTROLLER_NAMES
                    ):
                        devices.append(device)
                        logger.info(f"Found controller: {device.name} at {device_path}")
                except Exception as e:
                    logger.debug(f"Could not open device {device_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error listing devices: {e}")

        if not devices:
            try:
                for pattern in ["/dev/input/event*", "/dev/input/js*"]:
                    for path in glob.glob(pattern):
                        try:
                            device = InputDevice(path)
                            if "gamepad" in device.name.lower() or "controller" in device.name.lower():
                                devices.append(device)
                                logger.info(f"Found gamepad: {device.name} at {path}")
                        except Exception:
                            continue
            except Exception:
                pass

        return devices

    def register_handler(self, hotkey: str, handler: Callable) -> None:
        """Register a handler for a hotkey combination.

        Args:
            hotkey: Hotkey string (e.g., "steam+l2")
            handler: Function to call when hotkey is pressed
        """
        normalized = self._normalize_hotkey(hotkey)
        self.handlers[normalized] = handler
        logger.debug(f"Registered handler for: {normalized}")

    def unregister_handler(self, hotkey: str) -> None:
        """Unregister a hotkey handler.

        Args:
            hotkey: Hotkey string to unregister
        """
        normalized = self._normalize_hotkey(hotkey)
        if normalized in self.handlers:
            del self.handlers[normalized]

    def _normalize_hotkey(self, hotkey: str) -> str:
        """Normalize a hotkey string for consistent comparison.

        Args:
            hotkey: Hotkey string (e.g., "Steam+L2")

        Returns:
            Normalized hotkey string (e.g., "steam+l2")
        """
        parts = hotkey.lower().replace(" ", "").split("+")
        parts.sort()
        return "+".join(parts)

    def _get_pressed_hotkey(self) -> str:
        """Get the current pressed buttons as a hotkey string.

        Returns:
            Normalized hotkey string of currently pressed buttons
        """
        if not self.pressed_buttons:
            return ""

        parts = sorted(self.pressed_buttons)
        return "+".join(parts)

    def _check_hotkeys(self) -> None:
        """Check if any registered hotkeys are pressed and trigger handlers."""
        current_hotkey = self._get_pressed_hotkey()

        if current_hotkey in self.handlers:
            logger.info(f"Hotkey triggered: {current_hotkey}")
            try:
                self.handlers[current_hotkey]()
            except Exception as e:
                logger.error(f"Hotkey handler error: {e}")

            self.pressed_buttons.clear()

    def _button_name_from_code(self, code: int) -> Optional[str]:
        """Get button name from evdev code.

        Args:
            code: evdev button code

        Returns:
            Button name or None
        """
        for name, btn_code in self.BUTTON_CODES.items():
            if btn_code == code:
                return name
        return None

    def _process_event(self, event) -> None:
        """Process a single input event.

        Args:
            event: evdev event object
        """
        if not EVDEV_AVAILABLE:
            return

        if event.type == ecodes.EV_KEY:
            button_name = self._button_name_from_code(event.code)

            if button_name:
                if event.value == 1:
                    self.pressed_buttons.add(button_name)
                    self._check_hotkeys()
                elif event.value == 0:
                    self.pressed_buttons.discard(button_name)

        elif event.type == ecodes.EV_ABS:
            if event.code == self.AXIS_CODES.get("l2_axis"):
                if event.value > self._trigger_threshold:
                    self.pressed_buttons.add("l2")
                else:
                    self.pressed_buttons.discard("l2")

            elif event.code == self.AXIS_CODES.get("r2_axis"):
                if event.value > self._trigger_threshold:
                    self.pressed_buttons.add("r2")
                else:
                    self.pressed_buttons.discard("r2")

    def process_events(self) -> None:
        """Process pending input events (non-blocking)."""
        if not EVDEV_AVAILABLE:
            return

        for device in self._devices:
            try:
                while True:
                    event = device.read_one()
                    if event is None:
                        break
                    self._process_event(event)
            except Exception:
                continue

    def _listen_loop(self) -> None:
        """Main listening loop for background thread."""
        if not EVDEV_AVAILABLE:
            logger.error("evdev not available, cannot start listener")
            return

        try:
            import select

            while self.running:
                readable, _, _ = select.select(self._devices, [], [], 0.1)

                for device in readable:
                    try:
                        for event in device.read():
                            self._process_event(event)
                    except Exception as e:
                        logger.debug(f"Error reading device: {e}")
                        continue

        except Exception as e:
            logger.error(f"Listener loop error: {e}")

    def start(self, background: bool = True) -> None:
        """Start listening for hotkeys.

        Args:
            background: If True, run in background thread
        """
        if not EVDEV_AVAILABLE:
            logger.warning("Hotkey listener disabled (evdev not available)")
            return

        self._devices = self._find_controller_devices()

        if not self._devices:
            logger.warning("No controller devices found")
            return

        self.running = True

        if background:
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            logger.info("Hotkey listener started in background")
        else:
            logger.info("Hotkey listener starting in foreground")
            self._listen_loop()

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self.running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        for device in self._devices:
            try:
                device.close()
            except Exception:
                pass

        self._devices = []
        logger.info("Hotkey listener stopped")

    def is_button_pressed(self, button: str) -> bool:
        """Check if a specific button is currently pressed.

        Args:
            button: Button name (e.g., "steam", "l2")

        Returns:
            True if button is pressed
        """
        return button.lower() in self.pressed_buttons


class SimulatedHotkeyListener:
    """Simulated hotkey listener for testing without hardware."""

    def __init__(self, config: Config):
        """Initialize the simulated listener.

        Args:
            config: Configuration object
        """
        self.config = config
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, hotkey: str, handler: Callable) -> None:
        """Register a handler."""
        normalized = hotkey.lower().replace(" ", "")
        self.handlers[normalized] = handler

    def unregister_handler(self, hotkey: str) -> None:
        """Unregister a handler."""
        normalized = hotkey.lower().replace(" ", "")
        if normalized in self.handlers:
            del self.handlers[normalized]

    def simulate_hotkey(self, hotkey: str) -> bool:
        """Simulate a hotkey press.

        Args:
            hotkey: Hotkey string to simulate

        Returns:
            True if a handler was triggered
        """
        normalized = hotkey.lower().replace(" ", "")
        if normalized in self.handlers:
            self.handlers[normalized]()
            return True
        return False

    def start(self, background: bool = True) -> None:
        """Start the simulated listener (no-op)."""
        logger.info("Simulated hotkey listener started")

    def stop(self) -> None:
        """Stop the simulated listener (no-op)."""
        logger.info("Simulated hotkey listener stopped")

    def process_events(self) -> None:
        """Process events (no-op for simulation)."""
        pass
