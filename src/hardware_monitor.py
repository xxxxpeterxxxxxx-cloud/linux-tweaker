"""
Hardware Monitor
Read-only monitoring of temperatures, battery, and containers.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any


class HardwareMonitor:
    """Reads hardware sensors without root privileges."""

    def __init__(self):
        self.sys_root = Path("/sys")
    
    def get_temperatures(self) -> Dict[str, float]:
        """Read temperatures from /sys/class/hwmon/ in Celsius."""
        temps = {}
        hwmon_path = self.sys_root / "class" / "hwmon"
        if not hwmon_path.exists():
            return temps

        for hwmon in hwmon_path.glob("hwmon*"):
            try:
                name_file = hwmon / "name"
                if not name_file.exists():
                    continue
                name = name_file.read_text().strip()
                temp_inputs = list(hwmon.glob("temp*_input"))
                if not temp_inputs:
                    continue
                temp_millicelsius = int(temp_inputs[0].read_text().strip())
                temps[name] = round(temp_millicelsius / 1000.0, 1)
            except (FileNotFoundError, ValueError):
                continue
        return temps
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Read battery status from /sys/class/power_supply/BAT0/."""
        battery_path = self.sys_root / "class" / "power_supply" / "BAT0"
        if not battery_path.exists():
            return {"error": "no battery"}

        try:
            capacity = int((battery_path / "capacity").read_text().strip())
            status = (battery_path / "status").read_text().strip()
            energy_now = int((battery_path / "energy_now").read_text().strip()) / 1_000_000
            energy_full = int((battery_path / "energy_full").read_text().strip()) / 1_000_000
            return {
                "capacity": capacity,
                "status": status,
                "energy_now_wh": round(energy_now, 2),
                "energy_full_wh": round(energy_full, 2),
                "percentage": capacity,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_container_stats(self) -> List[Dict]:
        """Read container stats via podman stats."""
        try:
            result = subprocess.run(
                ["podman", "stats", "--no-stream", "--format", "json"],
                capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                return []
            return json.loads(result.stdout)
        except Exception:
            return []
    
    def get_zram_stats(self) -> Dict[str, float]:
        """Read zRAM statistics."""
        zram_path = self.sys_root / "block" / "zram0"
        if not zram_path.exists():
            return {"error": "zram0 not found"}

        try:
            disksize = int((zram_path / "disksize").read_text().strip()) / (1024**3)
            mm_stat = (zram_path / "mm_stat").read_text().strip().split()
            used_bytes = int(mm_stat[3]) if len(mm_stat) > 3 else 0
            used_gb = used_bytes / (1024**3)
            return {
                "total_gb": round(disksize, 2),
                "used_gb": round(used_gb, 2),
                "usage_percent": round((used_gb / disksize) * 100, 1) if disksize > 0 else 0,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Return all hardware stats in one dict."""
        return {
            "temperatures": self.get_temperatures(),
            "battery": self.get_battery_status(),
            "containers": self.get_container_stats(),
            "zram": self.get_zram_stats(),
        }
