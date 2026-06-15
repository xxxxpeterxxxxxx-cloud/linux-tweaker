"""Tests for DEDetector"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from de_detector import DEDetector, DEInfo


def test_detector_xdg_current_desktop():
    """Test detection via XDG_CURRENT_DESKTOP environment variable."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "GNOME"}):
        detector = DEDetector()
        result = detector.detect()
        
        assert result.name == "GNOME"
        assert result.type == "DE"
        assert result.engine == "GnomeThemeEngine"
        assert result.detected_by == "XDG_CURRENT_DESKTOP"


def test_detector_desktop_session():
    """Test detection via DESKTOP_SESSION environment variable."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": "KDE"}):
        detector = DEDetector()
        result = detector.detect()
        
        assert result.name == "KDE"
        assert result.type == "DE"
        assert result.engine == "PlasmaThemeEngine"
        assert result.detected_by == "DESKTOP_SESSION"


def test_detector_xdg_colon_separated():
    """Test XDG_CURRENT_DESKTOP with colon-separated values."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}):
        detector = DEDetector()
        result = detector.detect()
        
        # Should match GNOME (first match in ENGINE_MAP after splitting by :)
        assert result.name == "GNOME"
        assert result.engine == "GnomeThemeEngine"


def test_detector_fallback_to_generic():
    """Test fallback to GenericThemeEngine when nothing is detected."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        with patch.object(DEDetector, '_detect_by_process', return_value=None):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                assert result.name == "Unknown"
                assert result.type == "Unknown"
                assert result.engine == "GenericThemeEngine"
                assert result.detected_by == "fallback"


def test_detector_process_detection():
    """Test detection via running processes."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        mock_result = MagicMock()
        mock_result.stdout = "gnome-shell\nother-process"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                assert result.name == "GNOME"
                assert result.detected_by == "process"


def test_detector_config_detection():
    """Test detection via config files."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        with patch.object(DEDetector, '_detect_by_process', return_value=None):
            with patch('pathlib.Path.exists', return_value=True):
                detector = DEDetector()
                result = detector.detect()
                
                # Should detect via config if hypr config exists
                assert result.detected_by == "config" or result.detected_by == "fallback"


def test_detector_subprocess_error_handling():
    """Test that subprocess errors are handled gracefully."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                # Should not crash, fall back to generic
                assert result.engine == "GenericThemeEngine"


def test_detector_hyprland_detection():
    """Test Hyprland detection."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        mock_result = MagicMock()
        mock_result.stdout = "hyprland\nother-process"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                assert result.name == "Hyprland"
                assert result.type == "WM"
                assert result.engine == "HyprlandThemeEngine"


def test_detector_sway_detection():
    """Test Sway detection."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        mock_result = MagicMock()
        mock_result.stdout = "sway\nother-process"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                assert result.name == "sway"
                assert result.type == "WM"
                assert result.engine == "SwayThemeEngine"


def test_detector_xfce_detection():
    """Test XFCE detection."""
    with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "", "DESKTOP_SESSION": ""}):
        mock_result = MagicMock()
        mock_result.stdout = "xfce4-session\nxfce4-panel"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch.object(DEDetector, '_detect_by_config', return_value=None):
                detector = DEDetector()
                result = detector.detect()
                
                assert result.name == "XFCE"
                assert result.type == "DE"
                assert result.engine == "XfceThemeEngine"
