"""
Hyprland / Sway / i3 Theme Engine
Manages dotfiles in ~/.config/ for wayland and X11 tiling WMs.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from theme_engine import Preset, PreviewResult, ThemeEngine


class HyprlandThemeEngine(ThemeEngine):
    """Theme engine for Hyprland, Sway, and i3 via dotfile management."""

    def __init__(self):
        super().__init__()
        self.config_dir = Path.home() / ".config"
        self.wm = self._detect_wm()
        self.themes_dir = Path.home() / ".themes"
        self.icons_dir = Path.home() / ".icons"
        self.fonts_dir = Path.home() / ".local" / "share" / "fonts"
        for d in (self.themes_dir, self.icons_dir, self.fonts_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._check_dependencies()
        self._dotfiles_applied = False

    def _check_dependencies(self):
        """Check if required tools are installed. Warn if missing."""
        deps = ["gsettings", "git"]
        if self.wm == "hyprland":
            deps.extend(["hyprctl", "swww", "waybar", "rofi"])
        elif self.wm == "sway":
            deps.extend(["swaymsg", "waybar", "rofi"])
        elif self.wm == "i3":
            deps.extend(["feh", "rofi"])
        
        missing = []
        for dep in deps:
            try:
                self._run([dep, "--version"], check=False)
            except FileNotFoundError:
                missing.append(dep)
        
        if missing:
            print(f"[{self.wm.title()}] WARNING: Missing dependencies: {', '.join(missing)}")
            print(f"[{self.wm.title()}] Some features may not work. Install with your package manager.")

    def _detect_wm(self) -> str:
        if (self.config_dir / "hypr" / "hyprland.conf").exists():
            return "hyprland"
        if (self.config_dir / "sway" / "config").exists():
            return "sway"
        if (self.config_dir / "i3" / "config").exists():
            return "i3"
        return "hyprland"  # default

    def _wm_config(self) -> Path:
        if self.wm == "hyprland":
            return self.config_dir / "hypr" / "hyprland.conf"
        if self.wm == "sway":
            return self.config_dir / "sway" / "config"
        return self.config_dir / "i3" / "config"

    def _install_theme(self, name: str, url: str) -> bool:
        return self._install_theme_asset(name, url, self.themes_dir, "hypr_theme")

    def _install_icon_theme(self, name: str, url: str) -> bool:
        return self._install_theme_asset(name, url, self.icons_dir, "hypr_icons")

    def _install_cursor_theme(self, name: str, url: str) -> bool:
        """Download and install a cursor theme to ~/.local/share/icons/."""
        return self._install_theme_asset(name, url, self.icons_dir, "hypr_cursor")

    def _replace_line(self, path: Path, key: str, new_value: str):
        """Replace a key=value line in Hyprland config. Handles block syntax like general:border_size."""
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            # For block syntax, create the block structure
            if ":" in key:
                section, setting = key.split(":", 1)
                path.write_text(f"{section} {{\n    {setting} = {new_value}\n}}\n")
            else:
                path.write_text(f"{key} = {new_value}\n")
            return True
        
        lines = path.read_text().splitlines()
        replaced = False
        
        # Handle block syntax (e.g., "general:border_size")
        if ":" in key:
            section, setting = key.split(":", 1)
            in_section = False
            section_indent = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Detect section start
                if stripped.startswith(section + " {"):
                    in_section = True
                    section_indent = len(line) - len(line.lstrip())
                    continue
                # Detect section end
                if in_section and stripped == "}":
                    in_section = False
                    continue
                # If we're in the right section, look for the setting
                if in_section:
                    if stripped.startswith(setting + "=") or stripped.startswith(setting + " ="):
                        # Preserve indentation
                        indent = len(line) - len(line.lstrip())
                        lines[i] = " " * indent + f"{setting} = {new_value}"
                        replaced = True
                        break
            
            # If not found, add it to the section (create section if needed)
            if not replaced:
                # Find if section exists
                section_found = False
                section_line_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(section + " {"):
                        section_found = True
                        section_line_idx = i
                        break
                
                if section_found:
                    # Find the closing brace and insert before it
                    for i in range(section_line_idx + 1, len(lines)):
                        if lines[i].strip() == "}":
                            indent = len(lines[section_line_idx]) - len(lines[section_line_idx].lstrip())
                            lines.insert(i, " " * (indent + 4) + f"{setting} = {new_value}")
                            replaced = True
                            break
                else:
                    # Create new section at end
                    lines.append(f"{section} {{")
                    lines.append(f"    {setting} = {new_value}")
                    lines.append(f"}}")
                    replaced = True
        else:
            # Handle flat key syntax (fallback)
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith(key + "=") or stripped.startswith(key + " ="):
                    lines[i] = f"{key} = {new_value}"
                    replaced = True
            if not replaced:
                lines.append(f"{key} = {new_value}")
        
        path.write_text("\n".join(lines) + "\n")
        return True

    def _read_config_value(self, path: Path, key: str) -> str:
        """Read a value from Hyprland config. Handles flat keys and block syntax (section:key)."""
        if not path.exists():
            return "unknown"
        lines = path.read_text().splitlines()
        if ":" in key:
            section, setting = key.split(":", 1)
            in_section = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(section + " {"):
                    in_section = True
                    continue
                if in_section and stripped == "}":
                    in_section = False
                    continue
                if in_section:
                    if stripped.startswith(setting + "=") or stripped.startswith(setting + " ="):
                        return stripped.split("=", 1)[1].strip().split("#")[0].strip()
            return "unknown"
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith(key + "=") or stripped.startswith(key + " ="):
                return stripped.split("=", 1)[1].strip().split("#")[0].strip()
        return "unknown"

    def _apply_wallpaper(self, url: str):
        """Set wallpaper via swww, hyprpaper, swaybg, or feh depending on WM."""
        path = self._download_wallpaper(url, self.backup_dir)
        wallpaper = str(path) if path else url

        if self.wm == "hyprland":
            # Try swww first (most common in Hyprland setups)
            try:
                self._run(["swww", "img", wallpaper], check=False)
                print(f"  -> Wallpaper set via swww: {wallpaper}")
                return
            except FileNotFoundError:
                pass
            # Fallback to hyprpaper
            hyprpaper = self.config_dir / "hypr" / "hyprpaper.conf"
            if hyprpaper.exists():
                self._replace_line(hyprpaper, "preload", wallpaper)
                self._replace_line(hyprpaper, "wallpaper", f"eDP-1,{wallpaper}")
                try:
                    self._run(["hyprctl", "reload"], check=False)
                except FileNotFoundError:
                    pass
                print(f"  -> Wallpaper set via hyprpaper: {wallpaper}")
                return
            # Fallback to feh
            try:
                self._run(["feh", "--bg-scale", wallpaper], check=False)
                print(f"  -> Wallpaper set via feh: {wallpaper}")
            except FileNotFoundError:
                print(f"  -> Wallpaper downloaded but no setter found (swww/hyprpaper/feh)")

        elif self.wm == "sway":
            self._replace_line(self._wm_config(), "output * bg", f"{wallpaper} fill")
            self._run(["swaymsg", "reload"], check=False)
            print(f"  -> Wallpaper set (Sway): {wallpaper}")

        elif self.wm == "i3":
            self._run(["feh", "--bg-scale", wallpaper], check=False)
            print(f"  -> Wallpaper set (i3): {wallpaper}")

    def _apply_waybar_theme(self, style: str, url: str = "", theme_config: dict = None):
        """Download and apply waybar style from URL or generate full glassmorphism CSS + config."""
        waybar_dir = self.config_dir / "waybar"
        waybar_dir.mkdir(parents=True, exist_ok=True)
        
        # If dotfiles already provided waybar configs, skip generation
        if self._dotfiles_applied and (waybar_dir / "style.css").exists() and any((waybar_dir / f).exists() for f in ("config", "config.jsonc")):
            print("  -> Waybar config from dotfiles preserved")
            self._restart_waybar()
            return
        
        if url:
            archive = self.backup_dir / f"waybar_{style}.zip"
            tmp_dir = self.backup_dir / f"waybar_{style}_tmp"
            if self._download_file(url, archive):
                extracted = self._extract_archive(archive, tmp_dir)
                if extracted:
                    try:
                        css_file = None
                        if (extracted / "style.css").exists():
                            css_file = extracted / "style.css"
                        else:
                            for f in extracted.rglob("style.css"):
                                css_file = f
                                break
                        if css_file:
                            shutil.copy2(css_file, waybar_dir / "style.css")
                            for cfg_name in ("config", "config.jsonc"):
                                cfg_src = extracted / cfg_name
                                if cfg_src.exists():
                                    shutil.copy2(cfg_src, waybar_dir / cfg_name)
                                    break
                                for found in extracted.rglob(cfg_name):
                                    shutil.copy2(found, waybar_dir / cfg_name)
                                    break
                            print(f"  -> Waybar style downloaded: {style}")
                            self._restart_waybar()
                            return
                    finally:
                        # Clean up temporary directory
                        if tmp_dir.exists():
                            try:
                                shutil.rmtree(tmp_dir)
                            except (shutil.Error, OSError):
                                pass
        
        # Extract colors
        accent = "#89b4fa"
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        if theme_config:
            def hex_to_css(c):
                return "#" + c[4:] if c.startswith("0xff") else c
            accent = hex_to_css(theme_config.get("general:col.active_border", "0xff89b4fa"))
        if "a6e3a1" in accent.lower() or "green" in style.lower() or "lime" in style.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#a6e3a1"
        elif "bd93f9" in accent.lower() or "purple" in style.lower() or "violet" in style.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#bd93f9"
        elif "ff79c6" in accent.lower() or "pink" in style.lower() or "retro" in style.lower():
            bg = "#282a36"; fg = "#f8f8f2"; accent = "#ff79c6"
        elif "88c0d0" in accent.lower() or "nord" in style.lower():
            bg = "#2e3440"; fg = "#d8dee9"; accent = "#88c0d0"
        elif "89b4fa" in accent.lower() or "blue" in style.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#89b4fa"
        
        rgba_bg = f"rgba({int(bg[1:3],16)},{int(bg[3:5],16)},{int(bg[5:7],16)},0.75)"
        
        css = f"""/* linux-tweaker glassmorphism waybar theme */
