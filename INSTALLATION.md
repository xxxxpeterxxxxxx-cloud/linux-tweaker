# Installation Guide

Complete installation and setup instructions for linux-tweaker.

## Prerequisites

- **Python 3.8+** — Check with `python3 --version`
- **git** — For cloning dotfiles repos
- **curl or wget** — For downloading themes
- **Desktop Environment** — GNOME, KDE, Hyprland, Sway, i3, XFCE, or MATE

## Quick Install (5 minutes)

### One-Command Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | bash
```

This will:
- Clone the repository to `~/.local/share/linux-tweaker`
- Install Python dependencies
- Create `linux-tweaker` and `tweak` commands
- Add to PATH automatically

### Manual Install

#### 1. Clone the Repository

```bash
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
```

#### 2. Install Python Dependencies

```bash
# User-space installation (recommended)
pip install --user -r requirements.txt

# Or system-wide (if you have sudo)
pip install -r requirements.txt
```

#### 3. Run the Application

```bash
# Interactive menu
python3 main.py

# Or create wrapper commands
echo '#!/usr/bin/env bash' > ~/.local/bin/linux-tweaker
echo "exec python3 $(pwd)/main.py \"\$@\"" >> ~/.local/bin/linux-tweaker
chmod +x ~/.local/bin/linux-tweaker
ln -sf ~/.local/bin/linux-tweaker ~/.local/bin/tweak

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Advanced Installation

### Building a Standalone Binary

If you want to distribute linux-tweaker as a single executable:

```bash
# Install PyInstaller
pip install --user pyinstaller

# Build single-file binary
pyinstaller --onefile main.py -n linux-tweaker

# Binary will be in dist/linux-tweaker
./dist/linux-tweaker
```

### Installing to System PATH (Optional)

```bash
# Copy binary to ~/.local/bin/
mkdir -p ~/.local/bin
cp dist/linux-tweaker ~/.local/bin/

# Make sure ~/.local/bin is in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Now you can run from anywhere
linux-tweaker
```

### Development Installation

If you want to contribute:

```bash
# Clone your fork
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
pip install -r requirements.txt
pip install pytest pytest-cov  # For testing

# Run tests
pytest tests/ -v
```

## Verifying Installation

### Check Python Version

```bash
python3 --version
# Should be 3.8 or higher
```

### Check Dependencies

```bash
python3 -c "import rich; import yaml; import psutil; print('✓ All dependencies installed')"
```

### Test the Application

```bash
python3 main.py --version
python3 main.py --list  # List all presets
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'rich'"

**Solution**: Install dependencies
```bash
pip install --user -r requirements.txt
```

### "python: command not found"

**Solution**: Use `python3` instead
```bash
python3 main.py
```

### "Permission denied" when running

**Solution**: Make the file executable
```bash
chmod +x main.py
```

### "git: command not found"

**Solution**: Install git
```bash
# Arch/Manjaro
sudo pacman -S git

# Ubuntu/Debian
sudo apt install git

# Fedora
sudo dnf install git
```

### "curl: command not found"

**Solution**: Install curl or wget
```bash
# Arch/Manjaro
sudo pacman -S curl

# Ubuntu/Debian
sudo apt install curl

# Fedora
sudo dnf install curl
```

## Platform-Specific Instructions

### Arch Linux / Manjaro

```bash
# Install dependencies
sudo pacman -S python python-pip git curl

# Clone and install
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run
python3 main.py
```

### Ubuntu / Debian

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip git curl

# Clone and install
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run
python3 main.py
```

### Fedora / RHEL

```bash
# Install dependencies
sudo dnf install python3 python3-pip git curl

# Clone and install
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run
python3 main.py
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python git curl

# Clone and install
git clone https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker.git
cd linux-tweaker
pip install --user -r requirements.txt

# Run
python3 main.py
```

## Immutable Systems (Bluefin, Aurora, Silverblue)

linux-tweaker is designed to work on immutable systems without requiring root:

```bash
# Install in user space
pip install --user -r requirements.txt

# Run normally (no sudo needed)
python3 main.py
```

All configurations are stored in `~/.config/linux-tweaker/` and `~/.local/share/linux-tweaker/`.

## Uninstallation

### Remove User Installation

```bash
# Remove the cloned directory
rm -rf ~/path/to/linux-tweaker

# Remove Python packages
pip uninstall rich PyYAML psutil
```

### Remove System Binary

```bash
# Remove from ~/.local/bin
rm ~/.local/bin/linux-tweaker

# Remove configurations
rm -rf ~/.config/linux-tweaker/
rm -rf ~/.local/share/linux-tweaker/
```

## Next Steps

1. **Run the application**: `python3 main.py`
2. **Browse presets**: Select "View Presets" from the menu
3. **Apply a theme**: Select "Apply Preset" and choose your favorite
4. **Enjoy your new rice!** 🎨

## Getting Help

- **GitHub Issues** — Report bugs or request features
- **GitHub Discussions** — Ask questions
- **README.md** — Full documentation
- **TROUBLESHOOTING.md** — Common issues and solutions

---

**Happy ricing!** 🎨✨
