#!/usr/bin/env python3
"""
Linux Tweaker - Rice & Optimize Tool
Modular theming and tuning for immutable Linux systems.
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure src/ is importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent / "src"))

from version import __version__
from de_detector import DEDetector, DEInfo
from engines import (
    GenericThemeEngine, GnomeThemeEngine, PlasmaThemeEngine,
    XfceThemeEngine, HyprlandThemeEngine, SwayThemeEngine,
    I3ThemeEngine, BspwmThemeEngine, LxqtThemeEngine, MateThemeEngine,
)
from hardware_monitor import HardwareMonitor
from power_tuner import PowerTuner
from preset_manager import PresetManager
from ui.main_menu import MainMenu

# Map detected engine names to actual classes
ENGINE_MAP = {
    "GnomeThemeEngine": GnomeThemeEngine,
    "PlasmaThemeEngine": PlasmaThemeEngine,
    "XfceThemeEngine": XfceThemeEngine,
    "HyprlandThemeEngine": HyprlandThemeEngine,
    "SwayThemeEngine": SwayThemeEngine,
    "I3ThemeEngine": I3ThemeEngine,
    "BspwmThemeEngine": BspwmThemeEngine,
    "LxqtThemeEngine": LxqtThemeEngine,
    "MateThemeEngine": MateThemeEngine,
}


def list_presets(manager: PresetManager):
    """List all available presets."""
    presets = manager.list_presets()
    if not presets:
        print("No presets found.")
        return 1
    print(f"\n{'NAME':<20} {'DESCRIPTION':<40}")
    print("-" * 60)
    for p in presets:
        print(f"{p.name:<20} {p.description:<40}")
    return 0


def apply_preset(manager: PresetManager, preset_name: str, de_info):
    """Apply a preset by name."""
    presets = manager.list_presets()
    preset = next((p for p in presets if p.name.lower() == preset_name.lower()), None)
    if not preset:
        print(f"Error: Preset '{preset_name}' not found.")
        print("Run with --list to see available presets.")
        return 1

    # Get the right engine
    engine_class = ENGINE_MAP.get(de_info.engine, GenericThemeEngine)
    engine = engine_class()

    print(f"Applying preset: {preset.name}")
    engine.preview_preset(preset)
    success = engine.apply_preset(preset)
    if success:
        print(f"\nPreset '{preset.name}' applied successfully!")
        return 0
    else:
        print(f"\nFailed to apply preset '{preset.name}'.")
        return 1


def show_monitoring():
    """Show hardware monitoring stats."""
    monitor = HardwareMonitor()
    stats = monitor.get_all_stats()

    print("\n=== Hardware Monitoring ===")
    if stats.get("temperatures"):
        print("\nTemperatures:")
        for name, temp in stats["temperatures"].items():
            print(f"  {name}: {temp}°C")

    if stats.get("battery"):
        bat = stats["battery"]
        print(f"\nBattery: {bat.get('capacity', '?')}% ({bat.get('status', 'unknown')})")

    if stats.get("zram"):
        zram = stats["zram"]
        print(f"\nzRAM: {zram.get('usage_percent', '?')}% used")

    if stats.get("containers"):
        print(f"\nContainers: {len(stats['containers'])} running")
    return 0


def do_power_tune():
    """Auto-tune power profile."""
    tuner = PowerTuner()
    tuner.auto_tune()
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=f"Linux Tweaker v{__version__} - Rice & Optimize Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Launch interactive menu
  %(prog)s --list                   List all presets
  %(prog)s --apply "Blue Dream"     Apply a preset
  %(prog)s --preview "Blue Dream"   Preview a preset
  %(prog)s --restore <backup-id>   Restore a backup
  %(prog)s --monitor                Show hardware stats
  %(prog)s --tune                   Auto-tune power profile
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--list", action="store_true", help="List available presets")
    parser.add_argument("--apply", metavar="PRESET", help="Apply a preset by name")
    parser.add_argument("--preview", metavar="PRESET", help="Preview a preset")
    parser.add_argument("--restore", metavar="BACKUP_ID", help="Restore a backup by ID (use 'latest' for most recent)")
    parser.add_argument("--monitor", action="store_true", help="Show hardware monitoring")
    parser.add_argument("--tune", action="store_true", help="Auto-tune power profile")
    parser.add_argument("--force-de", metavar="DE", help="Force DE engine (gnome, plasma, xfce, hyprland, sway, i3, bspwm, lxqt, mate)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Handle restore first (DE-agnostic)
    if args.restore:
        from engines import HyprlandThemeEngine
        engine = HyprlandThemeEngine()  # Any engine works for restore
        backup_id = args.restore
        if backup_id.lower() == "latest":
            backups = sorted((engine.backup_dir).glob("backup_*"))
            if not backups:
                print("No backups found.")
                return 1
            backup_id = backups[-1].name.replace("backup_", "")
        success = engine.restore_backup(backup_id)
        return 0 if success else 1

    # Detect DE or use forced DE
    detector = DEDetector()
    try:
        if args.force_de:
            forced = args.force_de.lower()
            engine_map_cli = {
                "gnome": "GnomeThemeEngine",
                "plasma": "PlasmaThemeEngine",
                "kde": "PlasmaThemeEngine",
                "xfce": "XfceThemeEngine",
                "hyprland": "HyprlandThemeEngine",
                "sway": "SwayThemeEngine",
                "i3": "I3ThemeEngine",
                "bspwm": "BspwmThemeEngine",
                "lxqt": "LxqtThemeEngine",
                "mate": "MateThemeEngine",
            }
            engine_name = engine_map_cli.get(forced)
            if engine_name:
                de_info = DEInfo(name=forced.title(), type="DE", engine=engine_name, detected_by="--force-de")
            else:
                print(f"Error: Unknown DE '{forced}'. Valid: {', '.join(engine_map_cli.keys())}")
                return 1
        else:
            de_info = detector.detect()
    except Exception as e:
        logging.error(f"DE detection failed: {e}")
        de_info = DEInfo(name="Unknown", type="Unknown", engine="GenericThemeEngine", detected_by="fallback")

    manager = PresetManager()

    # Handle CLI args
    if args.list:
        return list_presets(manager)
    elif args.apply:
        return apply_preset(manager, args.apply, de_info)
    elif args.preview:
        presets = manager.list_presets()
        preset = next((p for p in presets if p.name.lower() == args.preview.lower()), None)
        if not preset:
            print(f"Error: Preset '{args.preview}' not found.")
            return 1
        engine_class = ENGINE_MAP.get(de_info.engine, GenericThemeEngine)
        engine = engine_class()
        engine.preview_preset(preset)
        return 0
    elif args.monitor:
        return show_monitoring()
    elif args.tune:
        return do_power_tune()

    # Interactive mode
    print(f"Linux Tweaker v{__version__}")
    print("Rice & Optimize for Immutable OS\n")
    print(f"Detected environment: {de_info.name} ({de_info.type})")
    print(f"Engine: {de_info.engine}\n")
    menu = MainMenu(de_info)
    menu.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
