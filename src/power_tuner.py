"""
Power Tuner
CPU / energy control via powerprofilesctl (user-space only).
"""

import subprocess
from typing import List

from hardware_monitor import HardwareMonitor


class PowerTuner:
    """Manages power profiles without root privileges."""

    def __init__(self):
        self.monitor = HardwareMonitor()

    def get_available_profiles(self) -> List[str]:
        """Return available power profiles."""
        try:
            result = subprocess.run(
                ["powerprofilesctl", "list"],
                capture_output=True, text=True, check=False
            )
            profiles = []
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("—"):
                    continue
                # Remove leading asterisk indicator
                profile = stripped.lstrip("* ").strip()
                if profile:
                    profiles.append(profile)
            return profiles
        except FileNotFoundError:
            return ["balanced", "power-saver", "performance"]

    def get_current_profile(self) -> str:
        """Return the currently active power profile."""
        try:
            result = subprocess.run(
                ["powerprofilesctl", "get"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return "balanced"

    def set_power_profile(self, profile: str) -> bool:
        """Set a power profile."""
        try:
            subprocess.run(["powerprofilesctl", "set", profile], check=True)
            print(f"[PowerTuner] Profile set: {profile}")
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            print(f"[PowerTuner] Failed to set {profile}: {e}")
            return False

    def pause_idle_containers(self, temp_threshold: float = 80.0, cpu_threshold: float = 5.0):
        """Pause idle podman containers when overheating."""
        temps = self.monitor.get_temperatures()
        if not temps or not any(t > temp_threshold for t in temps.values()):
            return
        print(f"[PowerTuner] Overheat detected: {temps}")
        for container in self.monitor.get_container_stats():
            cpu = float(container.get("cpu_percent", 0) or 0)
            if cpu < cpu_threshold:
                name = container.get("Name", "unknown")
                print(f"[PowerTuner] Pausing idle container: {name}")
                subprocess.run(["podman", "pause", name], check=False)

    def auto_tune(self):
        """Auto-select power profile based on battery and temperature."""
        battery = self.monitor.get_battery_status()
        status = battery.get("status", "").lower()
        capacity = battery.get("capacity", 100)
        temps = self.monitor.get_temperatures()

        if status == "discharging" and capacity < 20:
            self.set_power_profile("power-saver")
        elif status == "charging" and temps and temps.values() and max(temps.values()) < 70:
            self.set_power_profile("performance")
        else:
            self.set_power_profile("balanced")