* {{ font-family: "Inter", "JetBrains Mono Nerd Font", "Font Awesome 6 Free", sans-serif; font-size: 14px; font-weight: 500; min-height: 0; }}
window#waybar {{ background-color: {rgba_bg}; border-bottom: 2px solid {accent}; color: {fg}; transition-property: background-color; transition-duration: 0.5s; }}
window#waybar.hidden {{ opacity: 0.2; }}
.modules-left, .modules-center, .modules-right {{ padding: 0 8px; }}
#workspaces, #window, #cpu, #memory, #temperature, #network, #pulseaudio, #battery, #clock, #tray, #custom-media {{
    background-color: rgba(255,255,255,0.05); border-radius: 12px; padding: 4px 12px; margin: 4px 2px; color: {fg}; transition: all 0.3s ease;
}}
#workspaces:hover, #cpu:hover, #memory:hover, #temperature:hover, #network:hover, #pulseaudio:hover, #battery:hover, #clock:hover {{
    background-color: rgba(255,255,255,0.12);
}}
#workspaces {{ padding: 4px 6px; }}
#workspaces button {{ padding: 0 10px; margin: 0 2px; color: rgba({int(fg[1:3],16)},{int(fg[3:5],16)},{int(fg[5:7],16)},0.4); background-color: transparent; border-radius: 8px; transition: all 0.3s ease; min-width: 24px; }}
#workspaces button:hover {{ background-color: rgba(255,255,255,0.1); color: {fg}; }}
#workspaces button.focused {{ background-color: {accent}; color: {bg}; font-weight: bold; }}
#workspaces button.urgent {{ background-color: #f38ba8; color: {bg}; }}
#window {{ font-weight: 500; }}
window#waybar.empty #window {{ background-color: transparent; }}
#clock {{ font-weight: bold; font-size: 15px; }}
#battery {{ color: {fg}; }}
#battery.charging {{ color: #a6e3a1; }}
#battery.warning:not(.charging) {{ color: #f9e2af; }}
#battery.critical:not(.charging) {{ color: #f38ba8; animation: blink 1s linear infinite; }}
@keyframes blink {{ 50% {{ opacity: 0.5; }} }}
#network {{ color: {fg}; }}
#network.disconnected {{ color: #f38ba8; }}
#pulseaudio {{ color: {fg}; }}
#pulseaudio.muted {{ color: rgba({int(fg[1:3],16)},{int(fg[3:5],16)},{int(fg[5:7],16)},0.3); }}
#tray {{ padding: 4px 8px; }}
#tray > .passive {{ -gtk-icon-effect: dim; }}
#tray > .needs-attention {{ -gtk-icon-effect: highlight; background-color: #f38ba8; }}
#temperature {{ color: {fg}; }}
#temperature.critical {{ color: #f38ba8; }}
#cpu, #memory {{ color: {fg}; }}
tooltip {{ background-color: {bg}; border: 1px solid {accent}; border-radius: 8px; padding: 8px; }}
tooltip label {{ color: {fg}; }}
"""
        (waybar_dir / "style.css").write_text(css)
        
        config = {
            "layer": "top",
            "position": "top",
            "height": 36,
            "spacing": 4,
            "margin-top": 6,
            "margin-left": 10,
            "margin-right": 10,
            "modules-left": ["hyprland/workspaces", "hyprland/window"],
            "modules-center": ["clock"],
            "modules-right": ["cpu", "memory", "temperature", "network", "pulseaudio", "battery", "tray"],
            "hyprland/workspaces": {
                "disable-scroll": False,
                "all-outputs": True,
                "format": "{icon}",
                "format-icons": {"1":"1","2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9","10":"10","urgent":"!","active":"●","default":"○"}
            },
            "hyprland/window": {
                "max-length": 60,
                "separate-outputs": True
            },
            "clock": {
                "format": "  %H:%M",
                "format-alt": "  %Y-%m-%d %H:%M:%S",
                "tooltip-format": "<big>%Y %B</big>\n<tt>{calendar}</tt>"
            },
            "cpu": {
                "format": "  {usage}%",
                "tooltip": True,
                "interval": 2
            },
            "memory": {
                "format": "󰍛  {percentage}%",
                "tooltip-format": "RAM: {used:0.1f}GB / {total:0.1f}GB",
                "interval": 5
            },
            "temperature": {
                "critical-threshold": 80,
                "format": "  {temperatureC}°C",
                "format-critical": "  {temperatureC}°C",
                "tooltip": True
            },
            "network": {
                "format-wifi": "󰤨  {essid}",
                "format-ethernet": "󰈀  {ipaddr}/{cidr}",
                "format-linked": "󰈀  {ifname} (No IP)",
                "format-disconnected": "󰤭  Disconnected",
                "format-alt": "󰈀  {ipaddr}",
                "tooltip-format": "{ifname}: {ipaddr}/{cidr}",
                "interval": 10
            },
            "pulseaudio": {
                "format": "{icon}  {volume}%",
                "format-muted": "󰖁  Muted",
                "format-icons": {"default":["󰕿","󰖀","󰕾"]},
                "tooltip-format": "{desc}",
                "on-click": "pavucontrol"
            },
            "battery": {
                "states": {"warning":30,"critical":15},
                "format": "{icon}  {capacity}%",
                "format-charging": "󰂄  {capacity}%",
                "format-plugged": "󰚥  {capacity}%",
                "format-icons": ["󰁺","󰁻","󰁼","󰁽","󰁾","󰁿","󰂀","󰂁","󰂂","󰁹"],
                "tooltip-format": "{timeTo}",
                "interval": 30
            },
            "tray": {
                "icon-size": 16,
                "spacing": 8
            }
        }
        config_json = json.dumps(config, indent=2)
        config_json = config_json.replace('"False"', 'false').replace('"True"', 'true')
        (waybar_dir / "config.jsonc").write_text(config_json)
        print(f"  -> Waybar glassmorphism theme applied: {style}")
        self._restart_waybar()

    def _restart_waybar(self):
        """Kill and restart waybar non-blocking."""
        self._run(["pkill", "waybar"], check=False)
        try:
            subprocess.Popen(["waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except (FileNotFoundError, OSError):
            pass

    def _apply_rofi_theme(self, theme: str, url: str = "", theme_config: dict = None):
        """Download and apply rofi theme from URL or generate full glassmorphism .rasi."""
        rofi_dir = self.config_dir / "rofi"
        rofi_dir.mkdir(parents=True, exist_ok=True)
        rofi_cfg = rofi_dir / "config.rasi"
        
        if self._dotfiles_applied and rofi_cfg.exists():
            print("  -> Rofi config from dotfiles preserved")
            return
        
        if url:
            archive = self.backup_dir / f"rofi_{theme}.zip"
            tmp_dir = self.backup_dir / f"rofi_{theme}_tmp"
            if self._download_file(url, archive):
                extracted = self._extract_archive(archive, tmp_dir)
                if extracted:
                    try:
                        rasi_files = list(extracted.rglob("*.rasi"))
                        if rasi_files:
                            shutil.copy2(rasi_files[0], rofi_cfg)
                            print(f"  -> Rofi theme downloaded: {theme}")
                            return
                    finally:
                        # Clean up temporary directory
                        if tmp_dir.exists():
                            try:
                                shutil.rmtree(tmp_dir)
                            except (shutil.Error, OSError):
                                pass
        
        accent = "#89b4fa"
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        if theme_config:
            def hex_to_css(c):
                return "#" + c[4:] if c.startswith("0xff") else c
            accent = hex_to_css(theme_config.get("general:col.active_border", "0xff89b4fa"))
        if "a6e3a1" in accent.lower() or "green" in theme.lower() or "lime" in theme.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#a6e3a1"
        elif "bd93f9" in accent.lower() or "purple" in theme.lower() or "violet" in theme.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#bd93f9"
        elif "ff79c6" in accent.lower() or "pink" in theme.lower() or "retro" in theme.lower():
            bg = "#282a36"; fg = "#f8f8f2"; accent = "#ff79c6"
        elif "88c0d0" in accent.lower() or "nord" in theme.lower():
            bg = "#2e3440"; fg = "#d8dee9"; accent = "#88c0d0"
        elif "89b4fa" in accent.lower() or "blue" in theme.lower():
            bg = "#1a1b26"; fg = "#c0caf5"; accent = "#89b4fa"
        
        rgba_bg = f"rgba({int(bg[1:3],16)},{int(bg[3:5],16)},{int(bg[5:7],16)},0.92)"
        rgba_entry = f"rgba({int(bg[1:3],16)},{int(bg[3:5],16)},{int(bg[5:7],16)},0.6)"
        
        rasi = f"""/* linux-tweaker glassmorphism rofi theme */
