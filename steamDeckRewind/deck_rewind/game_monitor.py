"""Game process monitoring for Deck Rewind."""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil

from .config import Config


logger = logging.getLogger("deck-rewind.game_monitor")


class GameMonitor:
    """Monitors for active game processes on Steam Deck."""

    STEAM_REAPER_PATTERN = re.compile(r"reaper.*SteamLaunch")
    PROTON_PATTERN = re.compile(r"proton|wine|\.exe$", re.IGNORECASE)

    STEAM_PATHS = [
        Path("~/.steam/steam").expanduser(),
        Path("~/.local/share/Steam").expanduser(),
        Path("/home/deck/.steam/steam"),
    ]

    GAME_EXTENSIONS = {".exe", ".x86_64", ".x86", ".sh"}

    EXCLUDED_PROCESSES = {
        "steam",
        "steamwebhelper",
        "steam-runtime",
        "reaper",
        "pressure-vessel",
        "pv-bwrap",
        "proton",
        "wineserver",
        "winedevice.exe",
        "plugplay.exe",
        "services.exe",
        "explorer.exe",
        "start.exe",
        "tabtip.exe",
        "wine64-preloader",
        "wine-preloader",
    }

    def __init__(self, config: Config):
        """Initialize the game monitor.

        Args:
            config: Configuration object
        """
        self.config = config
        self._steam_path: Optional[Path] = None
        self._cached_game: Optional[Dict[str, Any]] = None
        self._last_check: float = 0

    def _find_steam_path(self) -> Optional[Path]:
        """Find the Steam installation path.

        Returns:
            Path to Steam directory or None
        """
        if self._steam_path and self._steam_path.exists():
            return self._steam_path

        for path in self.STEAM_PATHS:
            if path.exists():
                self._steam_path = path
                return path

        return None

    def get_active_game(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active game.

        Returns:
            Dictionary with game info or None if no game detected
        """
        methods = [
            self._detect_via_steam_reaper,
            self._detect_via_proton,
            self._detect_via_steam_process_tree,
        ]

        for method in methods:
            try:
                result = method()
                if result:
                    logger.debug(f"Game detected via {method.__name__}: {result}")
                    return result
            except Exception as e:
                logger.debug(f"Detection method {method.__name__} failed: {e}")
                continue

        return None

    def _detect_via_steam_reaper(self) -> Optional[Dict[str, Any]]:
        """Detect game via Steam reaper process.

        Returns:
            Game info dictionary or None
        """
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline", []) or [])
                if self.STEAM_REAPER_PATTERN.search(cmdline):
                    return self._analyze_reaper_children(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def _analyze_reaper_children(self, reaper_pid: int) -> Optional[Dict[str, Any]]:
        """Analyze children of a reaper process to find the game.

        Args:
            reaper_pid: PID of the reaper process

        Returns:
            Game info dictionary or None
        """
        try:
            reaper = psutil.Process(reaper_pid)
            children = reaper.children(recursive=True)

            for child in children:
                try:
                    name = child.name().lower()

                    if name in self.EXCLUDED_PROCESSES:
                        continue

                    if any(name.endswith(ext) for ext in self.GAME_EXTENSIONS):
                        return self._build_game_info(child)

                    if self.PROTON_PATTERN.search(name):
                        continue

                    cmdline = child.cmdline()
                    if cmdline and any(
                        cmd.endswith(".exe") for cmd in cmdline
                    ):
                        return self._build_game_info(child)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return None

    def _detect_via_proton(self) -> Optional[Dict[str, Any]]:
        """Detect game via Proton/Wine processes.

        Returns:
            Game info dictionary or None
        """
        for proc in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
            try:
                name = proc.info.get("name", "").lower()
                cmdline = proc.info.get("cmdline", []) or []

                if name.endswith(".exe") and name not in self.EXCLUDED_PROCESSES:
                    for arg in cmdline:
                        if "compatdata" in arg:
                            return self._build_game_info_from_proton(proc, arg)

                    return self._build_game_info(proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def _detect_via_steam_process_tree(self) -> Optional[Dict[str, Any]]:
        """Detect game by analyzing Steam's process tree.

        Returns:
            Game info dictionary or None
        """
        steam_procs = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info.get("name", "").lower() == "steam":
                    steam_procs.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for steam_pid in steam_procs:
            try:
                steam = psutil.Process(steam_pid)
                children = steam.children(recursive=True)

                for child in children:
                    try:
                        name = child.name().lower()
                        if name in self.EXCLUDED_PROCESSES:
                            continue

                        if any(name.endswith(ext) for ext in self.GAME_EXTENSIONS):
                            return self._build_game_info(child)

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def _build_game_info(self, proc: psutil.Process) -> Dict[str, Any]:
        """Build game info dictionary from a process.

        Args:
            proc: psutil Process object

        Returns:
            Game info dictionary
        """
        try:
            name = proc.name()
            cmdline = proc.cmdline()
            cwd = proc.cwd()

            game_id = self._extract_game_id(cmdline, cwd) or name

            return {
                "pid": proc.pid,
                "name": self._clean_game_name(name),
                "id": game_id,
                "exe": proc.exe() if hasattr(proc, "exe") else name,
                "cmdline": cmdline,
                "cwd": cwd,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Failed to build game info: {e}")
            return {
                "pid": proc.pid,
                "name": "Unknown",
                "id": str(proc.pid),
            }

    def _build_game_info_from_proton(
        self, proc: psutil.Process, compatdata_path: str
    ) -> Dict[str, Any]:
        """Build game info from Proton compatdata path.

        Args:
            proc: psutil Process object
            compatdata_path: Path containing compatdata

        Returns:
            Game info dictionary
        """
        game_id = self._extract_app_id_from_path(compatdata_path)

        info = self._build_game_info(proc)
        if game_id:
            info["id"] = game_id
            info["name"] = self._get_game_name_from_app_id(game_id) or info["name"]

        return info

    def _extract_game_id(
        self, cmdline: List[str], cwd: str
    ) -> Optional[str]:
        """Extract game ID from command line or working directory.

        Args:
            cmdline: Process command line arguments
            cwd: Process working directory

        Returns:
            Game ID or None
        """
        for arg in cmdline + [cwd]:
            app_id = self._extract_app_id_from_path(arg)
            if app_id:
                return app_id

        return None

    def _extract_app_id_from_path(self, path: str) -> Optional[str]:
        """Extract Steam App ID from a path.

        Args:
            path: File system path

        Returns:
            App ID or None
        """
        patterns = [
            r"compatdata[/\\](\d+)",
            r"steamapps[/\\]common[/\\]([^/\\]+)",
            r"AppId[/\\](\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _get_game_name_from_app_id(self, app_id: str) -> Optional[str]:
        """Get game name from Steam App ID.

        Args:
            app_id: Steam App ID

        Returns:
            Game name or None
        """
        steam_path = self._find_steam_path()
        if not steam_path:
            return None

        manifest_path = steam_path / "steamapps" / f"appmanifest_{app_id}.acf"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, "r") as f:
                content = f.read()
                match = re.search(r'"name"\s+"([^"]+)"', content)
                if match:
                    return match.group(1)
        except Exception:
            pass

        return None

    def _clean_game_name(self, name: str) -> str:
        """Clean up a game process name for display.

        Args:
            name: Raw process name

        Returns:
            Cleaned game name
        """
        name = re.sub(r"\.exe$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\.x86_64$", "", name)
        name = re.sub(r"\.x86$", "", name)
        name = name.replace("_", " ").replace("-", " ")
        name = " ".join(name.split())
        return name.title()

    def is_game_running(self, game_id: str) -> bool:
        """Check if a specific game is running.

        Args:
            game_id: Game identifier

        Returns:
            True if the game is running
        """
        active = self.get_active_game()
        return active is not None and active.get("id") == game_id

    def get_all_running_games(self) -> List[Dict[str, Any]]:
        """Get information about all running games.

        Returns:
            List of game info dictionaries
        """
        games = []
        seen_pids = set()

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info.get("name", "").lower()

                if name in self.EXCLUDED_PROCESSES:
                    continue

                if any(name.endswith(ext) for ext in self.GAME_EXTENSIONS):
                    if proc.info["pid"] not in seen_pids:
                        game_info = self._build_game_info(psutil.Process(proc.info["pid"]))
                        games.append(game_info)
                        seen_pids.add(proc.info["pid"])

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return games

    def wait_for_game(self, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Wait for a game to start.

        Args:
            timeout: Maximum time to wait in seconds (None for infinite)

        Returns:
            Game info when detected or None if timeout
        """
        import time
        start_time = time.time()

        while True:
            game = self.get_active_game()
            if game:
                return game

            if timeout and (time.time() - start_time) > timeout:
                return None

            time.sleep(1)
