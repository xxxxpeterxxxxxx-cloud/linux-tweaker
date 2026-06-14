"""Tests for PresetManager"""

import json
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from preset_manager import PresetManager
from theme_engine import Preset


def test_preset_manager_loads_valid_json():
    """Test that valid JSON preset files are loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_dir = Path(tmpdir)
        preset_file = preset_dir / "test_preset.json"
        
        preset_data = {
            "name": "Test Preset",
            "description": "A test preset",
            "themes": {"gtk": "test-theme"},
            "wallpaper": "https://example.com/wallpaper.jpg",
            "settings": {}
        }
        
        preset_file.write_text(json.dumps(preset_data))
        
        manager = PresetManager(str(preset_dir))
        
        assert len(manager.presets) == 1
        assert "test preset" in manager.presets
        assert manager.presets["test preset"].name == "Test Preset"
        assert manager.presets["test preset"].description == "A test preset"


def test_preset_manager_handles_malformed_json():
    """Test that malformed JSON files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_dir = Path(tmpdir)
        preset_file = preset_dir / "bad_preset.json"
        
        preset_file.write_text("{ invalid json }")
        
        manager = PresetManager(str(preset_dir))
        
        # Should not crash, just skip the bad file
        assert len(manager.presets) == 0


def test_preset_manager_handles_missing_required_field():
    """Test that presets missing required fields are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_dir = Path(tmpdir)
        preset_file = preset_dir / "incomplete_preset.json"
        
        preset_data = {
            "description": "Missing name field"
        }
        
        preset_file.write_text(json.dumps(preset_data))
        
        manager = PresetManager(str(preset_dir))
        
        # Should skip the incomplete preset
        assert len(manager.presets) == 0


def test_preset_manager_get_preset():
    """Test retrieving a preset by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_dir = Path(tmpdir)
        preset_file = preset_dir / "test_preset.json"
        
        preset_data = {
            "name": "Test Preset",
            "description": "A test preset",
            "themes": {},
            "wallpaper": "",
            "settings": {}
        }
        
        preset_file.write_text(json.dumps(preset_data))
        
        manager = PresetManager(str(preset_dir))
        
        preset = manager.get_preset("test preset")
        assert preset is not None
        assert preset.name == "Test Preset"
        
        # Case insensitive
        preset_upper = manager.get_preset("TEST PRESET")
        assert preset_upper is not None
        
        # Non-existent preset
        none_preset = manager.get_preset("nonexistent")
        assert none_preset is None


def test_preset_manager_search_presets():
    """Test searching presets by query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_dir = Path(tmpdir)
        
        preset1 = preset_dir / "dark_preset.json"
        preset1.write_text(json.dumps({
            "name": "Dark Theme",
            "description": "A dark theme preset",
            "themes": {},
            "wallpaper": "",
            "settings": {}
        }))
        
        preset2 = preset_dir / "light_preset.json"
        preset2.write_text(json.dumps({
            "name": "Light Theme",
            "description": "A light theme preset",
            "themes": {},
            "wallpaper": "",
            "settings": {}
        }))
        
        manager = PresetManager(str(preset_dir))
        
        # Search by name
        results = manager.search_presets("dark")
        assert len(results) == 1
        assert results[0].name == "Dark Theme"
        
        # Search by description
        results = manager.search_presets("light")
        assert len(results) == 1
        assert results[0].name == "Light Theme"
        
        # Search with no results
        results = manager.search_presets("nonexistent")
        assert len(results) == 0


def test_preset_manager_handles_empty_directory():
    """Test that empty preset directory is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PresetManager(str(tmpdir))
        
        assert len(manager.presets) == 0
        assert manager.list_presets() == []


def test_preset_manager_handles_nonexistent_directory():
    """Test that nonexistent preset directory is handled gracefully."""
    manager = PresetManager("/nonexistent/path")
    
    # Should not crash, just have no presets
    assert len(manager.presets) == 0
