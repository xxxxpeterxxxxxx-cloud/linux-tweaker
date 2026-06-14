"""
XFCE / MATE Theme Engine
Controls theming via xfconf-query. No root required.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from theme_engine import Preset, PreviewResult, ThemeEngine


class XfceThemeEngine(ThemeEngine):
    """Theme engine for XFCE and MATE."""

    CHANNEL = "xfce4-appearance"

    def __init__(self):
        super().__init__()
        self.themes_dir = Path.home() / ".themes"
        self.icons_dir = Path.home() / ".icons"
        self.fonts_dir = Path.home() / ".local" / "share" / "fonts"
        for d in (self.themes_dir, self.icons_dir, self.fonts_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._check_dependencies()

    def _install_theme(self, name: str, url: str) -> bool:
        if not url:
            return False
        dest = self.themes_dir / name
        if dest.exists():
            print(f"  -> Theme '{name}' already installed")
            return True
        archive = self.backup_dir / f"xfce_theme_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"xfce_theme_{name}_tmp")
        if not extracted:
            return False
        if extracted != dest:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(extracted), str(dest))
        print(f"  -> Theme installed: {name}")
        return True

    def _install_icon_theme(self, name: str, url: str) -> bool:
        if not url:
            return False
        dest = self.icons_dir / name
        if dest.exists():
            print(f"  -> Icon theme '{name}' already installed")
            return True
        archive = self.backup_dir / f"xfce_icons_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"xfce_icons_{name}_tmp")
        if not extracted:
            return False
        if extracted != dest:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(extracted), str(dest))
        print(f"  -> Icon theme installed: {name}")
        return True

    def _install_cursor_theme(self, name: str, url: str) -> bool:
        if not url:
            return False
        dest = self.icons_dir / name
        if dest.exists():
            print(f"  -> Cursor theme '{name}' already installed")
            return True
        archive = self.backup_dir / f"xfce_cursor_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"xfce_cursor_{name}_tmp")
        if not extracted:
            return False
        if extracted != dest:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(extracted), str(dest))
        print(f"  -> Cursor theme installed: {name}")
        return True

    def _check_dependencies(self):
        """Check if xfconf-query is installed. Warn if missing."""
        try:
            self._run(["xfconf-query", "--version"], check=False)
        except FileNotFoundError:
            print(f"[XFCE] WARNING: xfconf-query not found.")
            print(f"[XFCE] Install xfce4-settings package.")

    def _xfget(self, prop: str) -> str:
        try:
            r = self._run(["xfconf-query", "-c", self.CHANNEL, "-p", prop], check=False)
            if r.returncode == 0:
                return r.stdout.strip()
        except FileNotFoundError:
            return "unknown"
        return "unknown"

    def _xfset(self, prop: str, value: str) -> bool:
        try:
            self._run(["xfconf-query", "-c", self.CHANNEL, "-p", prop, "-n", "-t", "string", "-s", value], check=False)
            self._run(["xfconf-query", "-c", self.CHANNEL, "-p", prop, "-s", value], check=True)
            return True
        except Exception as e:
            print(f"[XFCE] Failed to set {prop}: {e}")
            return False

    def _apply_wallpaper(self, url: str):
        path = self._download_wallpaper(url, self.backup_dir)
        wallpaper = str(path) if path else url
        desktop_ch = "xfce4-desktop"
        # Try common monitor paths
        for prop in [
            "/backdrop/screen0/monitor0/image-path",
            "/backdrop/screen0/monitor0/workspace0/last-image",
            "/backdrop/screen0/monitorLVDS-1/workspace0/last-image",
        ]:
            try:
                self._run(["xfconf-query", "-c", desktop_ch, "-p", prop, "-n", "-t", "string", "-s", wallpaper], check=False)
                self._run(["xfconf-query", "-c", desktop_ch, "-p", prop, "-s", wallpaper], check=False)
            except FileNotFoundError:
                pass
        print(f"[XFCE]  -> Wallpaper: {wallpaper}")

    def apply_preset(self, preset: Preset) -> bool:
        print(f"[XFCE] Ricing with preset '{preset.name}' ...")
        backup_id = self.backup_current()
        ok = True

        resources = preset.get_setting("xfce.resources", {})

        # 1. Install fonts
        font_urls = resources.get("fonts", [])
        if font_urls:
            count = self._install_fonts(font_urls, self.backup_dir)
            print(f"  -> {count} font(s) installed")

        # 2. Install icon theme
        icon = preset.themes.get("icon") or preset.get_setting("xfce.icon-theme")
        icon_url = resources.get("icon-url", "")
        if icon and icon_url:
            self._install_icon_theme(icon, icon_url)

        # 3. Install GTK theme
        gtk = preset.themes.get("gtk") or preset.get_setting("xfce.gtk-theme")
        theme_url = resources.get("theme-url", "")
        if gtk and theme_url:
            self._install_theme(gtk, theme_url)

        # 4. Install cursor theme
        cursor = preset.themes.get("cursor") or preset.get_setting("xfce.cursor-theme")
        cursor_url = resources.get("cursor-url", "")
        if cursor and cursor_url:
            self._install_cursor_theme(cursor, cursor_url)

        # 5. Apply settings (don't fail entire preset on individual errors)
        if gtk:
            if not self._xfset("/Net/ThemeName", gtk):
                print(f"  -> GTK Theme: FAILED (skipped)")
            else:
                print(f"  -> GTK Theme: {gtk}")

        if icon:
            if not self._xfset("/Net/IconThemeName", icon):
                print(f"  -> Icon Theme: FAILED (skipped)")
            else:
                print(f"  -> Icon Theme: {icon}")

        if cursor:
            if not self._xfset("/Gtk/CursorThemeName", cursor):
                print(f"  -> Cursor Theme: FAILED (skipped)")
            else:
                print(f"  -> Cursor Theme: {cursor}")

        font = preset.themes.get("font") or preset.get_setting("xfce.font-name")
        if font:
            if not self._xfset("/Net/FontName", font):
                print(f"  -> Font: FAILED (skipped)")
            else:
                print(f"  -> Font: {font}")

        mono = preset.get_setting("xfce.monospace-font")
        if mono:
            self._xfset("/Gtk/MonospaceFontName", mono)
            print(f"  -> Mono Font: {mono}")

        # 6. Wallpaper
        if preset.wallpaper:
            self._apply_wallpaper(preset.wallpaper)

        print(f"\n[XFCE] Done. Backup ID: {backup_id}")
        return ok

    def preview_preset(self, preset: Preset) -> PreviewResult:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"XFCE Preview: {preset.name}")
        table.add_column("Setting", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")

        rows = [
            ("GTK Theme", self._xfget("/Net/ThemeName"),
             preset.themes.get("gtk") or preset.get_setting("xfce.gtk-theme")),
            ("Icon Theme", self._xfget("/Net/IconThemeName"),
             preset.themes.get("icon") or preset.get_setting("xfce.icon-theme")),
            ("Cursor Theme", self._xfget("/Gtk/CursorThemeName"),
             preset.themes.get("cursor") or preset.get_setting("xfce.cursor-theme")),
            ("Font", self._xfget("/Net/FontName"),
             preset.themes.get("font") or preset.get_setting("xfce.font-name")),
            ("Mono Font", self._xfget("/Gtk/MonospaceFontName"),
             preset.get_setting("xfce.monospace-font")),
        ]
        for label, cur, new in rows:
            table.add_row(label, cur, new or "N/A")

        console.print(table)
        console.print(f"\n[bold]Wallpaper:[/bold] {preset.wallpaper}")
        changes = self._calculate_changes(preset)
        console.print(f"\n[yellow]{len(changes)} changes will be applied[/yellow]")
        return PreviewResult(changes=changes)

    def backup_current(self) -> str:
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.backup_dir / f"xfce_{bid}.json"
        data = {
            "gtk_theme": self._xfget("/Net/ThemeName"),
            "icon_theme": self._xfget("/Net/IconThemeName"),
            "cursor_theme": self._xfget("/Gtk/CursorThemeName"),
            "font": self._xfget("/Net/FontName"),
            "mono_font": self._xfget("/Gtk/MonospaceFontName"),
        }
        path.write_text(json.dumps(data, indent=2))
        print(f"[XFCE] Backup saved: {bid}")
        return bid

    def restore_backup(self, backup_id: str) -> bool:
        path = self.backup_dir / f"xfce_{backup_id}.json"
        if not path.exists():
            print(f"[XFCE] Backup {backup_id} not found")
            return False
        try:
            data = json.loads(path.read_text())
            for key, value in data.items():
                if not value:
                    continue
                prop_map = {
                    "gtk_theme": "/Net/ThemeName",
                    "icon_theme": "/Net/IconThemeName",
                    "cursor_theme": "/Gtk/CursorThemeName",
                    "font": "/Net/FontName",
                    "mono_font": "/Gtk/MonospaceFontName",
                }
                prop = prop_map.get(key)
                if prop:
                    self._xfset(prop, value)
            print(f"[XFCE] Backup {backup_id} restored")
            return True
        except Exception as e:
            print(f"[XFCE] Restore failed: {e}")
            return False

    def _get_current_setting(self, key: str) -> str:
        if key == "xfce.gtk-theme":
            return self._xfget("/Net/ThemeName")
        elif key == "xfce.icon-theme":
            return self._xfget("/Net/IconThemeName")
        elif key == "xfce.font-name":
            return self._xfget("/Net/FontName")
        return "unknown"

    def reset_configs(self):
        """Backup and reset XFCE configs to defaults."""
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub = self.backup_dir / f"xfce_reset_{bid}"
        sub.mkdir(parents=True, exist_ok=True)
        
        # Backup current xfconf settings
        backup_data = {
            "gtk_theme": self._xfget("/Net/ThemeName"),
            "icon_theme": self._xfget("/Net/IconThemeName"),
            "cursor_theme": self._xfget("/Gtk/CursorThemeName"),
            "font": self._xfget("/Net/FontName"),
            "mono_font": self._xfget("/Gtk/MonospaceFontName"),
        }
        (sub / "xfconf_backup.json").write_text(json.dumps(backup_data, indent=2))
        
        # Reset to defaults
        self._xfset("/Net/ThemeName", "Adwaita")
        self._xfset("/Net/IconThemeName", "Adwaita")
        self._xfset("/Gtk/CursorThemeName", "Adwaita")
        self._xfset("/Net/FontName", "Sans 11")
        self._xfset("/Gtk/MonospaceFontName", "Monospace 11")
        
        print(f"[XFCE] Reset to defaults. Backup: {bid}")
