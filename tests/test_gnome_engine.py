"""Tests for GnomeThemeEngine"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_gnome_engine_module_imports():
    """Test that gnome_engine module can be imported."""
    from engines import gnome_engine
    assert gnome_engine is not None


def test_gnome_engine_class_exists():
    """Test that GnomeThemeEngine class exists."""
    from engines.gnome_engine import GnomeThemeEngine
    assert GnomeThemeEngine is not None


def test_gnome_engine_has_required_methods():
    """Test that GnomeThemeEngine has required methods."""
    from engines.gnome_engine import GnomeThemeEngine
    engine = GnomeThemeEngine()
    assert hasattr(engine, 'apply_preset')
    assert hasattr(engine, 'preview_preset')
    # Check for actual methods in GnomeThemeEngine
    assert hasattr(engine, '_install_theme')
    assert hasattr(engine, '_install_icon_theme')
    assert hasattr(engine, '_install_shell_theme')
    assert hasattr(engine, '_install_extension')
    assert hasattr(engine, '_apply_wallpaper')
    assert hasattr(engine, '_gset')
    assert hasattr(engine, '_gget')
