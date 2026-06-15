"""Tests for UI main_menu module"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_main_menu_module_imports():
    """Test that main_menu module can be imported."""
    from ui import main_menu
    assert main_menu is not None


def test_main_menu_class_exists():
    """Test that MainMenu class exists."""
    from ui.main_menu import MainMenu
    assert MainMenu is not None
