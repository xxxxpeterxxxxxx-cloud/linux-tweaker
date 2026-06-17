# Linux Tweaker

One command to rice your Linux desktop. 7 themes for Hyprland, Sway, i3, GNOME, KDE, XFCE.

## Features

- **7 Pre-built Themes** — Glassmorphism, Cyberpunk, Retro Pixel, and more
- **Multi-DE Support** — Hyprland, Sway, i3, GNOME, KDE Plasma, XFCE, MATE
- **Auto-Backup** — Always backs up your config before applying changes
- **Interactive TUI** — Rich terminal UI for easy navigation
- **CLI Mode** — Full command-line control for automation
- **Health Check** — Verify all dependencies are installed
- **No Root Required** — Works on immutable systems like Fedora Silverblue

## Install

### One-Command Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | bash
```

This will:
- Clone the repository to `~/.local/share/linux-tweaker`
- Install Python dependencies (rich, etc.)
- Create `linux-tweaker` and `tweak` commands in `~/.local/bin`
- Add `~/.local/bin` to your PATH
- Fix rofi usability (adds shell function)

### Manual Install

```bash
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run directly
python3 main.py

# Or create wrapper commands (optional)
echo '#!/usr/bin/env bash' > ~/.local/bin/linux-tweaker
echo "exec python3 $(pwd)/main.py \"\$@\"" >> ~/.local/bin/linux-tweaker
chmod +x ~/.local/bin/linux-tweaker
ln -sf ~/.local/bin/linux-tweaker ~/.local/bin/tweak

# Add ~/.local/bin to PATH if not already there
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Interactive Mode (Recommended for First-Time Users)

```bash
python3 main.py
```

Launches a beautiful TUI with:
- Preset browser with descriptions
- Hardware monitoring (CPU, battery, zRAM)
- Power profile tuning
- Backup management
- System health check
- Config reset

### CLI Commands

```bash
# List all available themes
linux-tweaker --list

# Apply a theme interactively
linux-tweaker --apply "Blue Dream"

# Force a specific desktop environment
linux-tweaker --apply "Cyberpunk" --force-de hyprland

# Preview a theme without applying
linux-tweaker --preview "Blue Dream"

# Restore a backup
linux-tweaker --restore 20260617_123456
linux-tweaker --restore latest  # Restore most recent backup

# List all backups
linux-tweaker --list-backups

# Check system health and dependencies
linux-tweaker --doctor

# Show hardware monitoring
linux-tweaker --monitor

# Auto-tune power profile
linux-tweaker --tune

# Show version
linux-tweaker --version
```

### Short Alias

After installation, use the shorter `tweak` command:

```bash
tweak --list
tweak --apply "Blue Dream"
tweak --doctor
```

## Themes

| Theme | Style | Best For |
|-------|-------|----------|
| Blue Dream | Glassmorphism, blue accent | Daily use, clean look |
| Cyberpunk | Neon, matrix rain | Gaming, dark aesthetic |
| Retro Pixel | Pink/purple, pixel art | Retro gaming vibes |
| Lime Glass | Green glassmorphism | Nature-inspired setups |
| Purple Elegance | Deep purple glass | Creative work |
| Violet Nights | Violet high contrast | Low-light environments |
| Nordic Productivity | Clean nordic | Minimalist productivity |

## What Each Theme Does

### Hyprland / Sway / i3
- Generates optimized config with animations and blur
- Configures Waybar with glassmorphism CSS
- Sets up Rofi app launcher with matching theme
- Applies wallpaper via swww/hyprpaper/feh
- Configures GTK theme and icons

### GNOME
- Installs GNOME Shell extensions
- Configures gsettings for theme, fonts, layout
- Sets wallpaper and cursor theme
- Applies GTK theme and icon pack

### KDE Plasma
- Configures via kwriteconfig6
- Sets global theme, colors, fonts
- Applies wallpaper and icon theme
- Tweaks window decoration effects

### XFCE / MATE
- Uses xfconf-query for theming
- Sets GTK theme, icon theme, fonts
- Configures window manager settings
- Applies wallpaper

## Backup & Restore

Every theme application automatically creates a backup with timestamp. Backups are stored in `~/.config/linux-tweaker/backups/`.

```bash
# List all backups
linux-tweaker --list-backups

# Restore specific backup
linux-tweaker --restore 20260617_123456

# Restore latest backup
linux-tweaker --restore latest
```

## Health Check

Verify all dependencies are installed for your desktop environment:

```bash
linux-tweaker --doctor
```

Checks for:
- Python 3.8+
- git, curl, pip3
- DE-specific tools (gsettings, kwriteconfig6, xfconf-query, hyprctl, etc.)

## Requirements

### Base Requirements
- Python 3.8+
- git
- curl
- pip3 (optional, for Python dependencies)

### Desktop-Specific
- **Hyprland**: hyprctl, swww, waybar, rofi
- **Sway/i3**: sway/i3, waybar, rofi, feh
- **GNOME**: gsettings
- **KDE Plasma**: kwriteconfig6
- **XFCE/MATE**: xfconf-query

**No root required.** Works on immutable systems like Fedora Silverblue.

## Troubleshooting

### "python3: command not found"
Install Python 3.8+:
```bash
# Fedora
sudo dnf install python3

# Ubuntu/Debian
sudo apt install python3

# Arch
sudo pacman -S python
```

### "pip3: command not found"
Install pip:
```bash
# Fedora
sudo dnf install python3-pip

# Ubuntu/Debian
sudo apt install python3-pip

# Arch
sudo pacman -S python-pip
```

### Theme doesn't apply correctly
1. Run `linux-tweaker --doctor` to check dependencies
2. Restore backup: `linux-tweaker --restore latest`
3. Check logs with `linux-tweaker --verbose --apply "Theme"`

### Rofi shows "unsure what to do"
The installer automatically fixes this by adding a shell function. If you still see it:
```bash
# Add this to your ~/.bashrc or ~/.zshrc
rofi() { if [ $# -eq 0 ]; then command rofi -show drun; else command rofi "$@"; fi }
```

## Development

```bash
# Clone repository
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker

# Install dependencies
pip install -r requirements.txt

# Run directly
python3 main.py

# Run tests
python3 -m pytest tests/
```

## License

MIT
