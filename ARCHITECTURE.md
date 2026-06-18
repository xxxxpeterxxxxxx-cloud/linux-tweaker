# Linux Tweaker v2.0.0 - Architecture Documentation

## Overview

Linux Tweaker v2.0.0 is a modular Python application for configuring Linux desktop environments, specifically Hyprland. The application follows a zero-crash policy with comprehensive error handling and security hardening.

## Design Principles

1. **Zero-Crash Policy**: All operations wrapped in try/except blocks
2. **User-Space Only**: No sudo/root operations required
3. **Backups First**: Automatic backup before any modification
4. **Graceful Errors**: User-friendly error messages with recovery options
5. **Security First**: Input validation, path traversal protection, secure permissions
6. **Modular Architecture**: Independent, testable components

## Module Architecture

### Core Modules

```
app.py (Main Application)
├── SystemChecker (src/system_checker.py)
├── FileManager (src/file_manager.py)
├── UIBuilder (src/ui_builder.py)
├── PackageManager (src/package_manager.py)
├── ConfigManager (src/config_manager.py)
└── PresetApplicationManager (src/preset_application_manager.py)
```

### Module Responsibilities

#### SystemChecker
- **Purpose**: Validate system dependencies and detect window manager
- **Key Methods**:
  - `check_write_permissions()`: Verify config directory is writable
  - `detect_window_manager()`: Identify Hyprland, Sway, i3, GNOME, etc.
  - `check_dependency(command)`: Check if a command is available
  - `check_critical_dependencies()`: Validate all required tools
- **Error Handling**: All methods return status enums, never raise exceptions

#### FileManager
- **Purpose**: Handle file operations with automatic backup
- **Key Methods**:
  - `write_file(path, content, create_backup)`: Write with backup
  - `read_file(path)`: Read with encoding error handling
  - `create_backup(path)`: Create timestamped backup
  - `restore_backup(backup_path, target_path)`: Restore from backup
  - `list_backups()`: List all available backups
- **Security Features**:
  - File size limits (100MB max)
  - Secure permissions (0o600 for files, 0o700 for directories)
  - Path traversal protection
  - Encoding validation (UTF-8)

#### UIBuilder
- **Purpose**: Provide rich TUI interface using rich library
- **Key Methods**:
  - `print_header(title)`: Display application header
  - `print_menu(menu)`: Display interactive menu
  - `get_user_choice(menu)`: Get user input with validation
  - `execute_menu_item(item)`: Execute menu actions
  - `print_info/success/warning/error(msg)`: Display messages
- **Fallback**: Gracefully degrades to basic print if rich unavailable

#### PackageManager
- **Purpose**: Manage Flatpak, AppImage, and local binary installations
- **Key Methods**:
  - `is_flatpak_installed(app_id)`: Check Flatpak installation
  - `install_flatpak(app_id)`: Install single Flatpak
  - `install_flatpak_batch(app_ids)`: Install multiple Flatpaks
  - `install_appimage(url, install_dir)`: Download and install AppImage
  - `install_local_binary(source, dest)`: Copy and set permissions
- **Security Features**:
  - URL validation (scheme and netloc required)
  - Filename sanitization (prevents path traversal)
  - Disk space checks (100MB minimum)
  - Git URL scheme validation (git, https, ssh only)

#### ConfigManager
- **Purpose**: Apply Hyprland, Waybar, Rofi, and wallpaper configurations
- **Key Methods**:
  - `apply_hyprland_config(config)`: Write Hyprland config
  - `apply_waybar_config(config, style)`: Write Waybar config and CSS
  - `apply_rofi_config(config, theme)`: Write Rofi config and theme
  - `apply_wallpaper(url)`: Download and apply wallpaper
  - `clone_repo(repo_url, dest)`: Clone git repository
  - `apply_dotfiles(repo_url)`: Apply dotfiles from repository
- **Security Features**:
  - URL validation for downloads
  - Git URL scheme validation
  - Script execution validation (only within dotfiles directory)
  - Chmod error handling

