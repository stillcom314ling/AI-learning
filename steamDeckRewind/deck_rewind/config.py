"""Configuration management for Deck Rewind."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG = {
    "snapshots": {
        "interval_seconds": 30,
        "max_rolling_snapshots": 10,
        "storage_path": "~/.local/share/deck-rewind/snapshots",
        "compression": "zstd",
        "compression_level": 3,
    },
    "snapshot_method": {
        "prefer_criu": True,
        "fallback_to_memory_dump": True,
        "save_thread_contexts": True,
    },
    "storage": {
        "max_total_size_gb": 10,
        "auto_cleanup": True,
    },
    "hotkeys": {
        "rewind_previous": "steam+l2",
        "rewind_back": "steam+dpad_left",
        "rewind_forward": "steam+dpad_right",
        "list_snapshots": "steam+dpad_up",
        "manual_snapshot": "steam+l1",
    },
    "ui": {
        "show_notifications": True,
        "notification_duration_seconds": 3,
        "overlay_position": "top-right",
    },
    "games": {
        "blacklist": [],
        "whitelist": [],
    },
}


class Config:
    """Manages Deck Rewind configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. Defaults to ~/.config/deck-rewind/config.yaml
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            self.config_path = Path("~/.config/deck-rewind/config.yaml").expanduser()

        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, creating defaults if necessary."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
            self.config = self._merge_configs(DEFAULT_CONFIG, user_config)
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.save()

    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def _merge_configs(
        self, default: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge user config into default config.

        Args:
            default: Default configuration dictionary
            user: User configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'snapshots.interval_seconds')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()

    @property
    def snapshot_interval(self) -> int:
        """Get snapshot interval in seconds."""
        return self.get("snapshots.interval_seconds", 30)

    @property
    def max_snapshots(self) -> int:
        """Get maximum number of rolling snapshots."""
        return self.get("snapshots.max_rolling_snapshots", 10)

    @property
    def storage_path(self) -> Path:
        """Get snapshot storage path."""
        path = self.get("snapshots.storage_path", "~/.local/share/deck-rewind/snapshots")
        return Path(path).expanduser()

    @property
    def prefer_criu(self) -> bool:
        """Check if CRIU is preferred snapshot method."""
        return self.get("snapshot_method.prefer_criu", True)

    @property
    def fallback_to_memory_dump(self) -> bool:
        """Check if memory dump fallback is enabled."""
        return self.get("snapshot_method.fallback_to_memory_dump", True)

    @property
    def max_storage_gb(self) -> int:
        """Get maximum storage size in GB."""
        return self.get("storage.max_total_size_gb", 10)

    @property
    def show_notifications(self) -> bool:
        """Check if notifications are enabled."""
        return self.get("ui.show_notifications", True)

    @property
    def game_blacklist(self) -> list:
        """Get list of blacklisted game IDs."""
        return self.get("games.blacklist", [])

    @property
    def game_whitelist(self) -> list:
        """Get list of whitelisted game IDs."""
        return self.get("games.whitelist", [])
