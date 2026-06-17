"""
PackageManager - Handles application installation in user space.

This module provides robust package management with zero-crash policy.
All operations are wrapped in try/except blocks to ensure graceful error handling.
Supports Flatpak (user-space) and other user-space installation methods.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum


class PackageType(Enum):
    """Package types supported."""
    FLATPAK = "flatpak"
    APPIMAGE = "appimage"
    LOCAL = "local"


class InstallStatus(Enum):
    """Installation status."""
    SUCCESS = "success"
    FAILED = "failed"
    ALREADY_INSTALLED = "already_installed"
    ERROR = "error"


class PackageManager:
    """
    Manages application installation in user space.
    
    Features:
    - Flatpak user-space installation (no sudo)
    - AppImage management
    - Local binary installation
    - Dependency checking
    - Zero-crash policy
    """
    
    def __init__(self):
        """Initialize PackageManager."""
        self._errors: List[str] = []
        self._installed_packages: Dict[str, bool] = {}
        self._check_flatpak_available()
    
    def _check_flatpak_available(self) -> bool:
        """
        Check if Flatpak is available.
        
        Returns:
            bool: True if Flatpak is available.
        """
        try:
            import shutil
            return shutil.which("flatpak") is not None
        except Exception:
            return False
    
    def install_flatpak(self, app_id: str, user: bool = True) -> InstallStatus:
        """
        Install a Flatpak application in user space.
        
        Args:
            app_id: Flatpak app ID (e.g., "org.gimp.GIMP").
            user: Install in user space (default: True).
            
        Returns:
            InstallStatus: Status of the installation.
        """
        try:
            # Check if already installed
            if self.is_flatpak_installed(app_id):
                self._installed_packages[app_id] = True
                return InstallStatus.ALREADY_INSTALLED
            
            # Build command
            cmd = ["flatpak", "install"]
            if user:
                cmd.append("--user")
            cmd.extend(["-y", app_id])
            
            # Run installation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self._installed_packages[app_id] = True
                return InstallStatus.SUCCESS
            else:
                self._errors.append(f"Flatpak install failed for {app_id}: {result.stderr}")
                return InstallStatus.FAILED
                
        except subprocess.TimeoutExpired:
            self._errors.append(f"Flatpak install timed out for {app_id}")
            return InstallStatus.FAILED
        except Exception as e:
            self._errors.append(f"Error installing Flatpak {app_id}: {e}")
            return InstallStatus.ERROR
    
    def is_flatpak_installed(self, app_id: str) -> bool:
        """
        Check if a Flatpak app is installed.
        
        Args:
            app_id: Flatpak app ID.
            
        Returns:
            bool: True if installed.
        """
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return app_id in result.stdout
            
            return False
            
        except Exception as e:
            self._errors.append(f"Error checking Flatpak installation {app_id}: {e}")
            return False
    
    def install_flatpak_batch(self, app_ids: List[str]) -> Dict[str, InstallStatus]:
        """
        Install multiple Flatpak applications.
        
        Args:
            app_ids: List of Flatpak app IDs.
            
        Returns:
            Dict[str, InstallStatus]: Dictionary of installation statuses.
        """
        results = {}
        
        for app_id in app_ids:
            status = self.install_flatpak(app_id)
            results[app_id] = status
        
        return results
    
    def install_appimage(self, url: str, install_dir: Optional[Path] = None) -> InstallStatus:
        """
        Download and install an AppImage.
        
        Args:
            url: URL to download AppImage from.
            install_dir: Directory to install to (default: ~/.local/bin).
            
        Returns:
            InstallStatus: Status of the installation.
        """
        try:
            import shutil
            
            # Set default install directory
            if install_dir is None:
                install_dir = Path.home() / ".local" / "bin"
            
            install_dir = Path(install_dir)
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Download AppImage
            filename = url.split("/")[-1]
            appimage_path = install_dir / filename
            
            # Use curl to download
            result = subprocess.run(
                ["curl", "-L", "-o", str(appimage_path), url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                self._errors.append(f"Failed to download AppImage from {url}")
                return InstallStatus.FAILED
            
            # Make executable
            appimage_path.chmod(0o755)
            
            return InstallStatus.SUCCESS
            
        except Exception as e:
            self._errors.append(f"Error installing AppImage from {url}: {e}")
            return InstallStatus.ERROR
    
    def install_local_binary(self, source: Path, dest: Optional[Path] = None) -> InstallStatus:
        """
        Install a local binary to user bin directory.
        
        Args:
            source: Path to source binary.
            dest: Destination path (default: ~/.local/bin/filename).
            
        Returns:
            InstallStatus: Status of the installation.
        """
        try:
            import shutil
            
            source = Path(source)
            
            if not source.exists():
                self._errors.append(f"Source binary not found: {source}")
                return InstallStatus.FAILED
            
            # Set default destination
            if dest is None:
                bin_dir = Path.home() / ".local" / "bin"
                bin_dir.mkdir(parents=True, exist_ok=True)
                dest = bin_dir / source.name
            
            dest = Path(dest)
            
            # Copy binary
            shutil.copy2(source, dest)
            dest.chmod(0o755)
            
            return InstallStatus.SUCCESS
            
        except Exception as e:
            self._errors.append(f"Error installing local binary {source}: {e}")
            return InstallStatus.ERROR
    
    def get_recommended_apps(self) -> Dict[str, List[str]]:
        """
        Get recommended applications for a GNOME-quality Hyprland setup.
        
        Returns:
            Dict[str, List[str]]: Dictionary of app categories and their Flatpak IDs.
        """
        return {
            "browsers": [
                "org.mozilla.firefox",
                "org.chromium.Chromium"
            ],
            "terminal": [
                "com.github.ameersaleh.Galculator"
            ],
            "media": [
                "org.gimp.GIMP",
                "org.inkscape.Inkscape",
                "org.blender.Blender",
                "org.kde.kdenlive",
                "io.github.mpv.Mpv"
            ],
            "communication": [
                "org.signal.Signal",
                "discord",
                "org.telegram.desktop"
            ],
            "productivity": [
                "org.libreoffice.LibreOffice",
                "org.gnome.World",
                "org.gnome.Evolution"
            ],
            "utilities": [
                "com.github.xournalpp.xournalpp",
                "org.gnome.FontManager",
                "org.gnome.DejaDup"
            ],
            "hyprland_essentials": [
                "org.freedesktop.Platform.VulkanLayer",
                "org.freedesktop.Platform.GL.default"
            ]
        }
    
    def install_essential_hyprland_apps(self) -> Dict[str, InstallStatus]:
        """
        Install essential applications for a GNOME-quality Hyprland setup.
        
        Returns:
            Dict[str, InstallStatus]: Installation results.
        """
        essential_apps = [
            "org.mozilla.firefox",
            "org.gnome.World",
            "org.libreoffice.LibreOffice",
            "discord",
            "org.telegram.desktop",
            "io.github.mpv.Mpv"
        ]
        
        return self.install_flatpak_batch(essential_apps)
    
    def get_errors(self) -> List[str]:
        """
        Get all errors encountered during operations.
        
        Returns:
            List[str]: List of error messages.
        """
        return self._errors.copy()
    
    def get_installed_packages(self) -> Dict[str, bool]:
        """
        Get installed packages.
        
        Returns:
            Dict[str, bool]: Dictionary of installed packages.
        """
        return self._installed_packages.copy()
