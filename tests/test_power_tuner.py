"""Tests for PowerTuner"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_tuner import PowerTuner


def test_power_tuner_get_current_profile():
    """Test getting current power profile."""
    tuner = PowerTuner()
    
    # Mock powerprofilesctl to return "performance"
    mock_result = MagicMock()
    mock_result.stdout = "performance"
    
    with patch('subprocess.run', return_value=mock_result):
        profile = tuner.get_current_profile()
        assert profile == "performance"


def test_power_tuner_get_current_profile_fallback():
    """Test fallback to balanced when powerprofilesctl fails."""
    tuner = PowerTuner()
    
    with patch('subprocess.run', side_effect=FileNotFoundError):
        profile = tuner.get_current_profile()
        assert profile == "balanced"


def test_power_tuner_set_power_profile():
    """Test setting power profile."""
    tuner = PowerTuner()
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        result = tuner.set_power_profile("performance")
        assert result is True


def test_power_tuner_set_power_profile_failure():
    """Test handling of profile set failure."""
    tuner = PowerTuner()
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    
    with patch('subprocess.run', return_value=mock_result):
        result = tuner.set_power_profile("performance")
        assert result is False


def test_power_tuner_pause_idle_containers():
    """Test pausing idle containers."""
    tuner = PowerTuner()
    
    # Mock hardware monitor to show low CPU usage
    with patch.object(tuner, '_get_container_cpu_usage', return_value=5.0):
        with patch('subprocess.run', return_value=MagicMock(returncode=0)) as mock_run:
            tuner.pause_idle_containers(threshold=10.0)
            # Should have called podman pause
            assert any('pause' in str(call) for call in mock_run.call_args_list)


def test_power_tuner_get_container_cpu_usage():
    """Test getting container CPU usage."""
    tuner = PowerTuner()
    
    mock_result = MagicMock()
    mock_result.stdout = "CONTAINER   CPU %\ntest_container 15.5"
    
    with patch('subprocess.run', return_value=mock_result):
        usage = tuner._get_container_cpu_usage("test_container")
        assert usage == 15.5


def test_power_tuner_get_container_cpu_usage_not_found():
    """Test handling when container not found in stats."""
    tuner = PowerTuner()
    
    mock_result = MagicMock()
    mock_result.stdout = "CONTAINER   CPU %\nother_container 10.0"
    
    with patch('subprocess.run', return_value=mock_result):
        usage = tuner._get_container_cpu_usage("test_container")
        assert usage == 0.0


def test_power_tuner_optimize_power():
    """Test power optimization based on battery status."""
    tuner = PowerTuner()
    
    # Mock battery at low capacity
    with patch.object(tuner.hw_monitor, 'get_battery_status', return_value={"capacity": 20, "status": "Discharging"}):
        with patch.object(tuner, 'set_power_profile') as mock_set:
            tuner.optimize_power()
            # Should switch to power-saver
            mock_set.assert_called_with("power-saver")


def test_power_tuner_optimize_power_charging():
    """Test power optimization when charging."""
    tuner = PowerTuner()
    
    # Mock battery charging
    with patch.object(tuner.hw_monitor, 'get_battery_status', return_value={"capacity": 50, "status": "Charging"}):
        with patch.object(tuner, 'set_power_profile') as mock_set:
            tuner.optimize_power()
            # Should switch to performance when charging
            mock_set.assert_called_with("performance")
