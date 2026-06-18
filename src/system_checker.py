"""
SystemChecker - Validates system environment and dependencies.

This module provides robust system checking capabilities with zero-crash policy.
All operations are wrapped in try/except blocks to ensure graceful error handling.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


class WindowManager(Enum):
    """Supported window managers/compositors."""
    HYPRLAND = "Hyprland"
    SWAY = "Sway"
    I3 = "i3"
    GNOME = "GNOME"
    KDE = "KDE Plasma"
    XFCE = "XFCE"
    UNKNOWN = "Unknown"


class DependencyStatus(Enum):
    """Dependency check status."""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


class SystemChecker:
    """
    Validates system environment for the ricing manager.
    
    Checks:
    - Write permissions in user home directory
    - Running window manager/compositor
    - Critical dependencies (git, python3, ags, etc.)
    """
    
    def __init__(self):
        """Initialize SystemChecker."""
        self.home_dir = Path.home()
        self._write_permission: Optional[bool] = None
        self._window_manager: Optional[WindowManager] = None
        self._dependencies: Dict[str, DependencyStatus] = {}
        self._errors: List[str] = []
        self._dependency_cache: Dict[str, DependencyStatus] = {}  # Cache for dependency checks
    
    def check_write_permissions(self) -> bool:
        """
        Check if script has write permissions in user home directory.
        
        Returns:
            bool: True if write permissions are available, False otherwise.
        """
        try:
            # Try to create a temporary file in home directory
            test_file = self.home_dir / ".linux_tweaker_write_test"
            try:
                test_file.touch()
                test_file.unlink()
                self._write_permission = True
                return True
            except (PermissionError, OSError) as e:
                self._errors.append(f"Write permission check failed: {e}")
                self._write_permission = False
                return False
        except Exception as e:
            self._errors.append(f"Unexpected error during write permission check: {e}")
            self._write_permission = False
            return False
    
    def detect_window_manager(self) -> WindowManager:
        """
        Detect the currently running window manager/compositor.
        
        Returns:
            WindowManager: Detected window manager.
        """
        try:
            # Check environment variables first
            xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
            display = os.environ.get("DISPLAY", "")
            
            # Check for Hyprland
            if "hyprland" in xdg_current_desktop:
                try:
                    result = subprocess.run(
                        ["hyprctl", "version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self._window_manager = WindowManager.HYPRLAND
                        return WindowManager.HYPRLAND
                except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
            
            # Check for Sway
            if "sway" in xdg_current_desktop:
                try:
                    result = subprocess.run(
                        ["sway", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self._window_manager = WindowManager.SWAY
                        return WindowManager.SWAY
                except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
            
            # Check for i3
            if "i3" in xdg_current_desktop:
                try:
                    result = subprocess.run(
                        ["i3", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self._window_manager = WindowManager.I3
                        return WindowManager.I3
                except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
            
            # Check for GNOME
            if "gnome" in xdg_current_desktop:
                self._window_manager = WindowManager.GNOME
                return WindowManager.GNOME
            
            # Check for KDE
            if "kde" in xdg_current_desktop or "plasma" in xdg_current_desktop:
                self._window_manager = WindowManager.KDE
                return WindowManager.KDE
            
            # Check for XFCE
            if "xfce" in xdg_current_desktop:
                self._window_manager = WindowManager.XFCE
                return WindowManager.XFCE
            
            # Fallback to unknown
            self._window_manager = WindowManager.UNKNOWN
            return WindowManager.UNKNOWN
            
        except Exception as e:
            self._errors.append(f"Error detecting window manager: {e}")
            self._window_manager = WindowManager.UNKNOWN
            return WindowManager.UNKNOWN
    
    def check_dependency(self, command: str) -> DependencyStatus:
        """
        Check if a dependency is installed without trying to install it.
        
        Args:
            command: Command to check (e.g., "git", "python3", "ags").
            
        Returns:
            DependencyStatus: Status of the dependency.
        """
        # Check cache first
        if command in self._dependency_cache:
            self._dependencies[command] = self._dependency_cache[command]
            return self._dependency_cache[command]
        
        try:
            # Try using shutil.which first (more reliable)
            import shutil
            if shutil.which(command):
                status = DependencyStatus.INSTALLED
                self._dependency_cache[command] = status
                self._dependencies[command] = status
                return status
            
            # Fallback to which command
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                status = DependencyStatus.INSTALLED
            else:
                status = DependencyStatus.NOT_INSTALLED
            
            self._dependency_cache[command] = status
            self._dependencies[command] = status
            return status
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self._errors.append(f"Error checking dependency '{command}': {e}")
            self._dependencies[command] = DependencyStatus.ERROR
            return DependencyStatus.ERROR
        except Exception as e:
            self._errors.append(f"Unexpected error checking dependency '{command}': {e}")
            self._dependencies[command] = DependencyStatus.ERROR
            return DependencyStatus.ERROR
    
    def check_critical_dependencies(self) -> Dict[str, DependencyStatus]:
        """
        Check all critical dependencies.
        
        Returns:
            Dict[str, DependencyStatus]: Dictionary of dependency statuses.
        """
        critical_deps = ["git", "python3", "ags", "rofi", "waybar"]
        
        for dep in critical_deps:
            self.check_dependency(dep)
        
        return self._dependencies
    
    def get_errors(self) -> List[str]:
        """
        Get all errors encountered during checks.
        
        Returns:
            List[str]: List of error messages.
        """
        return self._errors.copy()
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get a summary of all system checks.
        
        Returns:
            Dict[str, any]: Summary of all checks.
        """
        return {
            "write_permission": self._write_permission,
            "window_manager": self._window_manager.value if self._window_manager else "Not checked",
            "dependencies": {k: v.value for k, v in self._dependencies.items()},
            "errors": self._errors
        }
