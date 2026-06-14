"""Theme Engines for different DEs/WMs"""

from theme_engine import GenericThemeEngine
from .gnome_engine import GnomeThemeEngine
from .plasma_engine import PlasmaThemeEngine
from .hyprland_engine import HyprlandThemeEngine
from .xfce_engine import XfceThemeEngine

# Aliases for WMs that share similar theming approaches
SwayThemeEngine = HyprlandThemeEngine
I3ThemeEngine = HyprlandThemeEngine
BspwmThemeEngine = HyprlandThemeEngine
LxqtThemeEngine = XfceThemeEngine
MateThemeEngine = XfceThemeEngine

__all__ = [
    "GnomeThemeEngine",
    "PlasmaThemeEngine",
    "HyprlandThemeEngine",
    "XfceThemeEngine",
    "GenericThemeEngine",
    "SwayThemeEngine",
    "I3ThemeEngine",
    "BspwmThemeEngine",
    "LxqtThemeEngine",
    "MateThemeEngine",
]
