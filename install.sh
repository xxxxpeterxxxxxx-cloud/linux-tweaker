#!/usr/bin/env bash
# One-liner installer for linux-tweaker
# Usage: curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker"
INSTALL_DIR="${HOME}/.local/share/linux-tweaker"
BIN_DIR="${HOME}/.local/bin"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==>${NC} Linux Tweaker Installer"
echo ""

# Check Python version (proper numeric comparison)
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "0")
python_major=$(python3 -c 'import sys; print(sys.version_info[0])' 2>/dev/null || echo "0")
python_minor=$(python3 -c 'import sys; print(sys.version_info[1])' 2>/dev/null || echo "0")
if [[ "$python_major" -lt 3 ]] || [[ "$python_major" -eq 3 && "$python_minor" -lt 8 ]]; then
    echo -e "${RED}ERROR:${NC} Python 3.8+ required. Found: $python_version"
    echo "Install Python 3.8+ and try again."
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $python_version"

# Check for required tools
for tool in git curl; do
    if ! command -v "$tool" &>/dev/null; then
        echo -e "${RED}ERROR:${NC} $tool is required. Install it first:"
        echo "  Fedora: sudo dnf install $tool"
        echo "  Ubuntu/Debian: sudo apt install $tool"
        echo "  Arch: sudo pacman -S $tool"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $tool"
done

# Check for pip
if ! command -v pip3 &>/dev/null; then
    echo -e "${YELLOW}WARN:${NC} pip3 not found. Will try without installing Python deps."
    SKIP_PIP=1
fi

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Clone or update
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo -e "${GREEN}==>${NC} Updating existing installation..."
    cd "$INSTALL_DIR"
    if ! git pull --ff-only; then
        echo -e "${YELLOW}WARN:${NC} git pull failed, re-cloning..."
        cd "$HOME"
        rm -rf "$INSTALL_DIR"
        git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    fi
else
    echo -e "${GREEN}==>${NC} Cloning linux-tweaker..."
    rm -rf "$INSTALL_DIR"
    if ! git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"; then
        echo -e "${RED}ERROR:${NC} Failed to clone repository"
        exit 1
    fi
fi

# Install Python dependencies
if [[ "${SKIP_PIP:-0}" == "0" ]]; then
    echo -e "${GREEN}==>${NC} Installing Python dependencies..."
    cd "$INSTALL_DIR"
    if ! pip3 install --user -r requirements.txt 2>/dev/null; then
        echo -e "${YELLOW}WARN:${NC} pip install failed, trying with --break-system-packages..."
        pip3 install --user --break-system-packages -r requirements.txt 2>/dev/null || {
            echo -e "${YELLOW}WARN:${NC} Could not install dependencies. Some features may not work."
        }
    fi
fi

# Create wrapper script
cat > "$BIN_DIR/linux-tweaker" << 'EOF'
#!/usr/bin/env bash
exec python3 "${HOME}/.local/share/linux-tweaker/main.py" "$@"
EOF
chmod +x "$BIN_DIR/linux-tweaker"

# Symlink shorter command
ln -sf "$BIN_DIR/linux-tweaker" "$BIN_DIR/tweak"

# Add to PATH if needed
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    SHELL_RC=""
    if [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    elif [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    
    if [[ -n "$SHELL_RC" ]]; then
        echo "" >> "$SHELL_RC"
        echo "# Linux Tweaker" >> "$SHELL_RC"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        echo "==> Added $BIN_DIR to PATH in $(basename "$SHELL_RC")"
        echo "    Run: source $SHELL_RC"
    fi
fi

# Add rofi shell function to prevent "unsure what to do" error
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [[ -f "$RC" ]] && ! grep -q 'linux-tweaker: rofi default to drun' "$RC" 2>/dev/null; then
        echo "" >> "$RC"
        echo "# linux-tweaker: rofi default to drun" >> "$RC"
        echo "rofi() { if [ \$# -eq 0 ]; then command rofi -show drun; else command rofi \"\$@\"; fi }" >> "$RC"
    fi
done

echo ""
echo "==> Installation complete!"
echo ""
echo "Usage:"
echo "  linux-tweaker --list              # List presets"
echo "  linux-tweaker --apply 'Preset'   # Apply a preset"
echo "  linux-tweaker --help             # Show all options"
echo ""
echo "Or use the short alias:"
echo "  tweak --list"
echo "  tweak --apply 'Blue Dream'"
echo ""
echo "Note: typing 'rofi' in terminal now defaults to app launcher"
echo ""
