"""
KDE Plasma Theme Engine
Controls Plasma theming via kwriteconfig6 and CLI tools. No root required.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from theme_engine import Preset, PreviewResult, ThemeEngine


class PlasmaThemeEngine(ThemeEngine):
    """Theme engine for KDE Plasma 5 and 6."""

    CFG_KDEGLOBALS = str(Path.home() / ".config" / "kdeglobals")
    CFG_KCMFONTS = str(Path.home() / ".config" / "kcmfonts")
    CFG_PLASMARC = str(Path.home() / ".config" / "plasmarc")

    def __init__(self):
        super().__init__()
        self.themes_dir = Path.home() / ".local" / "share" / "themes"
        self.icons_dir = Path.home() / ".local" / "share" / "icons"
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
        archive = self.backup_dir / f"plasma_theme_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"plasma_theme_{name}_tmp")
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
        archive = self.backup_dir / f"plasma_icons_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"plasma_icons_{name}_tmp")
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
        archive = self.backup_dir / f"plasma_cursor_{name}.zip"
        if not self._download_file(url, archive):
            return False
        extracted = self._extract_archive(archive, self.backup_dir / f"plasma_cursor_{name}_tmp")
        if not extracted:
            return False
        if extracted != dest:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(extracted), str(dest))
        print(f"  -> Cursor theme installed: {name}")
        return True

    def _check_dependencies(self):
        """Check if required KDE tools are installed. Warn if missing."""
        deps = ["kwriteconfig6", "kreadconfig6"]
        optional = ["lookandfeeltool", "plasma-apply-globaltheme", "plasma-apply-wallpaperimage"]
        
        missing = []
        for dep in deps:
            try:
                self._run([dep, "--version"], check=False)
            except FileNotFoundError:
                missing.append(dep)
        
        optional_missing = []
        for dep in optional:
            try:
                self._run([dep, "--version"], check=False)
            except FileNotFoundError:
                optional_missing.append(dep)
        
        if missing:
            print(f"[Plasma] WARNING: Missing required tools: {', '.join(missing)}")
            print(f"[Plasma] Install kde-config-scripts package.")
        if optional_missing:
            print(f"[Plasma] NOTE: Optional tools missing: {', '.join(optional_missing)}")
            print(f"[Plasma] Some features may not work.")

    def _kwrite(self, file: str, group: str, key: str, value: str) -> bool:
        """Write a KDE config value via kwriteconfig6 (or kwriteconfig5)."""
        for binary in ("kwriteconfig6", "kwriteconfig5"):
            try:
                self._run([binary, "--file", file, "--group", group, "--key", key, value], check=True)
                return True
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"[Plasma] Failed to write {key}: {e}")
                return False
        print("[Plasma] kwriteconfig not found — is KDE installed?")
        return False

    def _kread(self, file: str, group: str, key: str) -> str:
        """Read a KDE config value."""
        for binary in ("kreadconfig6", "kreadconfig5"):
            try:
                r = self._run([binary, "--file", file, "--group", group, "--key", key], check=False)
                if r.returncode == 0:
                    return r.stdout.strip()
            except FileNotFoundError:
                continue
        return "unknown"

    def _apply_global_theme(self, name: str) -> bool:
        """Try to apply a KDE global theme."""
        for cmd in (["lookandfeeltool", "--apply", name],
                    ["plasma-apply-globaltheme", name]):
            try:
                self._run(cmd, check=True)
                return True
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return False

    def _apply_wallpaper(self, url: str) -> bool:
        """Apply wallpaper via kde cli if available."""
        path = self._download_wallpaper(url, self.backup_dir)
        wallpaper = str(path) if path else url
        for cmd in (["plasma-apply-wallpaperimage", wallpaper],
                    ["kwriteconfig6", "--file", str(Path.home() / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"),
                     "--group", "Containments", "--group", "1", "--group", "Wallpaper",
                     "--group", "org.kde.image", "--key", "Image", wallpaper]):
            try:
                self._run(cmd, check=False)
            except FileNotFoundError:
                continue
        return True

    def apply_preset(self, preset: Preset) -> bool:
        print(f"[Plasma] Ricing with preset '{preset.name}' ...")
        backup_id = self.backup_current()
        ok = True

        resources = preset.get_setting("kde.resources", {})

        # 1. Install fonts
        font_urls = resources.get("fonts", [])
        if font_urls:
            count = self._install_fonts(font_urls, self.backup_dir)
            print(f"  -> {count} font(s) installed")

        # 2. Install icon theme
        icon = preset.themes.get("icon") or preset.get_setting("kde.icon-theme")
        icon_url = resources.get("icon-url", "")
        if icon and icon_url:
            self._install_icon_theme(icon, icon_url)

        # 3. Install GTK theme
        gtk = preset.themes.get("gtk") or preset.get_setting("kde.gtk-theme")
        theme_url = resources.get("theme-url", "")
        if gtk and theme_url:
            self._install_theme(gtk, theme_url)

        # 4. Install cursor theme
        cursor = preset.themes.get("cursor") or preset.get_setting("kde.cursor-theme")
        cursor_url = resources.get("cursor-url", "")
        if cursor and cursor_url:
            self._install_cursor_theme(cursor, cursor_url)

        # 5. Global theme (Look-and-Feel)
        global_theme = preset.get_setting("kde.global-theme")
        if global_theme and not self._apply_global_theme(global_theme):
            print(f"  -> Global theme '{global_theme}' failed (tool not found)")

        # 6. Plasma widget theme
        plasma_theme = preset.get_setting("kde.plasma-theme")
        if plasma_theme:
            self._kwrite(self.CFG_PLASMARC, "Theme", "name", plasma_theme)
            print(f"  -> Plasma Theme: {plasma_theme}")

        # 7. Color scheme
        color = preset.get_setting("kde.color-scheme")
        if color:
            self._kwrite(self.CFG_KDEGLOBALS, "General", "ColorScheme", color)
            print(f"  -> Color Scheme: {color}")

        # 8. GTK theme
        if gtk:
            self._kwrite(self.CFG_KDEGLOBALS, "General", "Name", gtk)
            print(f"  -> GTK Theme: {gtk}")

        # 9. Icon theme
        if icon:
            self._kwrite(self.CFG_KDEGLOBALS, "Icons", "Theme", icon)
            print(f"  -> Icon Theme: {icon}")

        # 10. Cursor theme
        if cursor:
            self._kwrite(self.CFG_KDEGLOBALS, "General", "cursorTheme", cursor)
            print(f"  -> Cursor Theme: {cursor}")

        # 11. Fonts
        font = preset.themes.get("font") or preset.get_setting("kde.font")
        if font:
            self._kwrite(self.CFG_KDEGLOBALS, "General", "font", font)
            print(f"  -> Font: {font}")

        # 12. Wallpaper
        if preset.wallpaper:
            self._apply_wallpaper(preset.wallpaper)
            print(f"  -> Wallpaper applied")

        print(f"\n[Plasma] Done. Backup ID: {backup_id}")
        return ok

    def preview_preset(self, preset: Preset) -> PreviewResult:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Plasma Preview: {preset.name}")
        table.add_column("Setting", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")

        rows = [
            ("Global Theme", self._kread(self.CFG_KDEGLOBALS, "General", "ColorScheme"),
             preset.get_setting("kde.global-theme")),
            ("Plasma Theme", self._kread(self.CFG_PLASMARC, "Theme", "name"),
             preset.get_setting("kde.plasma-theme")),
            ("Color Scheme", self._kread(self.CFG_KDEGLOBALS, "General", "ColorScheme"),
             preset.get_setting("kde.color-scheme")),
            ("GTK Theme", self._kread(self.CFG_KDEGLOBALS, "General", "Name"),
             preset.themes.get("gtk") or preset.get_setting("kde.gtk-theme")),
            ("Icon Theme", self._kread(self.CFG_KDEGLOBALS, "Icons", "Theme"),
             preset.themes.get("icon") or preset.get_setting("kde.icon-theme")),
            ("Cursor", self._kread(self.CFG_KDEGLOBALS, "General", "cursorTheme"),
             preset.themes.get("cursor") or preset.get_setting("kde.cursor-theme")),
            ("Font", self._kread(self.CFG_KDEGLOBALS, "General", "font"),
             preset.themes.get("font") or preset.get_setting("kde.font")),
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
        path = self.backup_dir / f"plasma_{bid}.json"
        data = {
            "color_scheme": self._kread(self.CFG_KDEGLOBALS, "General", "ColorScheme"),
            "plasma_theme": self._kread(self.CFG_PLASMARC, "Theme", "name"),
            "gtk_theme": self._kread(self.CFG_KDEGLOBALS, "General", "Name"),
            "icon_theme": self._kread(self.CFG_KDEGLOBALS, "Icons", "Theme"),
            "cursor_theme": self._kread(self.CFG_KDEGLOBALS, "General", "cursorTheme"),
            "font": self._kread(self.CFG_KDEGLOBALS, "General", "font"),
        }
        path.write_text(json.dumps(data, indent=2))
        print(f"[Plasma] Backup saved: {bid}")
        return bid

    def restore_backup(self, backup_id: str) -> bool:
        path = self.backup_dir / f"plasma_{backup_id}.json"
        if not path.exists():
            print(f"[Plasma] Backup {backup_id} not found")
            return False
        try:
            data = json.loads(path.read_text())
            self._kwrite(self.CFG_KDEGLOBALS, "General", "ColorScheme", data.get("color_scheme", ""))
            self._kwrite(self.CFG_PLASMARC, "Theme", "name", data.get("plasma_theme", ""))
            self._kwrite(self.CFG_KDEGLOBALS, "General", "Name", data.get("gtk_theme", ""))
            self._kwrite(self.CFG_KDEGLOBALS, "Icons", "Theme", data.get("icon_theme", ""))
            self._kwrite(self.CFG_KDEGLOBALS, "General", "cursorTheme", data.get("cursor_theme", ""))
            self._kwrite(self.CFG_KDEGLOBALS, "General", "font", data.get("font", ""))
            print(f"[Plasma] Backup {backup_id} restored")
            return True
        except Exception as e:
            print(f"[Plasma] Restore failed: {e}")
            return False

    def _get_current_setting(self, key: str) -> str:
        if key == "kde.global-theme":
            return self._kread(self.CFG_KDEGLOBALS, "General", "ColorScheme")
        elif key == "kde.plasma-theme":
            return self._kread(self.CFG_PLASMARC, "Theme", "name")
        elif key == "kde.icon-theme":
            return self._kread(self.CFG_KDEGLOBALS, "Icons", "Theme")
        elif key == "kde.gtk-theme":
            return self._kread(self.CFG_KDEGLOBALS, "General", "Name")
        elif key == "kde.color-scheme":
            return self._kread(self.CFG_KDEGLOBALS, "General", "ColorScheme")
        return "unknown"

    def reset_configs(self):
        """Backup and reset Plasma configs to defaults."""
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub = self.backup_dir / f"plasma_reset_{bid}"
        sub.mkdir(parents=True, exist_ok=True)
        
        # Backup current configs
        for cfg in [self.CFG_KDEGLOBALS, self.CFG_KCMFONTS, self.CFG_PLASMARC]:
            p = Path(cfg)
            if p.exists():
                shutil.copy2(p, sub / p.name)
        
        # Reset to defaults by clearing kdeglobals
        kdeglobals = Path(self.CFG_KDEGLOBALS)
        if kdeglobals.exists():
            kdeglobals.write_text("[General]\n")
        
        print(f"[Plasma] Reset to defaults. Backup: {bid}")
