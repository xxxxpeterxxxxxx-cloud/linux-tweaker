"""
Preset Manager
Loads, saves, and manages visual theme presets.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from theme_engine import Preset


class PresetManager:
    """Manages theme presets from a JSON directory."""

    def __init__(self, preset_dir: Optional[str] = None):
        if preset_dir:
            self.preset_dir = Path(preset_dir)
        else:
            # Support running from repo root or from src/
            candidates = [
                Path(__file__).parent.parent / "presets",
                Path.cwd() / "presets",
                Path(__file__).parent.parent.parent / "presets",
            ]
            self.preset_dir = next((p for p in candidates if p.exists()), candidates[0] if candidates else Path.cwd() / "presets")

        self.presets: Dict[str, Preset] = {}
        self._load_presets()

    def _load_presets(self):
        if not self.preset_dir.exists():
            print(f"[PresetManager] Preset directory not found: {self.preset_dir}")
            return

        preset_files = sorted(self.preset_dir.glob("*.json"))
        if not preset_files:
            print(f"[PresetManager] No preset files found in {self.preset_dir}")
            return

        # Load preset files in parallel for better performance
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self._load_preset_file, pf): pf for pf in preset_files}
            for future in futures:
                preset_file = futures[future]
                try:
                    preset = future.result()
                    if preset:
                        self.presets[preset.name.lower()] = preset
                except (json.JSONDecodeError, KeyError, TypeError, OSError) as e:
                    print(f"[PresetManager] Error loading {preset_file.name}: {e}")

        print(f"[PresetManager] {len(self.presets)} preset(s) loaded from {self.preset_dir}")

    def _load_preset_file(self, path: Path) -> Optional[Preset]:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, IOError) as e:
            print(f"[PresetManager] Failed to parse {path.name}: {e}")
            return None
        return Preset(
            name=data["name"],
            description=data.get("description", ""),
            themes=data.get("themes", {}),
            wallpaper=data.get("wallpaper", ""),
            settings=data.get("settings", {}),
        )

    def get_preset(self, name: str) -> Optional[Preset]:
        return self.presets.get(name.lower())

    def list_presets(self) -> List[Preset]:
        return list(self.presets.values())

    def search_presets(self, query: str) -> List[Preset]:
        q = query.lower()
        return [
            p for p in self.presets.values()
            if q in p.name.lower() or q in p.description.lower()
        ]
