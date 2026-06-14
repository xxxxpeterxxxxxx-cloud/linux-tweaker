"""
GNOME Theme Engine
Real ricing: installs extensions, themes, icons, fonts, and configures
GNOME Shell layout via gsettings. No root required.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from theme_engine import Preset, PreviewResult, ThemeEngine


class GnomeThemeEngine(ThemeEngine):
    """Theme engine for GNOME. Installs extensions, themes, icons, fonts, and configures layout."""

    SCHEMA_INTERFACE = "org.gnome.desktop.interface"
    SCHEMA_BACKGROUND = "org.gnome.desktop.background"
    SCHEMA_PERIPHERALS = "org.gnome.desktop.peripherals"
    SCHEMA_SHELL = "org.gnome.shell"
    SCHEMA_EXTENSIONS = "org.gnome.shell.extensions"

    def __init__(self):
        super().__init__()
        self.themes_dir = Path.home() / ".themes"
        self.icons_dir = Path.home() / ".icons"
        self.extensions_dir = Path.home() / ".local" / "share" / "gnome-shell" / "extensions"
        self.fonts_dir = Path.home() / ".local" / "share" / "fonts"
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in (self.themes_dir, self.icons_dir, self.extensions_dir, self.fonts_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ── gsettings helpers ─────────────────────────────────────────────

    def _gget(self, schema: str, key: str) -> str:
        try:
            r = self._run(["gsettings", "get", schema, key], check=True)
            return r.stdout.strip().strip("'\"")
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return "unknown"

    def _gset(self, schema: str, key: str, value: str) -> bool:
        try:
            # Convert Python booleans to lowercase for gsettings
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, str):
                # If string is "True" or "False" (from JSON), convert to lowercase
                if value in ["True", "False"]:
                    value = value.lower()
            self._run(["gsettings", "set", schema, key, str(value)], check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            print(f"[GNOME] Failed to set {key}: {e}")
            return False

    def _dset(self, path: str, key: str, value: str) -> bool:
        """Set a dconf path directly. Useful for extension settings."""
        try:
            self._run(["dconf", "write", f"{path}/{key}", f"'{value}'"], check=False)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    # ── Resource installation ─────────────────────────────────────────

    def _install_theme(self, name: str, url: str) -> bool:
        """Download and extract a GTK theme to ~/.themes/."""
        return self._install_theme_asset(name, url, self.themes_dir, "theme")

    def _install_icon_theme(self, name: str, url: str) -> bool:
        """Download and extract an icon theme to ~/.icons/."""
        return self._install_theme_asset(name, url, self.icons_dir, "icons")

    def _install_shell_theme(self, name: str, url: str) -> bool:
        """Download and install a GNOME Shell theme. Requires User Themes extension."""
        return self._install_theme_asset(name, url, self.themes_dir, "shell")

    def _install_extension(self, uuid: str, url: str) -> bool:
        """Download and install a GNOME Shell extension zip to ~/.local/share/gnome-shell/extensions/."""
        ext_dir = self.extensions_dir / uuid
        if ext_dir.exists():
            print(f"  -> Extension '{uuid}' already installed")
            self._enable_extension(uuid)
            return True
        archive = self.backup_dir / f"ext_{uuid}.zip"
        if not self._download_file(url, archive):
            print(f"  -> Failed to download extension {uuid}")
            return False
        ext_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(archive, "r") as z:
                # Check for path traversal attacks
                for member in z.namelist():
                    if ".." in member or member.startswith("/"):
                        print(f"  -> Unsafe path in extension archive: {member}")
                        return False
                z.extractall(ext_dir)
            print(f"  -> Extension installed: {uuid}")
            self._enable_extension(uuid)
            return True
        except (zipfile.BadZipFile, OSError) as e:
            print(f"  -> Failed to extract extension {uuid}: {e}")
            return False

    def _enable_extension(self, uuid: str):
        """Add extension to GNOME's enabled-extensions list."""
        try:
            current = self._gget(self.SCHEMA_SHELL, "enabled-extensions")
            enabled = json.loads(current.replace("'", '"')) if current != "unknown" else []
            if uuid not in enabled:
                enabled.append(uuid)
                self._gset(self.SCHEMA_SHELL, "enabled-extensions", str(enabled).replace("'", '"'))
                print(f"  -> Extension enabled: {uuid}")
        except (json.JSONDecodeError, subprocess.SubprocessError, OSError) as e:
            print(f"  -> Could not enable {uuid}: {e}")

    def _set_shell_theme(self, name: str):
        """Set shell theme via User Themes extension."""
        self._gset(f"{self.SCHEMA_EXTENSIONS}.user-theme", "name", name)

    # ── Preset application ────────────────────────────────────────────

    def apply_preset(self, preset: Preset) -> bool:
        print(f"[GNOME] Ricing with preset '{preset.name}' ...")
        backup_id = self.backup_current()
        ok = True

        resources = preset.get_setting("gnome.resources", {})
        extensions = preset.get_setting("gnome.extensions", {})
        layout = preset.get_setting("gnome.layout", {})

        # 1. Install fonts
        font_urls = resources.get("fonts", [])
        if font_urls:
            count = self._install_fonts(font_urls, self.backup_dir)
            print(f"  -> {count} font(s) installed")

        # 2. Install icon theme
        icon_name = preset.themes.get("icon") or preset.get_setting("gnome.icon-theme")
        icon_url = resources.get("icon-url", "")
        if icon_name and icon_url:
            self._install_icon_theme(icon_name, icon_url)

        # 3. Install GTK theme
        gtk = preset.themes.get("gtk") or preset.get_setting("gnome.gtk-theme")
        theme_url = resources.get("theme-url", "")
        if gtk and theme_url:
            self._install_theme(gtk, theme_url)

        # 4. Install shell theme
        shell_theme = preset.get_setting("gnome.shell-theme")
        shell_url = resources.get("shell-theme-url", "")
        if shell_theme and shell_url:
            self._install_shell_theme(shell_theme, shell_url)
            self._set_shell_theme(shell_theme)

        # 5. Apply gsettings (don't fail entire preset on individual errors)
        for schema, key, value, label in self._collect_keys(preset):
            if not self._gset(schema, key, value):
                print(f"  -> {label}: FAILED (skipped)")
            else:
                print(f"  -> {label}: {value}")

        # 6. Install and configure extensions
        if extensions:
            print("  -> Installing extensions ...")
            for uuid, info in extensions.items():
                url = info.get("url", "") if isinstance(info, dict) else info
                self._install_extension(uuid, url)
                # Configure extension settings if provided (resilient)
                if isinstance(info, dict) and "settings" in info:
                    ext_schema = f"{self.SCHEMA_EXTENSIONS}.{uuid.replace('@', '_').replace('.', '_')}" if "schema" not in info else info["schema"]
                    for skey, sval in info["settings"].items():
                        try:
                            self._gset(ext_schema, skey, str(sval))
                        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
                            print(f"  -> Skipped {skey} for {uuid}: {e}")

        # 7. Configure layout (dock, panel, etc.)
        if layout:
            print("  -> Configuring layout ...")
            for schema_path, settings in layout.items():
                for key, value in settings.items():
                    self._gset(schema_path, key, str(value))

        # 8. Wallpaper
        if preset.wallpaper:
            self._apply_wallpaper(preset.wallpaper)

        print(f"\n[GNOME] Done. Backup ID: {backup_id}")
        print("[GNOME] NOTE: Some changes require a logout/login to take full effect.")
        return ok

    def _collect_keys(self, preset: Preset) -> List[tuple]:
        """Return list of (schema, key, value, label) tuples to apply."""
        keys = []
        themes = preset.themes

        gtk = themes.get("gtk") or preset.get_setting("gnome.gtk-theme")
        if gtk:
            keys.append((self.SCHEMA_INTERFACE, "gtk-theme", gtk, "GTK Theme"))

        icon = themes.get("icon") or preset.get_setting("gnome.icon-theme")
        if icon:
            keys.append((self.SCHEMA_INTERFACE, "icon-theme", icon, "Icon Theme"))

        cursor = themes.get("cursor") or preset.get_setting("gnome.cursor-theme")
        if cursor:
            keys.append((self.SCHEMA_INTERFACE, "cursor-theme", cursor, "Cursor Theme"))

        font = themes.get("font") or preset.get_setting("gnome.font-name")
        if font:
            keys.append((self.SCHEMA_INTERFACE, "font-name", font, "Font"))

        doc_font = preset.get_setting("gnome.document-font")
        if doc_font:
            keys.append((self.SCHEMA_INTERFACE, "document-font-name", doc_font, "Document Font"))

        mono_font = preset.get_setting("gnome.monospace-font")
        if mono_font:
            keys.append((self.SCHEMA_INTERFACE, "monospace-font-name", mono_font, "Mono Font"))

        color_scheme = preset.get_setting("gnome.color-scheme")
        if color_scheme:
            keys.append((self.SCHEMA_INTERFACE, "color-scheme", color_scheme, "Color Scheme"))

        return keys

    def _apply_wallpaper(self, url: str):
        path = self._download_wallpaper(url, self.backup_dir)
        if path:
            local = str(path)
            self._gset(self.SCHEMA_BACKGROUND, "picture-uri", f"file://{local}")
            self._gset(self.SCHEMA_BACKGROUND, "picture-uri-dark", f"file://{local}")
            print(f"  -> Wallpaper: {local}")
        else:
            self._gset(self.SCHEMA_BACKGROUND, "picture-uri", url)
            print(f"  -> Wallpaper: {url}")

    def preview_preset(self, preset: Preset) -> PreviewResult:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"GNOME Preview: {preset.name}")
        table.add_column("Setting", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")

        for schema, key, value, label in self._collect_keys(preset):
            current = self._gget(schema, key)
            table.add_row(label, current, value)

        # Show extensions to install
        extensions = preset.get_setting("gnome.extensions", {})
        if extensions:
            table.add_row("Extensions", f"{len(extensions)} to install", ", ".join(extensions.keys()))

        console.print(table)
        console.print(f"\n[bold]Wallpaper:[/bold] {preset.wallpaper}")
        changes = self._calculate_changes(preset)
        console.print(f"\n[yellow]{len(changes)} changes will be applied[/yellow]")
        return PreviewResult(changes=changes)

    def backup_current(self) -> str:
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.backup_dir / f"gnome_{bid}.json"
        data = {
            "gtk-theme": self._gget(self.SCHEMA_INTERFACE, "gtk-theme"),
            "icon-theme": self._gget(self.SCHEMA_INTERFACE, "icon-theme"),
            "cursor-theme": self._gget(self.SCHEMA_PERIPHERALS, "cursor-theme"),
            "font-name": self._gget(self.SCHEMA_INTERFACE, "font-name"),
            "document-font-name": self._gget(self.SCHEMA_INTERFACE, "document-font-name"),
            "monospace-font-name": self._gget(self.SCHEMA_INTERFACE, "monospace-font-name"),
            "color-scheme": self._gget(self.SCHEMA_INTERFACE, "color-scheme"),
            "picture-uri": self._gget(self.SCHEMA_BACKGROUND, "picture-uri"),
            "enabled-extensions": self._gget(self.SCHEMA_SHELL, "enabled-extensions"),
        }
        path.write_text(json.dumps(data, indent=2))
        print(f"[GNOME] Backup saved: {bid}")
        return bid

    def restore_backup(self, backup_id: str) -> bool:
        path = self.backup_dir / f"gnome_{backup_id}.json"
        if not path.exists():
            print(f"[GNOME] Backup {backup_id} not found")
            return False
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, IOError) as e:
            print(f"[GNOME] Failed to parse backup file: {e}")
            return False
        try:
            for key, value in data.items():
                if key == "enabled-extensions":
                    self._gset(self.SCHEMA_SHELL, key, value)
                else:
                    schema = self.SCHEMA_BACKGROUND if "picture" in key else self.SCHEMA_INTERFACE
                    if "cursor" in key:
                        schema = self.SCHEMA_PERIPHERALS
                    self._gset(schema, key, value)
            print(f"[GNOME] Backup {backup_id} restored")
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            print(f"[GNOME] Restore failed: {e}")
            return False

    def _get_current_setting(self, key: str) -> str:
        if key == "gnome.gtk-theme":
            return self._gget(self.SCHEMA_INTERFACE, "gtk-theme")
        elif key == "gnome.icon-theme":
            return self._gget(self.SCHEMA_INTERFACE, "icon-theme")
        elif key == "gnome.font-name":
            return self._gget(self.SCHEMA_INTERFACE, "font-name")
        elif key == "gnome.color-scheme":
            return self._gget(self.SCHEMA_INTERFACE, "color-scheme")
        return "unknown"

    def reset_configs(self):
        """Backup and reset GNOME settings to defaults."""
        bid = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.backup_dir / f"gnome_{bid}.json"
        data = {
            "gtk-theme": self._gget(self.SCHEMA_INTERFACE, "gtk-theme"),
            "icon-theme": self._gget(self.SCHEMA_INTERFACE, "icon-theme"),
            "cursor-theme": self._gget(self.SCHEMA_PERIPHERALS, "cursor-theme"),
            "font-name": self._gget(self.SCHEMA_INTERFACE, "font-name"),
            "document-font-name": self._gget(self.SCHEMA_INTERFACE, "document-font-name"),
            "monospace-font-name": self._gget(self.SCHEMA_INTERFACE, "monospace-font-name"),
            "color-scheme": self._gget(self.SCHEMA_INTERFACE, "color-scheme"),
            "picture-uri": self._gget(self.SCHEMA_BACKGROUND, "picture-uri"),
            "enabled-extensions": self._gget(self.SCHEMA_SHELL, "enabled-extensions"),
        }
        path.write_text(json.dumps(data, indent=2))
        self._gset(self.SCHEMA_INTERFACE, "gtk-theme", "Adwaita")
        self._gset(self.SCHEMA_INTERFACE, "icon-theme", "Adwaita")
        self._gset(self.SCHEMA_INTERFACE, "font-name", "Sans 11")
        self._gset(self.SCHEMA_INTERFACE, "document-font-name", "Sans 11")
        self._gset(self.SCHEMA_INTERFACE, "monospace-font-name", "Monospace 11")
        self._gset(self.SCHEMA_PERIPHERALS, "cursor-theme", "Adwaita")
        self._gset(self.SCHEMA_INTERFACE, "color-scheme", "default")
        self._gset(self.SCHEMA_BACKGROUND, "picture-uri", "")
        print(f"[GNOME] Reset to defaults. Backup ID: {bid} (restoreable via [5])")
