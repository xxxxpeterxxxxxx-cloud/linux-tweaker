# Linux Tweaker v2.0.0

A robust, secure Linux desktop configuration tool with zero-crash policy and comprehensive error handling.

## Features

- **3 Preset Types** — GNOME-quality Hyprland, Minimal Hyprland, Productivity-focused Hyprland
- **Auto-Backup** — Always backs up your config before applying changes with timestamps
- **Interactive TUI** — Rich terminal UI powered by rich library for easy navigation
- **Zero-Crash Policy** — All operations wrapped in try/except blocks for graceful error handling
- **Security Hardened** — Path traversal protection, URL validation, secure file permissions
- **Partial Failure Recovery** — Continues operation even if some steps fail
- **No Root Required** — Works on immutable systems like Fedora Silverblue
- **Comprehensive Testing** — 14 automated tests (8 integration + 6 unit)

## Install

### Manual Install

```bash
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run directly
python3 app.py
```

### Requirements

- Python 3.8+
- rich (pip install rich)
- git, curl
- Flatpak (for app installation)
- Hyprland (for config application)

## Usage

### Interactive Mode

```bash
python3 app.py
```

Launches a TUI with:
- System status display
- Preset application menu
- Backup management
- System health check

### Running Tests

```bash
# Run integration tests
python3 test_app.py

# Run unit tests
python3 test_unit.py

# Run all tests
python3 test_app.py && python3 test_unit.py
```

## Presets

| Preset | Description | Best For |
|--------|-------------|----------|
| GNOME-quality Hyprland | Full-featured with essential apps | Daily use, complete setup |
| Minimal Hyprland | Bare essentials only | Minimalist setups |
| Productivity Hyprland | Productivity-focused apps and configs | Work environments |

## What Each Preset Does

### Apps (Optional)
- Installs Flatpak applications for communication, productivity, media, utilities
- Includes Firefox, LibreOffice, Discord, Telegram, MPV, GIMP, Inkscape, Blender, etc.

### Configs
- **Hyprland**: Optimized config with animations and blur
- **Waybar**: Glassmorphism CSS with modules
- **Rofi**: App launcher with Catppuccin theme
- **Wallpapers**: Downloads and applies wallpapers

## Backup & Restore

Every preset application automatically creates a backup with timestamp. Backups are stored in `~/.config/linux-tweaker/backups/`.

The backup system includes:
- Timestamped backups (format: `filename_YYYYMMDD_HHMMSS`)
- Backup history tracking
- One-click restore functionality
- Secure file permissions

## Architecture

Linux Tweaker v2.0.0 is built with a modular architecture:

- **SystemChecker**: Validates system dependencies and window manager
- **FileManager**: Handles file operations with automatic backup
- **UIBuilder**: Provides rich TUI interface
- **PackageManager**: Manages Flatpak, AppImage, and local binary installations
- **ConfigManager**: Applies Hyprland, Waybar, Rofi, and wallpaper configurations
- **PresetApplicationManager**: Coordinates app and config application

## Troubleshooting

### Tests fail
- Ensure all dependencies are installed: `pip install rich`
- Check Python version: `python3 --version` (requires 3.8+)
- Run tests individually to identify issues

### Config application fails
- Check if running on Hyprland (configs are Hyprland-specific)
- Verify write permissions: `~/.config/hypr/` and `~/.config/waybar/`
- Check backup directory: `~/.config/linux-tweaker/backups/`
- Review error messages in test output

### Flatpak installation fails
- Verify Flatpak is installed: `flatpak --version`
- Check Flatpak is properly configured: `flatpak remotes`
- Ensure sufficient disk space (100MB+ required)

## Development

```bash
# Clone repository
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py

# Run tests
python3 test_app.py
python3 test_unit.py
```

## Security

Linux Tweaker v2.0.0 includes security hardening:
- Path traversal protection in all file operations
- URL validation for downloads
- Git URL scheme validation (git, https, ssh only)
- Script execution validation (only within dotfiles directory)
- Secure file permissions (0o600 for files, 0o700 for directories)
- File size limits (100MB max)
- Input validation for all public methods

## License

MIT
