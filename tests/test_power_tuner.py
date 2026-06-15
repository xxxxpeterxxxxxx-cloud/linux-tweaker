"""Tests for PowerTuner"""

import pytest
import subprocess
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
    
    with patch('subprocess.run', side_effect=subprocess.SubprocessError("Failed")):
        result = tuner.set_power_profile("performance")
        assert result is False


def test_power_tuner_pause_idle_containers():
    """Test pausing idle containers."""
    tuner = PowerTuner()
    
    # Mock hardware monitor to show high temp and low CPU usage
    with patch.object(tuner.monitor, 'get_temperatures', return_value={'cpu': 90.0}):
        with patch.object(tuner.monitor, 'get_container_stats', return_value=[{'Name': 'test_container', 'cpu_percent': 2.0}]):
            with patch('subprocess.run', return_value=MagicMock(returncode=0)) as mock_run:
                tuner.pause_idle_containers()
                # Should have called podman pause
                assert any('pause' in str(call) for call in mock_run.call_args_list)


def test_power_tuner_get_container_stats():
    """Test getting container stats from hardware monitor."""
    tuner = PowerTuner()
    
    with patch.object(tuner.monitor, 'get_container_stats', return_value=[{'Name': 'test_container', 'cpu_percent': 15.5}]):
        stats = tuner.monitor.get_container_stats()
        assert len(stats) == 1
        assert stats[0]['Name'] == 'test_container'
        assert stats[0]['cpu_percent'] == 15.5


def test_power_tuner_optimize_power():
    """Test power optimization based on battery status."""
    tuner = PowerTuner()
    
    # Mock battery at low capacity (must be < 20 to trigger power-saver)
    with patch.object(tuner.monitor, 'get_battery_status', return_value={"capacity": 15, "status": "Discharging"}):
        with patch.object(tuner, 'set_power_profile') as mock_set:
            tuner.auto_tune()
            # Should switch to power-saver
            mock_set.assert_called_with("power-saver")


def test_power_tuner_optimize_power_charging():
    """Test power optimization when charging."""
    tuner = PowerTuner()
    
    # Mock battery charging
    with patch.object(tuner.monitor, 'get_battery_status', return_value={"capacity": 50, "status": "Charging"}):
        with patch.object(tuner.monitor, 'get_temperatures', return_value={'cpu': 60.0}):
            with patch.object(tuner, 'set_power_profile') as mock_set:
                tuner.auto_tune()
                # Should switch to performance when charging
                mock_set.assert_called_with("performance")