configuration {{
    modi: "drun,run,window";
    show-icons: true;
    icon-theme: "Papirus";
    location: 0;
    fixed-num-lines: true;
    hover-select: true;
    me-select-entry: "";
    me-accept-entry: [MousePrimary];
}}
* {{
    background: {rgba_bg};
    foreground: {fg};
    accent: {accent};
    bg-alt: {rgba_entry};
    border-color: {accent};
    border: 2px;
    border-radius: 16px;
    font: "Inter 13";
}}
window {{
    width: 800px;
    height: 500px;
    border: 2px solid;
    border-color: @border-color;
    border-radius: 16px;
    background-color: @background;
    padding: 20px;
    location: center;
}}
mainbox {{
    background-color: transparent;
    children: [inputbar, listview];
    spacing: 12px;
    padding: 0;
}}
inputbar {{
    background-color: @bg-alt;
    border-radius: 12px;
    padding: 10px 16px;
    children: [prompt, entry];
    spacing: 10px;
}}
prompt {{
    background-color: transparent;
    text-color: @accent;
    font: "Inter 14";
}}
entry {{
    background-color: transparent;
    text-color: @foreground;
    placeholder: "Search...";
    placeholder-color: rgba({int(fg[1:3],16)},{int(fg[3:5],16)},{int(fg[5:7],16)},0.4);
    cursor: text;
    font: "Inter 13";
}}
listview {{
    background-color: transparent;
    border: 0;
    spacing: 6px;
    columns: 1;
    lines: 10;
    fixed-height: false;
    dynamic: true;
    cursor: default;
}}
element {{
    background-color: transparent;
    text-color: @foreground;
    border-radius: 10px;
    padding: 8px 12px;
    spacing: 10px;
}}
element-icon {{
    background-color: transparent;
    size: 28px;
}}
element-text {{
    background-color: transparent;
    text-color: inherit;
    vertical-align: 0.5;
}}
element selected {{
    background-color: @accent;
    text-color: {bg};
}}
element selected element-text {{
    text-color: {bg};
}}
element selected element-icon {{
    background-color: transparent;
}}
"""
        rofi_cfg.write_text(rasi)
        print(f"  -> Rofi glassmorphism theme applied: {theme}")

    def _apply_hyprland_theme(self, theme_config: dict):
        """Apply Hyprland-specific theming. Writes full config if none exists."""
        if not theme_config:
            return
        cfg = self._wm_config()
        if not cfg.exists():
            cfg.parent.mkdir(parents=True, exist_ok=True)
            base = self._generate_base_hyprland_config(theme_config)
            cfg.write_text(base)
            print(f"  -> Hyprland full config created")
        else:
            for key, value in theme_config.items():
                self._replace_line(cfg, key, str(value))
            print(f"  -> Hyprland theme applied ({len(theme_config)} settings)")
        try:
            self._run(["hyprctl", "reload"], check=False)
        except FileNotFoundError:
            pass

    def _generate_base_hyprland_config(self, theme_config: dict) -> str:
        """Generate a complete, working Hyprland config with animations and binds."""
        def v(k, default):
            return theme_config.get(k, default)
        accent = v("general:col.active_border", "0xff89b4fa")
        inactive = v("general:col.inactive_border", "0xff313244")
        return f"""# Generated by linux-tweaker
