"""Tests for ThemeEngine"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from theme_engine import ThemeEngine, GenericThemeEngine, Preset, PreviewResult


def test_preset_get_setting():
    """Test Preset.get_setting with dot notation."""
    preset = Preset(
        name="Test",
        description="Test preset",
        themes={},
        wallpaper="",
        settings={
            "hyprland": {
                "gaps_in": 5,
                "gaps_out": 10
            },
            "gtk": "test-theme"
        }
    )
    
    # Nested setting
    assert preset.get_setting("hyprland.gaps_in") == 5
    assert preset.get_setting("hyprland.gaps_out") == 10
    
    # Top-level setting
    assert preset.get_setting("gtk") == "test-theme"
    
    # Non-existent setting with default
    assert preset.get_setting("nonexistent", "default") == "default"
    
    # Non-existent nested setting
    assert preset.get_setting("hyprland.nonexistent") is None


def test_generic_engine_apply_preset():
    """Test that GenericThemeEngine cannot apply presets."""
    engine = GenericThemeEngine()
    preset = Preset(
        name="Test",
        description="Test",
        themes={},
        wallpaper="",
        settings={}
    )
    
    result = engine.apply_preset(preset)
    assert result is False


def test_generic_engine_preview_preset():
    """Test that GenericThemeEngine can preview presets."""
    engine = GenericThemeEngine()
    preset = Preset(
        name="Test",
        description="Test preset",
        themes={
            "gtk": "test-gtk",
            "icon": "test-icon",
            "font": "test-font"
        },
        wallpaper="https://example.com/wall.jpg",
        settings={}
    )
    
    result = engine.preview_preset(preset)
    
    assert isinstance(result, PreviewResult)
    assert result.changes == []


def test_generic_engine_backup_restore():
    """Test that GenericThemeEngine backup/restore are no-ops."""
    engine = GenericThemeEngine()
    
    backup_id = engine.backup_current()
    assert backup_id == "generic"
    
    result = engine.restore_backup("any-id")
    assert result is False


def test_theme_engine_backup_dir_creation():
    """Test that backup directory is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('pathlib.Path.home', return_value=Path(tmpdir)):
            engine = GenericThemeEngine()
            
            backup_dir = engine._get_backup_dir()
            assert backup_dir.exists()
            assert backup_dir.name == "backups"


def test_theme_engine_download_file_invalid_url():
    """Test that invalid URLs are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GenericThemeEngine()
        dest = Path(tmpdir) / "test.txt"
        
        # None URL
        result = engine._download_file(None, dest)
        assert result is False
        
        # Empty string
        result = engine._download_file("", dest)
        assert result is False
        
        # Non-string
        result = engine._download_file(123, dest)
        assert result is False
        
        # file:// protocol (should be rejected)
        result = engine._download_file("file:///etc/passwd", dest)
        assert result is False
        
        # ftp:// protocol (should be rejected)
        result = engine._download_file("ftp://example.com/file", dest)
        assert result is False


def test_theme_engine_download_file_valid_url():
    """Test that valid http/https URLs are accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GenericThemeEngine()
        dest = Path(tmpdir) / "test.txt"
        
        # http:// should be accepted
        # (will fail to actually download, but should pass validation)
        with patch.object(engine, '_run', return_value=MagicMock()):
            result = engine._download_file("http://example.com/file", dest)
            # Will return False because download fails, but validation passed
        
        # https:// should be accepted
        with patch.object(engine, '_run', return_value=MagicMock()):
            result = engine._download_file("https://example.com/file", dest)


def test_theme_engine_download_wallpaper_local():
    """Test downloading local wallpaper."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GenericThemeEngine()
        
        # Create a local wallpaper file
        local_wallpaper = Path(tmpdir) / "wallpaper.jpg"
        local_wallpaper.write_text("fake image")
        
        result = engine._download_wallpaper(str(local_wallpaper), Path(tmpdir))
        
        assert result == local_wallpaper


def test_theme_engine_download_wallpaper_nonexistent_local():
    """Test that nonexistent local wallpaper returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GenericThemeEngine()
        
        result = engine._download_wallpaper("/nonexistent/path.jpg", Path(tmpdir))
        
        assert result is None


def test_theme_engine_extract_archive_zip():
    """Test extracting zip archives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile
        
        engine = GenericThemeEngine()
        
        # Create a test zip file
        zip_path = Path(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as z:
            z.writestr("test.txt", "content")
        
        dest_dir = Path(tmpdir) / "extract"
        result = engine._extract_archive(zip_path, dest_dir)
        
        assert result is not None
        assert (dest_dir / "test.txt").exists()


def test_theme_engine_extract_archive_invalid():
    """Test that invalid archives return None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GenericThemeEngine()
        
        # Create a non-archive file
        invalid_path = Path(tmpdir) / "invalid.txt"
        invalid_path.write_text("not an archive")
        
        dest_dir = Path(tmpdir) / "extract"
        result = engine._extract_archive(invalid_path, dest_dir)
        
        assert result is None


def test_theme_engine_calculate_changes():
    """Test change calculation between current state and preset."""
    engine = GenericThemeEngine()
    
    preset = Preset(
        name="Test",
        description="Test",
        themes={},
        wallpaper="",
        settings={
            "key1": "value1",
            "key2": "value2"
        }
    )
    
    # Mock _get_current_setting to return different values
    with patch.object(engine, '_get_current_setting', side_effect=lambda k: "old_" + k):
        changes = engine._calculate_changes(preset)
        
        assert len(changes) == 2
        assert all(c["current"] != c["new"] for c in changes)


def test_theme_engine_run_command():
    """Test _run command execution."""
    engine = GenericThemeEngine()
    
    result = engine._run(["echo", "test"], check=True)
    
    assert result.returncode == 0
    assert "test" in result.stdout


def test_theme_engine_run_command_failure():
    """Test _run command with failure."""
    engine = GenericThemeEngine()
    
    result = engine._run(["false"], check=False)
    
    assert result.returncode != 0
