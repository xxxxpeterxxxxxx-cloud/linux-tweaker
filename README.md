# linux-tweaker

A command-line tool to apply, manage, and back up desktop configurations (ricing presets) on Linux. It supports Hyprland, Sway, i3, GNOME, KDE, XFCE, and MATE.

## Features

- **14 Pre-configured Themes** — Includes themes like Cyberpunk, Lime Glass, Nordic, Violet Nights, Blue Dream, and more.
- **Full-system Theme Application** — Applies fonts, icon sets, GTK themes, cursors, window manager configurations, Waybar styles, and Rofi menus in a single command.
- **Safety First** — Automatically creates backups before applying any changes so you can restore your setup easily.
- **Zero Root Privileges** — Runs entirely in user-space, making it safe for immutable or Fedora Silverblue/Bluefin/Universal Blue environments.
- **Hardware Stats** — Includes a basic, read-only system monitoring dashboard.

---

## ⚠️ Warning

**Use at your own risk.** This script modifies configurations in `~/.config`. Although the script creates automatic backups before applying presets, you should manually back up your files first.

---

## Quick Start

### 1. Prerequisites
Ensure you have the following installed on your system:
- Python 3.8+
- `git`
- `curl` or `wget`

### 2. Installation
```bash
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker

# Install requirements
pip install --user -r requirements.txt
```

### 3. Usage
```bash
# Start the interactive TUI menu
python src/main.py
```

---

## CLI Reference

Instead of the TUI, you can use the command-line interface directly:

```bash
# List all available presets
python src/main.py list

# Preview changes of a preset before applying
python src/main.py preview lime-glass

# Apply a preset
python src/main.py apply lime-glass

# Restore a previous backup
python src/main.py restore <backup-id>

# Run hardware monitor
python src/main.py monitor
```

---

## Project Structure

```
linux-tweaker/
├── src/
│   ├── main.py                 # Entry point
│   ├── de_detector.py          # Desktop environment detection
│   ├── theme_engine.py         # Base class for engines
│   ├── preset_manager.py       # Preset parser
│   ├── hardware_monitor.py     # Simple system monitor
│   ├── engines/
│   │   ├── hyprland_engine.py  # Hyprland / Waybar / Rofi integration
│   │   ├── gnome_engine.py     # GNOME configuration
│   │   ├── plasma_engine.py    # KDE Plasma configuration
│   │   └── xfce_engine.py      # XFCE setup
│   └── ui/
│       └── main_menu.py        # Terminal user interface (Rich)
├── presets/                    # Theme configurations (JSON)
├── tests/                      # Unit & integration tests
└── docs/                       # Configuration backups & guides
```

---

## Preset Configuration Example

Presets are stored as JSON files in `presets/`:

```json
{
  "name": "Lime Glass",
  "description": "Modern glassmorphism with lime-green accent",
  "themes": {
    "gtk": "Orchis-Green-Dark",
    "icon": "Tela-circle-green",
    "cursor": "Bibata-Modern-Classic",
    "font": "Inter 11"
  },
  "wallpaper": "https://example.com/wallpaper.jpg",
  "hyprland": {
    "theme": {
      "general:col.active_border": "0xffa6e3a1",
      "general:gaps_in": 10,
      "general:gaps_out": 10,
      "general:border_size": 2,
      "general:rounding": 12
    },
    "waybar-style": "lime-glass",
    "rofi-theme": "lime-glass",
    "resources": {
      "fonts": ["https://example.com/inter.zip"],
      "theme-url": "https://example.com/orchis.zip",
      "icon-url": "https://example.com/tela.zip",
      "cursor-url": "https://example.com/bibata.zip"
    }
  }
}
```

---

## Backups & Troubleshooting

Before running any theme modification, a backup is created in `~/.config/linux-tweaker/backups/`. 

If your desktop theme is broken or doesn't apply correctly, find the latest backup ID using `ls ~/.config/linux-tweaker/backups/` and run:

```bash
python src/main.py restore <backup-id>
```

If Waybar or Rofi don't reload automatically after applying a theme, reload your desktop or run:
```bash
# Force waybar restart
pkill waybar && waybar &
```

---

## Contributing

1. Fork the repository.
2. Add your custom preset to `presets/` as a JSON file.
3. Verify your preset using: `python src/main.py preview <preset-name>`.
4. Submit a Pull Request.

---

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

