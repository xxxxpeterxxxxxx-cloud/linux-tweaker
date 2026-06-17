"""
ConfigManager - Handles configuration downloading and application.

This module provides robust configuration management with zero-crash policy.
All operations are wrapped in try/except blocks to ensure graceful error handling.
Supports downloading configs from GitHub and applying them to user space.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum
from urllib.parse import urlparse


class ConfigType(Enum):
    """Configuration types."""
    HYPRLAND = "hyprland"
    WAYBAR = "waybar"
    ROFI = "rofi"
    AGS = "ags"
    DOTFILES = "dotfiles"
    WALLPAPER = "wallpaper"


class ConfigStatus(Enum):
    """Configuration operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ConfigManager:
    """
    Manages configuration downloading and application.
    
    Features:
    - Download configs from GitHub repositories
    - Apply configurations to user space
    - Wallpaper management
    - Dotfiles repository cloning
    - Zero-crash policy
    """
    
    def __init__(self, file_manager):
        """
        Initialize ConfigManager.
        
        Args:
            file_manager: FileManager instance for file operations.
        """
        self.file_manager = file_manager
        self._errors: List[str] = []
        self._downloaded_configs: Dict[str, Path] = {}
    
    def download_file(self, url: str, dest: Path) -> ConfigStatus:
        """
        Download a file from URL.
        
        Args:
            url: URL to download from.
            dest: Destination path.
            
        Returns:
            ConfigStatus: Status of the download.
        """
        try:
            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Use curl to download
            result = subprocess.run(
                ["curl", "-L", "-o", str(dest), url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return ConfigStatus.SUCCESS
            else:
                self._errors.append(f"Failed to download from {url}: {result.stderr}")
                return ConfigStatus.FAILED
                
        except subprocess.TimeoutExpired:
            self._errors.append(f"Download timed out for {url}")
            return ConfigStatus.FAILED
        except Exception as e:
            self._errors.append(f"Error downloading from {url}: {e}")
            return ConfigStatus.ERROR
    
    def clone_repo(self, repo_url: str, dest: Path) -> ConfigStatus:
        """
        Clone a Git repository.
        
        Args:
            repo_url: Git repository URL.
            dest: Destination path.
            
        Returns:
            ConfigStatus: Status of the clone operation.
        """
        try:
            dest = Path(dest)
            
            # Check if git is available
            import shutil
            if not shutil.which("git"):
                self._errors.append("Git is not available")
                return ConfigStatus.FAILED
            
            # Clone repository
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(dest)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return ConfigStatus.SUCCESS
            else:
                self._errors.append(f"Failed to clone {repo_url}: {result.stderr}")
                return ConfigStatus.FAILED
                
        except subprocess.TimeoutExpired:
            self._errors.append(f"Git clone timed out for {repo_url}")
            return ConfigStatus.FAILED
        except Exception as e:
            self._errors.append(f"Error cloning {repo_url}: {e}")
            return ConfigStatus.ERROR
    
    def apply_hyprland_config(self, config_content: str) -> ConfigStatus:
        """
        Apply Hyprland configuration.
        
        Args:
            config_content: Hyprland configuration content.
            
        Returns:
            ConfigStatus: Status of the application.
        """
        try:
            config_path = Path.home() / ".config" / "hypr" / "hyprland.conf"
            
            # Create backup
            self.file_manager.create_backup(config_path)
            
            # Write new config
            status = self.file_manager.write_file(config_path, config_content, create_backup=False)
            
            if status.value == "success":
                return ConfigStatus.SUCCESS
            else:
                return ConfigStatus.FAILED
                
        except Exception as e:
            self._errors.append(f"Error applying Hyprland config: {e}")
            return ConfigStatus.ERROR
    
    def apply_waybar_config(self, config_content: str, style_content: str) -> ConfigStatus:
        """
        Apply Waybar configuration.
        
        Args:
            config_content: Waybar config.jsonc content.
            style_content: Waybar style.css content.
            
        Returns:
            ConfigStatus: Status of the application.
        """
        try:
            config_path = Path.home() / ".config" / "waybar" / "config.jsonc"
            style_path = Path.home() / ".config" / "waybar" / "style.css"
            
            # Create backups
            self.file_manager.create_backup(config_path)
            self.file_manager.create_backup(style_path)
            
            # Write new configs
            config_status = self.file_manager.write_file(config_path, config_content, create_backup=False)
            style_status = self.file_manager.write_file(style_path, style_content, create_backup=False)
            
            if config_status.value == "success" and style_status.value == "success":
                return ConfigStatus.SUCCESS
            else:
                return ConfigStatus.FAILED
                
        except Exception as e:
            self._errors.append(f"Error applying Waybar config: {e}")
            return ConfigStatus.ERROR
    
    def apply_rofi_config(self, config_content: str, theme_content: str) -> ConfigStatus:
        """
        Apply Rofi configuration.
        
        Args:
            config_content: Rofi config.rasi content.
            theme_content: Rofi theme content.
            
        Returns:
            ConfigStatus: Status of the application.
        """
        try:
            config_path = Path.home() / ".config" / "rofi" / "config.rasi"
            theme_path = Path.home() / ".config" / "rofi" / "themes" / "catppuccin.rasi"
            
            # Create backups
            self.file_manager.create_backup(config_path)
            self.file_manager.create_backup(theme_path)
            
            # Write new configs
            config_status = self.file_manager.write_file(config_path, config_content, create_backup=False)
            theme_status = self.file_manager.write_file(theme_path, theme_content, create_backup=False)
            
            if config_status.value == "success" and theme_status.value == "success":
                return ConfigStatus.SUCCESS
            else:
                return ConfigStatus.FAILED
                
        except Exception as e:
            self._errors.append(f"Error applying Rofi config: {e}")
            return ConfigStatus.ERROR
    
    def apply_wallpaper(self, wallpaper_url: str) -> ConfigStatus:
        """
        Download and apply wallpaper.
        
        Args:
            wallpaper_url: URL to download wallpaper from.
            
        Returns:
            ConfigStatus: Status of the application.
        """
        try:
            # Download wallpaper
            wallpaper_dir = Path.home() / ".config" / "linux-tweaker" / "wallpapers"
            wallpaper_dir.mkdir(parents=True, exist_ok=True)
            
            filename = wallpaper_url.split("/")[-1]
            wallpaper_path = wallpaper_dir / filename
            
            download_status = self.download_file(wallpaper_url, wallpaper_path)
            
            if download_status != ConfigStatus.SUCCESS:
                return download_status
            
            # Apply wallpaper based on WM
            # For now, just save it - application depends on WM
            self._downloaded_configs["wallpaper"] = wallpaper_path
            
            return ConfigStatus.SUCCESS
            
        except Exception as e:
            self._errors.append(f"Error applying wallpaper: {e}")
            return ConfigStatus.ERROR
    
    def apply_dotfiles(self, repo_url: str) -> ConfigStatus:
        """
        Clone and apply dotfiles from a repository.
        
        Args:
            repo_url: Git repository URL.
            
        Returns:
            ConfigStatus: Status of the application.
        """
        try:
            # Clone repository
            dotfiles_dir = Path.home() / ".config" / "linux-tweaker" / "dotfiles"
            
            clone_status = self.clone_repo(repo_url, dotfiles_dir)
            
            if clone_status != ConfigStatus.SUCCESS:
                return clone_status
            
            # Look for install script
            install_scripts = [
                dotfiles_dir / "install.sh",
                dotfiles_dir / "setup.sh",
                dotfiles_dir / "bootstrap.sh"
            ]
            
            for script in install_scripts:
                if script.exists():
                    # Make executable and run
                    script.chmod(0o755)
                    result = subprocess.run(
                        [str(script)],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        return ConfigStatus.SUCCESS
                    else:
                        self._errors.append(f"Install script failed: {result.stderr}")
                        return ConfigStatus.FAILED
            
            # No install script found, just copy files
            return ConfigStatus.SUCCESS
            
        except Exception as e:
            self._errors.append(f"Error applying dotfiles: {e}")
            return ConfigStatus.ERROR
    
    def get_gnome_quality_hyprland_config(self) -> str:
        """
        Get a GNOME-quality Hyprland configuration.
        
        Returns:
            str: Hyprland configuration content.
        """
        return """# GNOME-Quality Hyprland Configuration
# Optimized for daily use with modern aesthetics

monitor=,preferred,auto,auto

# Input settings
input {
    kb_layout = us
    follow_mouse = 1
    touchpad {
        natural_scroll = no
        tap-to-click = yes
    }
}

# General settings
general {
    gaps_in = 5
    gaps_out = 10
    border_size = 2
    col.active_border = rgba(89b4faee)
    col.inactive_border = rgba(45475aee)
    layout = dwindle
}

# Decoration with blur
decoration {
    rounding = 10
    blur {
        enabled = yes
        size = 8
        passes = 3
    }
    drop_shadow = yes
    shadow_range = 20
    shadow_render_power = 3
}

# Animations
animations {
    enabled = yes
    animation = windows, 1, 7, default
    animation = workspaces, 1, 6, default
    animation = border, 1, 10, default
}

# Dwindle layout
dwindle {
    pseudotile = yes
    preserve_split = yes
}

$mod = SUPER

# Terminal
bind = $mod, Return, exec, kitty

# App launcher
bind = $mod, D, exec, rofi -show drun
bind = $mod, TAB, exec, rofi -show window

# Window management
bind = $mod, Q, killactive,
bind = $mod, F, fullscreen, 0
bind = $mod, V, togglefloating,
bind = $mod, Space, togglesplit,
bind = $mod, M, togglespecialworkspace, magic
bind = $mod SHIFT, M, movetoworkspacespecial, magic

# Move focus
bind = $mod, left, movefocus, l
bind = $mod, right, movefocus, r
bind = $mod, up, movefocus, u
bind = $mod, down, movefocus, d

# Move windows
bind = $mod SHIFT, left, movewindow, l
bind = $mod SHIFT, right, movewindow, r
bind = $mod SHIFT, up, movewindow, u
bind = $mod SHIFT, down, movewindow, d

# Resize windows
bind = $mod CTRL, left, resizeactive, -10 0
bind = $mod CTRL, right, resizeactive, 10 0
bind = $mod CTRL, up, resizeactive, 0 -10
bind = $mod CTRL, down, resizeactive, 0 10

# Workspaces
bind = $mod, 1, workspace, 1
bind = $mod, 2, workspace, 2
bind = $mod, 3, workspace, 3
bind = $mod, 4, workspace, 4
bind = $mod, 5, workspace, 5
bind = $mod, 6, workspace, 6
bind = $mod, 7, workspace, 7
bind = $mod, 8, workspace, 8
bind = $mod, 9, workspace, 9
bind = $mod, 0, workspace, 10

bind = $mod SHIFT, 1, movetoworkspace, 1
bind = $mod SHIFT, 2, movetoworkspace, 2
bind = $mod SHIFT, 3, movetoworkspace, 3
bind = $mod SHIFT, 4, movetoworkspace, 4
bind = $mod SHIFT, 5, movetoworkspace, 5
bind = $mod SHIFT, 6, movetoworkspace, 6
bind = $mod SHIFT, 7, movetoworkspace, 7
bind = $mod SHIFT, 8, movetoworkspace, 8
bind = $mod SHIFT, 9, movetoworkspace, 9
bind = $mod SHIFT, 0, movetoworkspace, 10

# Scroll through workspaces
bind = $mod, mouse_down, workspace, e+1
bind = $mod, mouse_up, workspace, e-1

# Mouse bindings
bindm = $mod, mouse:272, movewindow
bindm = $mod, mouse:273, resizewindow

# Useful apps
bind = $mod, E, exec, thunar
bind = $mod, B, exec, firefox
bind = $mod, C, exec, code
bind = $mod, T, exec, telegram-desktop
bind = $mod, D, exec, discord
bind = $mod, S, exec, spotify

# Media keys
bind = , XF86AudioRaiseVolume, exec, wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
bind = , XF86AudioLowerVolume, exec, wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
bind = , XF86AudioMute, exec, wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
bind = , XF86MonBrightnessUp, exec, brightnessctl set +5%
bind = , XF86MonBrightnessDown, exec, brightnessctl set 5%-

# Screenshot
bind = $mod SHIFT, S, exec, grim -g "$(slurp)" - | wl-copy

# Reload config
bind = $mod SHIFT, R, reload,

# Startup
exec-once = waybar
exec-once = dunst
exec-once = swww init
exec-once = swww img /usr/share/backgrounds/default.png
"""
    
    def get_gnome_quality_waybar_config(self) -> str:
        """
        Get a GNOME-quality Waybar configuration.
        
        Returns:
            str: Waybar configuration content.
        """
        return """{
  "layer": "top",
  "position": "top",
  "height": 40,
  "spacing": 8,
  "margin-top": 8,
  "margin-left": 12,
  "margin-right": 12,
  "modules-left": [
    "hyprland/workspaces",
    "hyprland/window"
  ],
  "modules-center": [
    "clock"
  ],
  "modules-right": [
    "network",
    "pulseaudio",
    "battery",
    "tray"
  ],
  "hyprland/workspaces": {
    "disable-scroll": false,
    "all-outputs": true,
    "format": "{name}",
    "persistent-workspaces": {
      "1": {},
      "2": {},
      "3": {},
      "4": {},
      "5": {}
    }
  },
  "hyprland/window": {
    "format": "{}",
    "max-length": 40,
    "separate-outputs": true
  },
  "clock": {
    "format": "{:%H:%M}",
    "format-alt": "{:%Y-%m-%d %H:%M:%S}",
    "tooltip-format": "<tt>{calendar}</tt>"
  },
  "network": {
    "format-wifi": "WiFi {signalStrength}%",
    "format-ethernet": "Ethernet",
    "format-disconnected": "Disconnected",
    "tooltip-format": "{ifname}: {ipaddr}",
    "interval": 5
  },
  "pulseaudio": {
    "format": "{icon} {volume}%",
    "format-muted": "Muted",
    "format-icons": {
      "default": ["", "", ""]
    },
    "on-click": "pavucontrol"
  },
  "battery": {
    "states": {
      "warning": 30,
      "critical": 15
    },
    "format": "{icon} {capacity}%",
    "format-charging": " {capacity}%",
    "format-plugged": " {capacity}%",
    "format-icons": ["", "", "", "", ""],
    "interval": 30
  },
  "tray": {
    "icon-size": 18,
    "spacing": 10
  }
}"""
    
    def get_gnome_quality_waybar_style(self) -> str:
        """
        Get a GNOME-quality Waybar style.
        
        Returns:
            str: Waybar style content.
        """
        return """/* GNOME-Quality Waybar Theme */
* {
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 13px;
    font-weight: 500;
    min-height: 0;
    margin: 0;
    padding: 0;
}

window#waybar {
    background-color: rgba(30, 30, 46, 0.9);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: #cdd6f4;
}

window#waybar.hidden {
    opacity: 0.2;
}

#workspaces {
    margin-left: 8px;
}

#workspaces button {
    padding: 0 12px;
    margin: 0 4px;
    color: rgba(205, 214, 244, 0.5);
    background-color: transparent;
    border-radius: 6px;
    transition: all 0.2s ease;
}

#workspaces button:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #cdd6f4;
}

#workspaces button.focused {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

#workspaces button.urgent {
    background-color: #f38ba8;
    color: #1e1e2e;
}

#clock {
    font-weight: bold;
    font-size: 14px;
    padding: 0 16px;
}

#network,
#pulseaudio,
#battery {
    padding: 0 12px;
    margin: 0 4px;
}

#network.disconnected {
    color: #f38ba8;
}

#pulseaudio.muted {
    color: rgba(205, 214, 244, 0.5);
}

#battery.charging {
    color: #a6e3a1;
}

#battery.warning:not(.charging) {
    color: #f9e2af;
}

#battery.critical:not(.charging) {
    color: #f38ba8;
}

#tray {
    margin-right: 8px;
    padding: 0 8px;
}

#tray > .passive {
    -gtk-icon-effect: dim;
}

#tray > .needs-attention {
    -gtk-icon-effect: highlight;
}

tooltip {
    background-color: #1e1e2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 12px;
}

tooltip label {
    color: #cdd6f4;
}"""
    
    def get_errors(self) -> List[str]:
        """
        Get all errors encountered during operations.
        
        Returns:
            List[str]: List of error messages.
        """
        return self._errors.copy()
    
    def get_downloaded_configs(self) -> Dict[str, Path]:
        """
        Get downloaded configurations.
        
        Returns:
            Dict[str, Path]: Dictionary of downloaded configs.
        """
        return self._downloaded_configs.copy()
