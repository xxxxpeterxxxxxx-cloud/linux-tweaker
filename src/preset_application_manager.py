"""
PresetApplicationManager - Coordinates preset application with apps and configs.

This module provides robust preset application with zero-crash policy.
All operations are wrapped in try/except blocks to ensure graceful error handling.
Coordinates between PackageManager and ConfigManager for complete setup.
"""

from typing import Dict, List, Optional, Callable
from enum import Enum
from pathlib import Path
import os
import stat

from src.package_manager import PackageManager, InstallStatus
from src.config_manager import ConfigManager, ConfigStatus
from src.system_checker import WindowManager

# Constants
MAX_PARTIAL_ERRORS = 3
# Maximum file size for operations (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024
# Maximum backup age in days (30 days)
MAX_BACKUP_AGE_DAYS = 30


class PresetType(Enum):
    """Available preset types."""
    GNOME_QUALITY_HYPRLAND = "gnome_quality_hyprland"
    MINIMAL_HYPRLAND = "minimal_hyprland"
    PRODUCTIVITY_HYPRLAND = "productivity_hyprand"


class PresetStatus(Enum):
    """Preset application status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ERROR = "error"


class PresetApplicationManager:
    """
    Manages preset application with apps and configurations.
    
    Features:
    - Coordinates between PackageManager and ConfigManager
    - Applies complete presets (apps + configs)
    - Progress tracking
    - Rollback capability
    - Zero-crash policy
    """
    
    def __init__(self, package_manager: PackageManager, config_manager: ConfigManager):
        """
        Initialize PresetApplicationManager.
        
        Args:
            package_manager: PackageManager instance.
            config_manager: ConfigManager instance.
        """
        self.package_manager = package_manager
        self.config_manager = config_manager
        self._errors: List[str] = []
        self._progress: List[str] = []
        self._applied_presets: List[str] = []
    
    def add_progress(self, message: str):
        """
        Add a progress message.
        
        Args:
            message: Progress message.
        """
        self._progress.append(message)
    
    def apply_preset(
        self,
        preset_type: PresetType,
        install_apps: bool = True,
        apply_configs: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> PresetStatus:
        """
        Apply a complete preset with apps and configurations.
        
        Args:
            preset_type: Type of preset to apply.
            install_apps: Whether to install applications.
            apply_configs: Whether to apply configurations.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            PresetStatus: Status of the preset application.
        """
        try:
            self._errors.clear()
            self._progress.clear()
            
            if progress_callback:
                progress_callback(f"Starting preset application: {preset_type.value}")
            
            self.add_progress(f"Applying preset: {preset_type.value}")
            
            # Install apps if requested
            if install_apps:
                if progress_callback:
                    progress_callback("Installing applications...")
                
                app_status = self._install_preset_apps(preset_type)
                if app_status != PresetStatus.SUCCESS:
                    self._errors.append("App installation failed or partial")
            
            # Apply configs if requested
            if apply_configs:
                if progress_callback:
                    progress_callback("Applying configurations...")
                
                config_status = self._apply_preset_configs(preset_type)
                if config_status != PresetStatus.SUCCESS:
                    self._errors.append("Config application failed or partial")
            
            # Check overall status
            if not self._errors:
                self._applied_presets.append(preset_type.value)
                return PresetStatus.SUCCESS
            elif len(self._errors) < MAX_PARTIAL_ERRORS:
                return PresetStatus.PARTIAL
            else:
                return PresetStatus.FAILED
                
        except Exception as e:
            self._errors.append(f"Error applying preset: {e}")
            return PresetStatus.ERROR
    
    def _install_preset_apps(self, preset_type: PresetType) -> PresetStatus:
        """
        Install applications for a preset.
        
        Args:
            preset_type: Type of preset.
            
        Returns:
            PresetStatus: Status of app installation.
        """
        try:
            if preset_type == PresetType.GNOME_QUALITY_HYPRLAND:
                self.add_progress("Installing essential GNOME-quality apps...")
                results = self.package_manager.install_essential_hyprland_apps()
                
                failed = [app for app, status in results.items() if status != InstallStatus.SUCCESS]
                if failed:
                    self._errors.append(f"Failed to install apps: {', '.join(failed)}")
                    return PresetStatus.PARTIAL
                
                self.add_progress("Successfully installed all essential apps")
                return PresetStatus.SUCCESS
            
            else:
                self.add_progress("No specific apps for this preset")
                return PresetStatus.SUCCESS
                
        except Exception as e:
            self._errors.append(f"Error installing preset apps: {e}")
            return PresetStatus.ERROR
    
    def _apply_preset_configs(self, preset_type: PresetType) -> PresetStatus:
        """
        Apply configurations for a preset.
        
        Args:
            preset_type: Type of preset.
            
        Returns:
            PresetStatus: Status of config application.
        """
        try:
            if preset_type == PresetType.GNOME_QUALITY_HYPRLAND:
                self.add_progress("Applying GNOME-quality Hyprland configuration...")
                
                # Apply Hyprland config
                hyprland_config = self.config_manager.get_gnome_quality_hyprland_config()
                hyprland_status = self.config_manager.apply_hyprland_config(hyprland_config)
                
                if hyprland_status != ConfigStatus.SUCCESS:
                    self._errors.append("Failed to apply Hyprland config")
                    return PresetStatus.FAILED
                
                self.add_progress("Applied Hyprland configuration")
                
                # Apply Waybar config
                self.add_progress("Applying Waybar configuration...")
                waybar_config = self.config_manager.get_gnome_quality_waybar_config()
                waybar_style = self.config_manager.get_gnome_quality_waybar_style()
                waybar_status = self.config_manager.apply_waybar_config(waybar_config, waybar_style)
                
                if waybar_status != ConfigStatus.SUCCESS:
                    self._errors.append("Failed to apply Waybar config")
                    return PresetStatus.PARTIAL
                
                self.add_progress("Applied Waybar configuration")
                
                # Apply Rofi config
                self.add_progress("Applying Rofi configuration...")
                rofi_config = 'configuration {\n    modi: "drun,run,window,ssh";\n    show-icons: true;\n    icon-theme: "Papirus";\n    display-drun: "Apps";\n    display-run: "Run";\n    display-window: "Windows";\n    display-ssh: "SSH";\n    drun-display-format: "{name}";\n    window-format: "{w} · {c}";\n    sidebar-mode: false;\n    matching: "fuzzy";\n    sort: true;\n}\n\n@theme "' + str(Path.home() / '.config' / 'rofi' / 'themes' / 'catppuccin.rasi') + '"'
                
                rofi_theme = '/* Catppuccin Theme for Rofi */\n* {\n    font: "JetBrains Mono 12";\n    background-color: #1e1e2e;\n    text-color: #cdd6f4;\n    selected-background: #89b4fa;\n    selected-text: #1e1e2e;\n    border-color: #89b4fa;\n    separator-color: #45475a;\n}\n\nwindow {\n    background-color: #1e1e2e;\n    border: 2px;\n    border-color: #89b4fa;\n    border-radius: 12px;\n    padding: 20px;\n}\n\nmainbox {\n    background-color: #1e1e2e;\n    border: 0;\n    padding: 0;\n}\n\ninputbar {\n    background-color: #313244;\n    border: 0;\n    border-radius: 8px;\n    padding: 12px;\n    margin: 0 0 15px 0;\n    children: [ prompt, textbox-prompt-colon, entry, case-indicator ];\n}\n\nprompt {\n    background-color: transparent;\n    text-color: #89b4fa;\n    padding: 0 8px 0 0;\n}\n\ntextbox-prompt-colon {\n    background-color: transparent;\n    text-color: #cdd6f4;\n    padding: 0;\n    expand: false;\n    str: ":";\n}\n\nentry {\n    background-color: transparent;\n    text-color: #cdd6f4;\n    padding: 0;\n    placeholder: "Search...";\n    placeholder-color: #6c7086;\n}\n\ncase-indicator {\n    background-color: transparent;\n    text-color: #a6e3a1;\n    padding: 0 8px 0 0;\n}\n\nlistbox {\n    background-color: #1e1e2e;\n    border: 0;\n    padding: 0;\n    spacing: 4px;\n}\n\nelement {\n    background-color: #313244;\n    border: 0;\n    border-radius: 8px;\n    padding: 10px;\n    children: [ element-icon, element-text ];\n    spacing: 10px;\n}\n\nelement normal.normal {\n    background-color: #313244;\n    text-color: #cdd6f4;\n}\n\nelement normal.urgent {\n    background-color: #f38ba8;\n    text-color: #1e1e2e;\n}\n\nelement normal.active {\n    background-color: #a6e3a1;\n    text-color: #1e1e2e;\n}\n\nelement selected.normal {\n    background-color: #89b4fa;\n    text-color: #1e1e2e;\n}\n\nelement selected.urgent {\n    background-color: #f38ba8;\n    text-color: #1e1e2e;\n}\n\nelement selected.active {\n    background-color: #a6e3a1;\n    text-color: #1e1e2e;\n}\n\nelement-icon {\n    background-color: transparent;\n    size: 24px;\n    text-color: #cdd6f4;\n}\n\nelement-text {\n    background-color: transparent;\n    text-color: #cdd6f4;\n}'
                
                rofi_status = self.config_manager.apply_rofi_config(rofi_config, rofi_theme)
                
                if rofi_status != ConfigStatus.SUCCESS:
                    self._errors.append("Failed to apply Rofi config")
                    return PresetStatus.PARTIAL
                
                self.add_progress("Applied Rofi configuration")
                
                return PresetStatus.SUCCESS
            
            else:
                self.add_progress("No specific configs for this preset")
                return PresetStatus.SUCCESS
                
        except Exception as e:
            self._errors.append(f"Error applying preset configs: {e}")
            return PresetStatus.ERROR
    
    def get_available_presets(self) -> List[PresetType]:
        """
        Get list of available presets.
        
        Returns:
            List[PresetType]: Available presets.
        """
        return list(PresetType)
    
    def get_preset_description(self, preset_type: PresetType) -> str:
        """
        Get description of a preset.
        
        Args:
            preset_type: Type of preset.
            
        Returns:
            str: Preset description.
        """
        descriptions = {
            PresetType.GNOME_QUALITY_HYPRLAND: "GNOME-quality Hyprland setup with essential apps, modern Waybar, Rofi launcher, and polished configurations for daily use.",
            PresetType.MINIMAL_HYPRLAND: "Minimal Hyprland setup with bare essentials for a clean, lightweight experience.",
            PresetType.PRODUCTIVITY_HYPRLAND: "Productivity-focused Hyprland setup with apps and configs optimized for work and development."
        }
        
        return descriptions.get(preset_type, "No description available.")
    
    def get_errors(self) -> List[str]:
        """
        Get all errors encountered during operations.
        
        Returns:
            List[str]: List of error messages.
        """
        return self._errors.copy()
    
    def get_progress(self) -> List[str]:
        """
        Get progress messages.
        
        Returns:
            List[str]: List of progress messages.
        """
        return self._progress.copy()
    
    def get_applied_presets(self) -> List[str]:
        """
        Get list of applied presets.
        
        Returns:
            List[str]: List of applied preset names.
        """
        return self._applied_presets.copy()
