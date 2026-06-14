# Contributing to linux-tweaker

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Report issues constructively

## How to Contribute

### Reporting Bugs

1. **Check existing issues** — Search GitHub Issues to avoid duplicates
2. **Create a detailed report** — Include:
   - Your OS and desktop environment
   - Steps to reproduce
   - Expected vs. actual behavior
   - Error messages or logs
   - Screenshots if applicable

### Suggesting Features

1. **Check existing discussions** — Avoid duplicate suggestions
2. **Describe the use case** — Why would this feature be useful?
3. **Provide examples** — Show how it would work
4. **Consider alternatives** — Are there workarounds?

### Adding a New Preset

1. **Create a JSON file** in `presets/` following this structure:

```json
{
  "name": "Your Theme Name",
  "description": "Brief description of the theme",
  "themes": {
    "gtk": "Theme Name",
    "icon": "Icon Theme Name",
    "cursor": "Cursor Theme Name",
    "font": "Font Name 11"
  },
  "wallpaper": "https://example.com/wallpaper.jpg",
  "hyprland": {
    "theme": {
      "general:col.active_border": "0xffRRGGBB",
      "general:gaps_in": 10,
      "general:gaps_out": 10,
      "general:border_size": 2,
      "general:rounding": 12
    },
    "waybar-style": "your-theme-name",
    "rofi-theme": "your-theme-name",
    "resources": {
      "fonts": ["https://example.com/fonts.zip"],
      "theme-url": "https://example.com/theme.zip",
      "icon-url": "https://example.com/icons.zip",
      "cursor-url": "https://example.com/cursors.zip"
    }
  }
}
```

2. **Test the preset**:
   ```bash
   python src/main.py preview your-theme-name
   python src/main.py apply your-theme-name
   ```

3. **Verify all components apply** — Check fonts, icons, GTK, cursor, Waybar, Rofi

4. **Submit a pull request** with:
   - Preset JSON file
   - Screenshot of the applied theme
   - Description of the theme's aesthetic

### Improving Code

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** following the code style:
   - Use 4 spaces for indentation
   - Follow PEP 8 for Python
   - Add docstrings to functions
   - Keep functions focused and small

4. **Test your changes**:
   ```bash
   python -m pytest tests/ -v
   ```

5. **Commit with clear messages**:
   ```bash
   git commit -m "Fix: description of what was fixed"
   git commit -m "Feature: description of new feature"
   git commit -m "Refactor: description of refactoring"
   ```

6. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guide

### Python

```python
# Good: Clear, documented, follows PEP 8
def apply_preset(self, preset: Preset) -> bool:
    """Apply a preset and return success status.
    
    Args:
        preset: The preset to apply
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Implementation
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Bad: Unclear, no documentation, poor error handling
def apply(p):
    # do stuff
    return something
```

### Error Handling

```python
# Good: Graceful degradation
try:
    self._run(["gsettings", "set", ...], check=False)
except FileNotFoundError:
    print("Warning: gsettings not found, skipping")
    pass

# Bad: Silent failure
try:
    self._run(["gsettings", "set", ...])
except:
    pass
```

### Naming Conventions

- **Functions**: `snake_case` (e.g., `apply_preset`)
- **Classes**: `PascalCase` (e.g., `HyprlandThemeEngine`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `BACKUP_DIR`)
- **Private methods**: `_leading_underscore` (e.g., `_apply_wallpaper`)

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_hyprland_engine.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

```python
import pytest
from src.engines.hyprland_engine import HyprlandThemeEngine
from src.preset_manager import PresetManager

def test_apply_preset_creates_backup():
    """Test that applying a preset creates a backup."""
    engine = HyprlandThemeEngine()
    pm = PresetManager()
    preset = pm.get_preset('lime-glass')
    
    backup_id = engine.backup_current()
    assert backup_id is not None
    assert len(backup_id) == 15  # YYYYmmdd_HHMMSS

def test_apply_preset_returns_true_on_success():
    """Test that apply_preset returns True on success."""
    engine = HyprlandThemeEngine()
    pm = PresetManager()
    preset = pm.get_preset('lime-glass')
    
    result = engine.apply_preset(preset)
    assert result is True
```

## Documentation

### Updating README

- Keep it concise and well-organized
- Use clear headings and sections
- Include code examples
- Update the table of contents if adding sections

### Adding API Documentation

```python
def apply_preset(self, preset: Preset) -> bool:
    """Apply a preset to the current desktop environment.
    
    This method:
    1. Creates a backup of current configuration
    2. Downloads required resources (fonts, themes, icons)
    3. Applies all theme components (GTK, icons, cursor, etc.)
    4. Generates Waybar CSS and Rofi theme
    5. Applies Hyprland/Sway/i3 configuration
    
    Args:
        preset (Preset): The preset to apply
        
    Returns:
        bool: True if successful, False if any step failed
        
    Raises:
        FileNotFoundError: If required tools are missing
        
    Example:
        >>> engine = HyprlandThemeEngine()
        >>> preset = PresetManager().get_preset('lime-glass')
        >>> success = engine.apply_preset(preset)
        >>> if success:
        ...     print("Theme applied successfully!")
    """
```

## Pull Request Process

1. **Update documentation** — If adding features, update README and docs
2. **Add tests** — All new code should have tests
3. **Run tests locally** — Ensure all tests pass
4. **Write clear PR description** — Explain what and why
5. **Link related issues** — Use "Fixes #123" in PR description
6. **Be responsive** — Address review comments promptly

## Release Process

1. **Update version** in `setup.py` and `package.json`
2. **Update CHANGELOG.md** with new features and fixes
3. **Create a git tag**: `git tag v1.0.0`
4. **Push tag**: `git push origin v1.0.0`
5. **Create GitHub Release** with changelog
6. **Build and upload binary** (if applicable)

## Questions?

- **GitHub Issues** — For bug reports and feature requests
- **GitHub Discussions** — For questions and ideas
- **Email** — For security issues (don't use public issues)

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors page
- Project README (if significant contributions)

Thank you for contributing to linux-tweaker! 🎨
