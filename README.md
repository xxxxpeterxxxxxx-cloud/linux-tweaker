# Linux Tweaker

One command to rice your Linux desktop. 7 themes for Hyprland, Sway, i3, GNOME, KDE, XFCE.

## Install

```bash
# Easiest way — one command
curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | bash

# Or manually
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt
```

## Use

```bash
# Interactive mode (recommended for first-time users)
python3 main.py

# Or use CLI commands
linux-tweaker --list

# Apply a theme
tweak --apply "Blue Dream"

# Force a specific desktop environment
tweak --apply "Cyberpunk" --force-de hyprland

# Restore backup if something breaks
tweak --restore 20260617_123456

# Check system health
linux-tweaker --doctor

# List all backups
linux-tweaker --list-backups
```

## Themes

| Theme | Style |
|-------|-------|
| Blue Dream | Glassmorphism, blue accent |
| Cyberpunk | Neon, matrix rain |
| Retro Pixel | Pink/purple, pixel art |
| Lime Glass | Green glassmorphism |
| Purple Elegance | Deep purple glass |
| Violet Nights | Violet high contrast |
| Nordic Productivity | Clean nordic |

## What it does

- Installs GTK theme, icons, cursor, fonts
- Generates Hyprland config with animations & blur
- Configures Waybar with glassmorphism
- Sets up Rofi app launcher
- Applies wallpaper
- **Backs up your config first**

## Requirements

- Python 3.8+, `git`, `curl`
- Your desktop environment

**No root needed.** Works on Fedora Silverblue.

## License

MIT
