#!/usr/bin/env python3
"""
Linux Tweaker - Rice & Optimize Tool
Modular theming and tuning for immutable Linux systems.
"""

import sys
from pathlib import Path

# Ensure src/ is importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent / "src"))

from de_detector import DEDetector
from ui.main_menu import MainMenu


def main():
    """Main entry point."""
    print("🚀 Linux Tweaker v0.1.0")
    print("Rice & Optimize for Immutable OS\n")

    detector = DEDetector()
    de_info = detector.detect()

    print(f"Detected environment: {de_info.name} ({de_info.type})")
    print(f"Engine: {de_info.engine}\n")

    menu = MainMenu(de_info)
    menu.run()


if __name__ == "__main__":
    main()
