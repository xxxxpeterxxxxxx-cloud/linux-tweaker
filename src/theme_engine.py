"""
Theme Engine Base Classes
Abstract base classes for modular desktop theming engines.
"""

import shutil
import subprocess
import tarfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Preset:
    """Represents a visual theme preset."""
    name: str
    description: str
    themes: Dict[str, str]
    wallpaper: str
    settings: Dict[str, Any]

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a nested setting by dot-notation key."""
        value = self.settings
        for k in key.split("."):
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


@dataclass
class PreviewResult:
    """Result of a preview generation."""
    changes: List[Dict[str, str]]
    confirmed: bool = False
    backup_id: Optional[str] = None


class ThemeEngine(ABC):
    """
    Abstract base class for all theme engines.
    Each engine must implement apply, preview, backup, and restore.
    """

    def __init__(self):
        self.backup_dir = self._get_backup_dir()

    @abstractmethod
    def apply_preset(self, preset: Preset) -> bool:
        """Apply a preset. Returns True on success."""
        pass

    @abstractmethod
    def preview_preset(self, preset: Preset) -> PreviewResult:
        """Generate a preview without making changes."""
        pass

    @abstractmethod
    def backup_current(self) -> str:
        """Save current config. Returns a backup ID."""
        pass

    @abstractmethod
    def restore_backup(self, backup_id: str) -> bool:
        """Restore a backup by ID."""
        pass

    def _get_backup_dir(self) -> Path:
        path = Path.home() / ".config" / "linux-tweaker" / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_current_setting(self, key: str) -> str:
        """Get a current setting value. Override per engine."""
        return "unknown"

    def _calculate_changes(self, preset: Preset) -> List[Dict[str, str]]:
        """Compute diff between current state and a preset."""
        changes = []
        for key, new_value in preset.settings.items():
            current = self._get_current_setting(key)
            if current != new_value:
                changes.append({"key": key, "current": current, "new": new_value})
        return changes

    def _run(self, cmd: List[str], check: bool = True, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a shell command safely."""
        kwargs = {"capture_output": True, "text": True, "check": check}
        if cwd:
            kwargs["cwd"] = cwd
        return subprocess.run(cmd, **kwargs)

    def _download_file(self, url: str, dest: Path) -> bool:
        """Download a file via curl or wget. Returns True on success."""
        # Basic URL validation to prevent security issues
        if not url or not isinstance(url, str):
            return False
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Add user-agent to avoid GitHub rate limiting
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        for downloader in (["curl", "-fsSL", "-A", user_agent, "-o", str(dest), url],
                           ["wget", "-q", "-U", user_agent, "-O", str(dest), url]):
            try:
                result = self._run(downloader, check=False)
                if dest.exists() and dest.stat().st_size > 1024:
                    return True
                # If download failed but file exists (partial), remove it
                if dest.exists():
                    dest.unlink()
            except FileNotFoundError:
                continue
        return False

    def _download_wallpaper(self, url: str, dest_dir: Path) -> Optional[Path]:
        """Download a wallpaper to a local path."""
        if not url or url.startswith("/"):
            local = Path(url) if url else None
            return local if local and local.exists() else None
        parts = url.split("/")
        filename = parts[-1].split("?")[0] if parts else "wallpaper"
        if not filename:
            filename = "wallpaper"
        if not filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
            filename += ".jpg"
        dest = dest_dir / filename
        if self._download_file(url, dest):
            return dest
        return None

    def _extract_archive(self, archive: Path, dest_dir: Path) -> Optional[Path]:
        """Extract a .tar.gz, .tar.xz, or .zip to dest_dir. Return top-level dir."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            if archive.suffix == ".zip" or str(archive).endswith(".shell-extension.zip"):
                with zipfile.ZipFile(archive, "r") as z:
                    # Check for path traversal attacks (zip bomb)
                    for member in z.namelist():
                        if ".." in member or member.startswith("/"):
                            print(f"[ThemeEngine] Unsafe path in archive: {member}")
                            return None
                    z.extractall(dest_dir)
            elif ".tar." in archive.name or archive.suffix in (".tar", ".gz", ".xz"):
                with tarfile.open(archive, "r:*") as t:
                    # Check for path traversal attacks
                    for member in t.getmembers():
                        if ".." in member.name or member.name.startswith("/"):
                            print(f"[ThemeEngine] Unsafe path in archive: {member.name}")
                            return None
                    t.extractall(dest_dir)
            else:
                return None
        except (zipfile.BadZipFile, tarfile.TarError, OSError) as e:
            print(f"[ThemeEngine] Extraction failed for {archive}: {e}")
            return None
        # Return the first sub-directory that was created
        for item in dest_dir.iterdir():
            if item.is_dir():
                return item
        return dest_dir

    def _install_theme_from_repo(self, name: str, repo_url: str, install_cmd: List[str], dest_dir: Path) -> bool:
        """Download repo tarball and run an install script to install a theme."""
        import os
        dest = dest_dir / name
        if dest.exists():
            print(f"  -> {name} already installed")
            return True
        # Derive tarball URL from repo URL
        tarball_url = repo_url.replace("https://github.com/", "https://github.com/") + "/archive/refs/heads/main.tar.gz"
        tmp_dir = self.backup_dir / f"repo_{name}_tmp"
        archive = self.backup_dir / f"repo_{name}.tar.gz"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        print(f"  -> Downloading {name} source...")
        if not self._download_file(tarball_url, archive):
            # Fallback to master branch
            tarball_url = repo_url + "/archive/refs/heads/master.tar.gz"
            if not self._download_file(tarball_url, archive):
                print(f"  -> [ERROR] Failed to download source from {repo_url}")
                return False
        extracted = self._extract_archive(archive, tmp_dir)
        if not extracted:
            print(f"  -> [ERROR] Failed to extract source archive")
            return False
        # The extracted dir is the top-level repo dir
        src_dir = extracted
        # Try pre-built release archives first (fast path)
        release_dir = src_dir / "release"
        if release_dir.exists():
            # Find a matching .tar.xz file
            base_name = name.split("-")[0]  # e.g. "Orchis-Green-Dark" -> "Orchis"
            # Try to match the color variant specifically
            color_part = name.split("-")[1].lower() if "-" in name else ""  # "green" from "Orchis-Green-Dark"
            matched = False
            for archive in release_dir.glob("*.tar.xz"):
                archive_name_lower = archive.name.lower()
                # Check if base name AND color part match
                if base_name.lower() in archive_name_lower and (color_part in archive_name_lower or not color_part):
                    print(f"  -> Installing pre-built {archive.name}...")
                    try:
                        with tarfile.open(archive, "r:*") as t:
                            t.extractall(dest_dir)
                        if (dest_dir / name).exists():
                            print(f"  -> {name} installed from release archive")
                            return True
                    except (tarfile.TarError, OSError) as e:
                        print(f"  -> [WARN] Failed to extract release archive: {e}")
                    matched = True
                    break
            # Fallback: try to match just the base name (e.g., "Orchis.tar.xz" for "Orchis-Blue-Dark")
            if not matched:
                for archive in release_dir.glob("*.tar.xz"):
                    # Handle .tar.xz double extension
                    archive_stem = archive.stem.lower()
                    if archive_stem.endswith(".tar"):
                        archive_stem = archive_stem[:-4]  # Remove ".tar" suffix
                    if archive_stem == base_name.lower():
                        print(f"  -> Installing pre-built {archive.name} (fallback)...")
                        try:
                            with tarfile.open(archive, "r:*") as t:
                                t.extractall(dest_dir)
                            if (dest_dir / name).exists():
                                print(f"  -> {name} installed from release archive")
                                return True
                        except (tarfile.TarError, OSError) as e:
                            print(f"  -> [WARN] Failed to extract release archive: {e}")
                        matched = True
                        break
            if not matched:
                print(f"  -> No matching release archive found, will use install script")
            elif not (dest_dir / name).exists():
                # Archive extracted but specific theme name not found, try install script
                print(f"  -> Release archive extracted but '{name}' not found, trying install script...")
                matched = False
        # Expand ~ in install command args
        expanded_cmd = [os.path.expanduser(arg) for arg in install_cmd]
        print(f"  -> Running install script for {name}...")
        r = self._run(expanded_cmd, check=False, cwd=str(src_dir))
        if r.returncode != 0:
            print(f"  -> [WARN] Install script may have had issues, checking if theme exists...")
        # Verify the theme was installed
        if dest.exists():
            print(f"  -> {name} installed from repo")
            return True
        # Also check common install locations
        for alt_dir in [Path.home() / ".themes", Path.home() / ".icons", Path.home() / ".local/share/icons", Path.home() / ".local/share/themes"]:
            if (alt_dir / name).exists():
                print(f"  -> {name} installed to {alt_dir}")
                return True
        print(f"  -> [WARN] Could not verify {name} installation")
        return False

    def _install_fonts(self, font_urls: List[str], dest_dir: Path) -> int:
        """Download fonts (or font archives) and install to ~/.local/share/fonts/. Returns count installed."""
        font_dir = Path.home() / ".local" / "share" / "fonts"
        font_dir.mkdir(parents=True, exist_ok=True)
        installed = 0
        for url in font_urls:
            parts = url.split("/")
            filename = parts[-1].split("?")[0] if parts else ""
            if not filename:
                continue
            dest = dest_dir / filename
            if not self._download_file(url, dest):
                continue
            # If it's a zip containing fonts, extract font files into font_dir
            if filename.endswith(".zip"):
                try:
                    tmp_extract = dest_dir / f"_font_extract_{filename.replace('.', '_')}"
                    tmp_extract.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(dest, "r") as z:
                        for member in z.namelist():
                            if member.lower().endswith((".ttf", ".otf", ".woff2")):
                                z.extract(member, tmp_extract)
                                extracted_file = tmp_extract / member
                                if extracted_file.exists():
                                    target = font_dir / extracted_file.name
                                    shutil.copy2(str(extracted_file), str(target))
                                    installed += 1
                                    print(f"  -> Font installed: {extracted_file.name}")
                    shutil.rmtree(tmp_extract)
                except (zipfile.BadZipFile, OSError) as e:
                    print(f"  -> Font zip extraction failed: {e}")
                finally:
                    if dest.exists():
                        dest.unlink()
            elif filename.endswith((".ttf", ".otf", ".woff2")):
                target = font_dir / filename
                if target.exists():
                    installed += 1
                    continue
                shutil.copy2(str(dest), str(target))
                installed += 1
                print(f"  -> Font installed: {filename}")
        if installed:
            self._run(["fc-cache", "-f"], check=False)
        return installed

    def _install_theme_asset(self, name: str, url: str, dest_dir: Path, asset_type: str = "theme") -> bool:
        """Generic method to install theme assets (themes, icons, cursors)."""
        if not url:
            return False
        dest = dest_dir / name
        if dest.exists():
            print(f"  -> {asset_type.capitalize()} '{name}' already installed")
            return True
        # Preserve original file extension from URL
        url_path = url.split("?")[0]
        suffix = Path(url_path).suffix or ".zip"
        archive = self.backup_dir / f"{asset_type}_{name}{suffix}"
        if not self._download_file(url, archive):
            print(f"  -> [ERROR] Failed to download {asset_type} from {url}")
            return False
        tmp_dir = self.backup_dir / f"{asset_type}_{name}_tmp"
        extracted = self._extract_archive(archive, tmp_dir)
        if not extracted:
            print(f"  -> [ERROR] Failed to extract {asset_type} archive")
            return False
        try:
            if extracted != dest:
                if dest.exists():
                    shutil.rmtree(dest)
                try:
                    shutil.move(str(extracted), str(dest))
                except (shutil.Error, OSError) as e:
                    print(f"[ThemeEngine] Failed to move {asset_type}: {e}")
                    return False
            print(f"  -> {asset_type.capitalize()} installed: {name}")
            return True
        finally:
            # Clean up temporary directory
            if tmp_dir.exists():
                try:
                    shutil.rmtree(tmp_dir)
                except (shutil.Error, OSError):
                    pass


class GenericThemeEngine(ThemeEngine):
    """Fallback engine for unknown DEs/Wms — preview-only, no changes."""

    def apply_preset(self, preset: Preset) -> bool:
        print(f"[Generic] Cannot apply '{preset.name}' — unknown desktop environment")
        return False

    def preview_preset(self, preset: Preset) -> PreviewResult:
        print(f"[Generic] Preview for '{preset.name}':")
        print(f"  GTK theme : {preset.themes.get('gtk', 'N/A')}")
        print(f"  Icon theme: {preset.themes.get('icon', 'N/A')}")
        print(f"  Font      : {preset.themes.get('font', 'N/A')}")
        print(f"  Wallpaper : {preset.wallpaper}")
        return PreviewResult(changes=[])

    def backup_current(self) -> str:
        return "generic"

    def restore_backup(self, backup_id: str) -> bool:
        print(f"[Generic] Cannot restore backup '{backup_id}'")
        return False
