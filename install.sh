#!/usr/bin/env bash
# One-liner installer for linux-tweaker
# Usage: curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | bash

set -e

REPO_URL="https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker"
INSTALL_DIR="${HOME}/.local/share/linux-tweaker"
BIN_DIR="${HOME}/.local/bin"

echo "==> Linux Tweaker Installer"
echo ""

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "0")
if [[ "$python_version" < "3.8" ]]; then
    echo "ERROR: Python 3.8+ required. Found: $python_version"
    exit 1
fi

# Check for git
if ! command -v git &>/dev/null; then
    echo "ERROR: git is required. Install it first:"
    echo "  Fedora: sudo dnf install git"
    echo "  Ubuntu: sudo apt install git"
    exit 1
fi

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Clone or update
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "==> Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    echo "==> Cloning linux-tweaker..."
    rm -rf "$INSTALL_DIR"
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

# Install Python dependencies
echo "==> Installing Python dependencies..."
cd "$INSTALL_DIR"
pip3 install --user -r requirements.txt 2>/dev/null || {
    echo "WARN: pip install failed, trying with --break-system-packages..."
    pip3 install --user --break-system-packages -r requirements.txt 2>/dev/null || true
}

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
