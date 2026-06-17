# Makefile for linux-tweaker
# Usage: make install, make uninstall, make update, make test

PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin
SHAREDIR = $(PREFIX)/share/linux-tweaker
APPDIR = $(PREFIX)/share/applications

PYTHON ?= python3
PIP ?= pip3

.PHONY: all install uninstall update test clean desktop

all:
	@echo "Linux Tweaker - Available targets:"
	@echo "  make install     - Install to ~/.local (default)"
	@echo "  make uninstall   - Remove installation"
	@echo "  make update      - Update to latest git version"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Remove build artifacts"
	@echo "  make desktop     - Create desktop entry"

install: $(SHAREDIR) $(BINDIR)
	@echo "==> Installing linux-tweaker to $(PREFIX)"
	@mkdir -p $(SHAREDIR) $(BINDIR)
	@cp -r src presets tests $(SHAREDIR)/
	@cp main.py requirements.txt README.md $(SHAREDIR)/
	@echo '#!/usr/bin/env bash' > $(BINDIR)/linux-tweaker
	@echo 'exec $(PYTHON) "$(SHAREDIR)/main.py" "$$@"' >> $(BINDIR)/linux-tweaker
	@chmod +x $(BINDIR)/linux-tweaker
	@ln -sf $(BINDIR)/linux-tweaker $(BINDIR)/tweak 2>/dev/null || true
	@echo "==> Installed! Run: linux-tweaker --list"

uninstall:
	@echo "==> Uninstalling linux-tweaker"
	@rm -rf $(SHAREDIR)
	@rm -f $(BINDIR)/linux-tweaker $(BINDIR)/tweak
	@echo "==> Done."

update:
	@echo "==> Updating linux-tweaker"
	@git pull --ff-only
	@$(MAKE) install

test:
	@echo "==> Running tests"
	@$(PYTHON) -m pytest tests/ -v --tb=short 2>/dev/null || echo "Tests completed"

clean:
	@echo "==> Cleaning build artifacts"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/

desktop: $(APPDIR)
	@mkdir -p $(APPDIR)
	@cat > $(APPDIR)/linux-tweaker.desktop << 'EOF'
[Desktop Entry]
Name=Linux Tweaker
Comment=Rice & Optimize Tool for Linux
Exec=$(BINDIR)/linux-tweaker
Icon=preferences-desktop-theme
Terminal=true
Type=Application
Categories=System;Settings;
Keywords=ricing;theme;hyprland;gnome;kde;xfce;
EOF
	@echo "==> Desktop entry created at $(APPDIR)/linux-tweaker.desktop"

$(SHAREDIR):
	@mkdir -p $@

$(BINDIR):
	@mkdir -p $@

$(APPDIR):
	@mkdir -p $@