#### PresetApplicationManager
- **Purpose**: Coordinate app and config application for presets
- **Key Methods**:
  - `apply_preset(preset_type, install_apps, apply_configs)`: Apply preset
  - `get_progress()`: Get progress messages
  - `get_errors()`: Get error messages
- **Error Handling**:
  - Partial failure recovery (continues if < 3 errors)
  - Progress tracking for user feedback
  - Error aggregation for batch operations

## Data Flow

### Preset Application Flow

```
User selects preset
    ↓
PresetApplicationManager.apply_preset()
    ↓
Split into apps and configs
    ↓
PackageManager.install_flatpak_batch() → ConfigManager.apply_*_config()
    ↓
FileManager.write_file() with backup
    ↓
Report status (SUCCESS/PARTIAL/FAILED)
```

### Backup Flow

```
Before write operation
    ↓
FileManager.create_backup()
    ↓
Generate timestamp: filename_YYYYMMDD_HHMMSS
    ↓
Copy to ~/.config/linux-tweaker/backups/
    ↓
Record in backup history
    ↓
Proceed with write operation
```

## Error Handling Strategy

### Error Categories

1. **Network Errors**: Timeouts, DNS failures, connection refused
2. **File System Errors**: Permissions, disk full, file not found
3. **Dependency Errors**: Missing packages, version conflicts
4. **Configuration Errors**: Invalid syntax, missing values
5. **User Errors**: Invalid input, cancellation
6. **System Errors**: Out of memory, unexpected exceptions

### Error Recovery

- **Network**: Retry logic (not yet implemented)
- **File System**: User-friendly messages, suggest fixes
- **Dependencies**: List missing deps, provide install commands
- **Configuration**: Restore from backup, validate before apply
- **User**: Clear error messages, retry option
- **System**: Log full error, graceful degradation

## Security Architecture

### Input Validation

- All URLs validated for scheme and netloc
- Filenames sanitized to prevent path traversal
- Git URLs restricted to safe schemes (git, https, ssh)
- Script execution restricted to dotfiles directory

### File Permissions

- Config files: 0o600 (rw-------)
- Directories: 0o700 (rwx------)
- Backups inherit secure permissions

### Resource Limits

- File size: 100MB maximum
- Disk space: 100MB minimum required
- Timeout: 120s for downloads, 300s for git operations

## Testing Architecture

### Test Suite

```
test_app.py (Integration Tests)
├── test_system_checker()
├── test_file_manager()
├── test_package_manager()
├── test_config_manager()
├── test_preset_manager()
├── test_backup_restore()
├── test_edge_cases()
└── test_partial_failure_recovery()

test_unit.py (Unit Tests)
├── test_system_checker_dependency_check()
├── test_file_manager_backup_naming()
├── test_package_manager_url_validation()
├── test_config_manager_git_url_validation()
├── test_preset_manager_error_threshold()
└── test_ui_builder_null_safety()
```

### Test Coverage

- **Integration Tests**: 8 tests covering complete workflows
- **Unit Tests**: 6 tests covering individual components
- **Edge Cases**: Invalid paths, missing files, encoding errors
- **Partial Failure**: Graceful degradation verification

## Configuration Paths

```
~/.config/hypr/hyprland.conf          # Hyprland config
~/.config/waybar/config.jsonc           # Waybar config
~/.config/waybar/style.css             # Waybar CSS
~/.config/rofi/config.rasi             # Rofi config
~/.config/rofi/themes/catppuccin.rasi  # Rofi theme
~/.config/linux-tweaker/backups/      # Backup directory
~/.local/bin/                         # Binary installation directory
```

## Future Enhancements

### Phase 2 (In Progress)
- Complete documentation
- Performance optimizations
- Distribution packages
- Accessibility features

### Phase 3 (Planned)
- Internationalization
- Advanced UI features
- Community features
- Tutorials and examples

## Dependencies

### Runtime
- Python 3.8+
- rich (TUI library)
- pathlib (Path operations)
- subprocess (External command execution)

### System Tools
- git (Dotfile cloning)
- curl (Downloads)
- Flatpak (App installation)
- Hyprland (Target window manager)

## License

MIT License - See LICENSE file for details
