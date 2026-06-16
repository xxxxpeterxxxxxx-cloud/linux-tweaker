"""
Desktop Environment / Window Manager Detection
Detects the active DE/WM via environment variables, running processes, and config files.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DEInfo:
    """Info about the detected desktop environment."""
    name: str
    type: str  # "DE" or "WM"
    engine: str  # ThemeEngine class name
    detected_by: Optional[str] = None


class DEDetector:
    """Detects the active desktop environment or window manager."""

    ENGINE_MAP = {
        "GNOME": "GnomeThemeEngine",
        "ubuntu:GNOME": "GnomeThemeEngine",
        "pop:GNOME": "GnomeThemeEngine",
        "bluefin:GNOME": "GnomeThemeEngine",
        "Bluefin": "GnomeThemeEngine",
        "bluefin": "GnomeThemeEngine",
        "Silverblue": "GnomeThemeEngine",
        "silverblue": "GnomeThemeEngine",
        "Fedora": "GnomeThemeEngine",
        "Cinnamon": "GnomeThemeEngine",
        "KDE": "PlasmaThemeEngine",
        "LXQt": "LxqtThemeEngine",
        "XFCE": "XfceThemeEngine",
        "MATE": "MateThemeEngine",
        "sway": "SwayThemeEngine",
        "Hyprland": "HyprlandThemeEngine",
        "i3": "I3ThemeEngine",
        "bspwm": "BspwmThemeEngine",
    }

    def detect(self) -> DEInfo:
        """Main detection entry point."""
        # 1. Check $XDG_CURRENT_DESKTOP (highest priority)
        xdg = os.environ.get("XDG_CURRENT_DESKTOP", "")
        for de_name in xdg.split(":"):
            if de_name in self.ENGINE_MAP:
                return DEInfo(
                    name=de_name,
                    type="DE",
                    engine=self.ENGINE_MAP[de_name],
                    detected_by="XDG_CURRENT_DESKTOP",
                )

        # 2. Check $DESKTOP_SESSION
        session = os.environ.get("DESKTOP_SESSION", "")
        if session in self.ENGINE_MAP:
            return DEInfo(
                name=session,
                type="DE",
                engine=self.ENGINE_MAP[session],
                detected_by="DESKTOP_SESSION",
            )

        # 3. Process detection
        by_proc = self._detect_by_process()
        if by_proc:
            return by_proc

        # 4. Config file detection
        by_cfg = self._detect_by_config()
        if by_cfg:
            return by_cfg

        return DEInfo(
            name="Unknown",
            type="Unknown",
            engine="GenericThemeEngine",
            detected_by="fallback",
        )

    def _detect_by_process(self) -> Optional[DEInfo]:
        """Detect DE/WM by looking at running processes. Uses pgrep for faster detection."""
        # Try pgrep first (faster than ps aux on systems with many processes)
        try:
            result = subprocess.run(
                ["pgrep", "-l", "-x", "gnome-shell", "plasmashell", "Hyprland", "sway", "xfce4-session", "i3"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                proc = result.stdout.lower()
                if "gnome-shell" in proc:
                    return DEInfo(name="GNOME", type="DE", engine="GnomeThemeEngine", detected_by="process")
                if "plasmashell" in proc:
                    return DEInfo(name="KDE", type="DE", engine="PlasmaThemeEngine", detected_by="process")
                if "hyprland" in proc:
                    return DEInfo(name="Hyprland", type="WM", engine="HyprlandThemeEngine", detected_by="process")
                if "sway" in proc:
                    return DEInfo(name="sway", type="WM", engine="SwayThemeEngine", detected_by="process")
                if "xfce4-session" in proc:
                    return DEInfo(name="XFCE", type="DE", engine="XfceThemeEngine", detected_by="process")
                if "i3" in proc:
                    return DEInfo(name="i3", type="WM", engine="I3ThemeEngine", detected_by="process")
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            # Fallback to ps aux if pgrep is not available
            pass

        # Fallback to ps aux (slower but more portable)
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                check=False,
            )
            proc = result.stdout.lower()
        except (subprocess.SubprocessError, OSError) as e:
            return None

        if "gnome-shell" in proc:
            return DEInfo(name="GNOME", type="DE", engine="GnomeThemeEngine", detected_by="process")
        if "plasmashell" in proc:
            return DEInfo(name="KDE", type="DE", engine="PlasmaThemeEngine", detected_by="process")
        if "hyprland" in proc:
            return DEInfo(name="Hyprland", type="WM", engine="HyprlandThemeEngine", detected_by="process")
        if "sway" in proc:
            return DEInfo(name="sway", type="WM", engine="SwayThemeEngine", detected_by="process")
        if "xfce4-session" in proc or "xfce4-panel" in proc:
            return DEInfo(name="XFCE", type="DE", engine="XfceThemeEngine", detected_by="process")
        if "i3" in proc:
            return DEInfo(name="i3", type="WM", engine="I3ThemeEngine", detected_by="process")

        return None

    def _detect_by_config(self) -> Optional[DEInfo]:
        """Detect DE/WM by checking config directories."""
        cfg = Path.home() / ".config"

        if (cfg / "hypr" / "hyprland.conf").exists():
            return DEInfo(name="Hyprland", type="WM", engine="HyprlandThemeEngine", detected_by="config")
        if (cfg / "sway" / "config").exists():
            return DEInfo(name="sway", type="WM", engine="SwayThemeEngine", detected_by="config")
        if (cfg / "i3" / "config").exists():
            return DEInfo(name="i3", type="WM", engine="I3ThemeEngine", detected_by="config")

        # GNOME config detection (Bluefin, Silverblue, etc. when running in terminal)
        if (cfg / "gnome" / "user").exists() or (cfg / "dconf" / "user").exists():
            return DEInfo(name="GNOME", type="DE", engine="GnomeThemeEngine", detected_by="config")

        return None