monitor=,preferred,auto,auto
input {{
    kb_layout = us
    follow_mouse = 1
    touchpad:natural_scroll = no
}}
general {{
    gaps_in = {v("general:gaps_in", 5)}
    gaps_out = {v("general:gaps_out", 10)}
    border_size = {v("general:border_size", 2)}
    col.active_border = {accent}
    col.inactive_border = {inactive}
    layout = dwindle
    resize_on_border = true
    extend_border_grab_area = 15
}}
decoration {{
    rounding = {v("decoration:rounding", 10)}
    blur {{
        enabled = {str(v("decoration:blur:enabled", True)).lower()}
        size = {v("decoration:blur:size", 8)}
        passes = {v("decoration:blur:passes", 4)}
        new_optimizations = true
        ignore_opacity = true
    }}
    active_opacity = {v("decoration:active_opacity", 0.95)}
    inactive_opacity = {v("decoration:inactive_opacity", 0.85)}
    shadow {{
        enabled = true
        range = 12
        render_power = 3
        color = 0x66000000
    }}
}}
animations {{
    enabled = true
    bezier = easeOutQuart,0.25,1,0.5,1
    bezier = easeInOutCubic,0.65,0,0.35,1
    bezier = overshot,0.05,0.9,0.1,1.1
    animation = windows, 1, 5, easeOutQuart, popin
    animation = windowsOut, 1, 5, easeOutQuart, popin
    animation = windowsMove, 1, 5, easeOutQuart, slide
    animation = border, 1, 8, easeOutQuart
    animation = borderangle, 1, 20, easeInOutCubic, loop
    animation = fade, 1, 5, easeOutQuart
    animation = fadeDim, 1, 5, easeOutQuart
    animation = workspaces, 1, 6, easeOutQuart, slide
    animation = specialWorkspace, 1, 5, easeOutQuart, slidevert
}}
dwindle {{
    pseudotile = true
    preserve_split = true
    force_split = 2
}}
master {{
    new_status = master
    new_on_top = true
}}
misc {{
    force_default_wallpaper = 0
    disable_hyprland_logo = true
    disable_splash_rendering = true
    mouse_move_enables_dpms = true
    key_press_enables_dpms = true
    background_color = 0x111111
}}
windowrulev2 = opacity 0.95 0.85, class:^(kitty|alacritty|wezterm)$
windowrulev2 = opacity 0.90 0.80, class:^(discord|webcord|vesktop)$
windowrulev2 = opacity 0.90 0.80, class:^(Spotify|spotify)$
windowrulev2 = float, class:^(pavucontrol)$
windowrulev2 = float, class:^(blueman-manager)$
windowrulev2 = float, title:^(Picture-in-Picture)$
windowrulev2 = pin, title:^(Picture-in-Picture)$
$mod = SUPER
bind = $mod, Return, exec, kitty
bind = $mod, Q, killactive,
bind = $mod SHIFT, M, exit,
bind = $mod, V, togglefloating,
bind = $mod, R, exec, rofi -show drun
bind = $mod, E, exec, thunar
bind = $mod, L, exec, hyprlock
bind = $mod, F, fullscreen, 0
bind = $mod SHIFT, F, fullscreen, 1
bind = $mod, left, movefocus, l
bind = $mod, right, movefocus, r
bind = $mod, up, movefocus, u
bind = $mod, down, movefocus, d
bind = $mod SHIFT, left, movewindow, l
bind = $mod SHIFT, right, movewindow, r
bind = $mod SHIFT, up, movewindow, u
bind = $mod SHIFT, down, movewindow, d
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
bind = $mod, mouse_down, workspace, e+1
bind = $mod, mouse_up, workspace, e-1
bindm = $mod, mouse:272, movewindow
bindm = $mod, mouse:273, resizewindow
exec-once = waybar &
exec-once = swww init || true
"""

    def _apply_dotfiles(self, dotfiles: dict) -> bool:
        """Clone a dotfiles repo and apply its configs."""
        repo_url = dotfiles.get("repo", "")
        if not repo_url:
            return False
        branch = dotfiles.get("branch", "main")
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        clone_dir = self.backup_dir / f"dotfiles_{repo_name}"
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        print(f"  -> Cloning dotfiles...")
        r = self._run(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(clone_dir)], check=False)
        if r.returncode != 0:
            print("  -> FAILED to clone dotfiles")
            return False
        deps = dotfiles.get("dependencies", [])
        if deps:
            missing = []
            for dep in deps:
                try:
                    self._run([dep, "--version"], check=False)
                except FileNotFoundError:
                    missing.append(dep)
            if missing:
                print(f"  -> WARNING: Missing deps for this rice: {', '.join(missing)}")
        for src, dest in dotfiles.get("config_paths", {}).items():
            sp = clone_dir / src
            dp = Path(dest).expanduser()
            if not sp.exists():
                print(f"  -> SKIP: {src} not found in cloned repo")
                continue
            if dp.exists():
                bp = self.backup_dir / f"dotfiles_backup_{dp.name}"
                if bp.exists():
                    if bp.is_dir():
                        shutil.rmtree(bp)
                    else:
                        bp.unlink()
                if dp.is_dir():
                    shutil.copytree(dp, bp)
                else:
                    bp.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dp, bp)
            if dp.exists():
                try:
                    if dp.is_dir():
                        shutil.rmtree(dp)
                    else:
                        dp.unlink()
                except (shutil.Error, OSError) as e:
                    print(f"[{self.wm.title()}] Failed to remove {dp}: {e}")
            if sp.is_dir():
                shutil.copytree(sp, dp)
            else:
                dp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, dp)
            print(f"  -> Applied config: {src} -> {dest}")
        script = dotfiles.get("install_script", "")
        if script:
            sp = clone_dir / script
            if sp.exists():
                stat_mode = sp.stat().st_mode
                if not stat_mode & 0o111:
                    sp.chmod(stat_mode | 0o755)
                print(f"  -> Running install script: {script}")
                subprocess.run([str(sp)], capture_output=True, text=True, check=False, cwd=str(clone_dir))
        print("  -> Dotfiles applied!")
        self._dotfiles_applied = True
        return True

    def apply_preset(self, preset: Preset) -> bool:
        print(f"[{self.wm.title()}] Ricing with preset '{preset.name}' ...", flush=True)
        sys.stdout.flush()
        backup_id = self.backup_current()

        try:
            # 0. Apply dotfiles repo if specified
            dotfiles = preset.get_setting("hyprland.dotfiles", {})
            if dotfiles:
                if not self._apply_dotfiles(dotfiles):
                    print(f"[{self.wm.title()}] WARNING: Dotfiles apply failed, continuing...", flush=True)
                    sys.stdout.flush()

            resources = preset.get_setting("hyprland.resources", {})
            hyprland_theme = preset.get_setting("hyprland.theme", {})

            # 1. Install fonts
            font_urls = resources.get("fonts", [])
            if font_urls:
                count = self._install_fonts(font_urls, self.backup_dir)
                print(f"  -> {count} font(s) installed")

            # 2. Install icon theme
            icon = preset.themes.get("icon")
            icon_url = resources.get("icon-url", "")
            if icon and icon_url:
                self._install_icon_theme(icon, icon_url)

            # 3. Install GTK theme
            gtk = preset.themes.get("gtk") or preset.get_setting("hyprland.gtk-theme")
            theme_url = resources.get("theme-url", "")
            if gtk and theme_url:
                self._install_theme(gtk, theme_url)

            # 4. Install cursor theme
            cursor = preset.themes.get("cursor")
            cursor_url = resources.get("cursor-url", "")
            if cursor and cursor_url:
                self._install_cursor_theme(cursor, cursor_url)

            # 5. Apply Hyprland theme (borders, gaps, rounding, etc.)
            if hyprland_theme:
                self._apply_hyprland_theme(hyprland_theme)

            # 6. Wallpaper
            if preset.wallpaper:
                self._apply_wallpaper(preset.wallpaper)

            # 7. Waybar style
            waybar = preset.get_setting("hyprland.waybar-style")
            waybar_url = resources.get("waybar-style-url", "")
            if waybar:
                self._apply_waybar_theme(waybar, waybar_url, hyprland_theme)

            # 8. Rofi theme
            rofi = preset.get_setting("hyprland.rofi-theme")
            rofi_url = resources.get("rofi-theme-url", "")
            if rofi:
                self._apply_rofi_theme(rofi, rofi_url, hyprland_theme)

            # 9. GTK theme (via gsettings if available, or write to ~/.config/gtk-3.0/settings.ini)
            if gtk:
                try:
                    self._run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", gtk], check=False)
                except FileNotFoundError:
                    pass
                gtk_ini = self.config_dir / "gtk-3.0" / "settings.ini"
                gtk_ini.parent.mkdir(parents=True, exist_ok=True)
                if gtk_ini.exists():
                    self._replace_line(gtk_ini, "gtk-theme-name", gtk)
                else:
                    gtk_ini.write_text(f"[Settings]\ngtk-theme-name={gtk}\n")
                print(f"  -> GTK Theme: {gtk}")

            # 10. Icon theme
            if icon:
                try:
                    self._run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icon], check=False)
                except FileNotFoundError:
                    pass
                print(f"  -> Icon Theme: {icon}")

            # 11. Cursor theme (via gsettings)
            if cursor:
                try:
                    self._run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", cursor], check=False)
                except FileNotFoundError:
                    pass
                print(f"  -> Cursor Theme: {cursor}")

            # 12. Font
            font = preset.themes.get("font")
            if font:
                try:
                    self._run(["gsettings", "set", "org.gnome.desktop.interface", "font-name", font], check=False)
                except FileNotFoundError:
                    pass
                print(f"  -> Font: {font}")

            print(f"\n[{self.wm.title()}] Done. Backup ID: {backup_id}", flush=True)
            print(f"[{self.wm.title()}] NOTE: Reload Hyprland (Mod+Shift+R) for full effect.", flush=True)
            sys.stdout.flush()
            return True
        except Exception as e:
            print(f"\n[{self.wm.title()}] ERROR: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            return False

    def preview_preset(self, preset: Preset) -> PreviewResult:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"{self.wm.title()} Preview: {preset.name}")
        table.add_column("Setting", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")

        cfg = self._wm_config()
        hyprland_theme = preset.get_setting("hyprland.theme", {})

        table.add_row("Wallpaper", "—", preset.wallpaper or "N/A")
        table.add_row("GTK Theme", "—", preset.themes.get("gtk") or "N/A")
        table.add_row("Icon Theme", "—", preset.themes.get("icon") or "N/A")
        table.add_row("Cursor Theme", "—", preset.themes.get("cursor") or "N/A")
        table.add_row("Font", "—", preset.themes.get("font") or "N/A")
        table.add_row("Waybar Style", "—", preset.get_setting("hyprland.waybar-style") or "N/A")
        table.add_row("Rofi Theme", "—", preset.get_setting("hyprland.rofi-theme") or "N/A")

        if hyprland_theme:
            for key, value in list(hyprland_theme.items())[:5]:
                current = self._read_config_value(cfg, key)
                table.add_row(key, current, str(value))
            if len(hyprland_theme) > 5:
                table.add_row("...", f"+{len(hyprland_theme)-5} more", "...")

        console.print(table)
        changes = self._calculate_changes(preset)
        console.print(f"\n[yellow]{len(changes)} changes will be applied[/yellow]")
        return PreviewResult(changes=changes)

    def backup_current(self) -> str:
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"{self.wm}_{bid}"
        dest.mkdir(parents=True, exist_ok=True)

        files_to_backup = [
            (self._wm_config(), f"{self.wm}.conf"),
            (self.config_dir / "waybar" / "style.css", "waybar_style.css"),
            (self.config_dir / "waybar" / "config", "waybar_config"),
            (self.config_dir / "waybar" / "config.jsonc", "waybar_config.jsonc"),
            (self.config_dir / "rofi" / "config.rasi", "rofi_config.rasi"),
            (self.config_dir / "gtk-3.0" / "settings.ini", "gtk3_settings.ini"),
            (self.config_dir / "gtk-4.0" / "settings.ini", "gtk4_settings.ini"),
        ]
        for src, name in files_to_backup:
            if src.exists():
                shutil.copy2(src, dest / name)

        print(f"[{self.wm.title()}] Backup saved: {bid}")
        return bid

    def restore_backup(self, backup_id: str) -> bool:
        src = self.backup_dir / f"{self.wm}_{backup_id}"
        if not src.exists():
            print(f"[{self.wm.title()}] Backup {backup_id} not found")
            return False

        mappings = [
            (src / f"{self.wm}.conf", self._wm_config()),
            (src / "waybar_style.css", self.config_dir / "waybar" / "style.css"),
            (src / "waybar_config", self.config_dir / "waybar" / "config"),
            (src / "waybar_config.jsonc", self.config_dir / "waybar" / "config.jsonc"),
            (src / "rofi_config.rasi", self.config_dir / "rofi" / "config.rasi"),
            (src / "gtk3_settings.ini", self.config_dir / "gtk-3.0" / "settings.ini"),
            (src / "gtk4_settings.ini", self.config_dir / "gtk-4.0" / "settings.ini"),
        ]
        try:
            for s, d in mappings:
                if s.exists():
                    d.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, d)
            print(f"[{self.wm.title()}] Backup {backup_id} restored")
            if self.wm == "hyprland":
                try:
                    self._run(["hyprctl", "reload"], check=False)
                except FileNotFoundError:
                    pass
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            print(f"[{self.wm.title()}] Restore failed: {e}")
            return False

    def _get_current_setting(self, key: str) -> str:
        if key == "hyprland.waybar-style":
            waybar_css = self.config_dir / "waybar" / "style.css"
            return waybar_css.name if waybar_css.exists() else "default"
        elif key == "hyprland.rofi-theme":
            rofi_cfg = self.config_dir / "rofi" / "config.rasi"
            if rofi_cfg.exists():
                for line in rofi_cfg.read_text().splitlines():
                    if "@theme" in line:
                        return line.split("\"")[1] if '"' in line else "default"
            return "default"
        return "unknown"

    def reset_configs(self):
        """Backup and wipe current WM configs, create clean defaults."""
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub = self.backup_dir / f"{self.wm}_reset_{bid}"
        sub.mkdir(parents=True, exist_ok=True)

        # Only reset configs for the currently detected WM
        if self.wm == "hyprland":
            paths = [
                self.config_dir / "hypr" / "hyprland.conf",
                self.config_dir / "waybar" / "style.css",
                self.config_dir / "waybar" / "config",
                self.config_dir / "waybar" / "config.jsonc",
                self.config_dir / "rofi" / "config.rasi",
            ]
            for p in paths:
                if p.exists():
                    try:
                        shutil.copy2(p, sub / p.name)
                        p.unlink()
                    except (shutil.Error, OSError) as e:
                        print(f"[Hyprland] Failed to backup {p.name}: {e}")
            (self.config_dir / "hypr").mkdir(parents=True, exist_ok=True)
            clean_conf = self.config_dir / "hypr" / "hyprland.conf"
            clean_conf.write_text("monitor=,preferred,auto,auto\ngeneral {\n    gaps_in = 5\n    gaps_out = 10\n    border_size = 2\n}\n")
            print(f"[{self.wm.title()}] Reset Hyprland configs. Backup: {bid}")

        elif self.wm == "sway":
            paths = [
                self.config_dir / "sway" / "config",
                self.config_dir / "waybar" / "style.css",
                self.config_dir / "waybar" / "config",
                self.config_dir / "rofi" / "config.rasi",
            ]
            for p in paths:
                if p.exists():
                    try:
                        shutil.copy2(p, sub / p.name)
                        p.unlink()
                    except (shutil.Error, OSError) as e:
                        print(f"[Sway] Failed to backup {p.name}: {e}")
            (self.config_dir / "sway").mkdir(parents=True, exist_ok=True)
            clean_conf = self.config_dir / "sway" / "config"
            clean_conf.write_text("# Default Sway config\noutput * bg #1a1a1a solid_color\n")
            print(f"[{self.wm.title()}] Reset Sway configs. Backup: {bid}")

        elif self.wm == "i3":
            paths = [
                self.config_dir / "i3" / "config",
                self.config_dir / "polybar" / "config",
                self.config_dir / "rofi" / "config.rasi",
            ]
            for p in paths:
                if p.exists():
                    try:
                        shutil.copy2(p, sub / p.name)
                        p.unlink()
                    except (shutil.Error, OSError) as e:
                        print(f"[i3] Failed to backup {p.name}: {e}")
            (self.config_dir / "i3").mkdir(parents=True, exist_ok=True)
            clean_conf = self.config_dir / "i3" / "config"
            clean_conf.write_text("# Default i3 config\n")
            print(f"[{self.wm.title()}] Reset i3 configs. Backup: {bid}")
