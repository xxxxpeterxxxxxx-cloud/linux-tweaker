#!/bin/bash
# setup_mock_env.sh - Erstellt Test-Umgebung für sicheres Testing
# Erzeugt Fake-Sysfs für Temps/Akku und Dummy-Config-Ordner für GNOME/KDE/Hyprland

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCK_ROOT="$SCRIPT_DIR/mock_env"

echo "🔧 Erstelle Mock-Umgebung in: $MOCK_ROOT"

# Bereinige alte Mock-Umgebung
rm -rf "$MOCK_ROOT"
mkdir -p "$MOCK_ROOT"

# 1. Fake Sysfs für Hardware-Monitoring
echo "📊 Erstelle Fake /sys/class/hwmon..."
mkdir -p "$MOCK_ROOT/sys/class/hwmon/hwmon0"
echo "coretemp" > "$MOCK_ROOT/sys/class/hwmon/hwmon0/name"
echo "45000" > "$MOCK_ROOT/sys/class/hwmon/hwmon0/temp1_input"  # 45°C
echo "Package id 0" > "$MOCK_ROOT/sys/class/hwmon/hwmon0/temp1_label"

mkdir -p "$MOCK_ROOT/sys/class/hwmon/hwmon1"
echo "i915" > "$MOCK_ROOT/sys/class/hwmon/hwmon1/name"
echo "52000" > "$MOCK_ROOT/sys/class/hwmon/hwmon1/temp1_input"  # 52°C
echo "GT0 temp" > "$MOCK_ROOT/sys/class/hwmon/hwmon1/temp1_label"

# 2. Fake Power Supply für Akku
echo "🔋 Erstelle Fake /sys/class/power_supply/BAT0..."
mkdir -p "$MOCK_ROOT/sys/class/power_supply/BAT0"
echo "Battery" > "$MOCK_ROOT/sys/class/power_supply/BAT0/type"
echo "85" > "$MOCK_ROOT/sys/class/power_supply/BAT0/capacity"
echo "Discharging" > "$MOCK_ROOT/sys/class/power_supply/BAT0/status"
echo "45000000" > "$MOCK_ROOT/sys/class/power_supply/BAT0/energy_now"  # 45 Wh
echo "55000000" > "$MOCK_ROOT/sys/class/power_supply/BAT0/energy_full"  # 55 Wh

# 3. Fake zram
echo "💾 Erstelle Fake /sys/block/zram0..."
mkdir -p "$MOCK_ROOT/sys/block/zram0"
mkdir -p "$MOCK_ROOT/sys/class/block/zram0"
echo "2147483648" > "$MOCK_ROOT/sys/block/zram0/disksize"  # 2 GB
echo "0 0 0 1073741824 0 0 0 0" > "$MOCK_ROOT/sys/block/zram0/mm_stat"  # 1 GB used

# 4. Fake GNOME Config
echo "🖥️  Erstelle Fake ~/.config (GNOME)..."
mkdir -p "$MOCK_ROOT/config/gtk-3.0"
cat > "$MOCK_ROOT/config/gtk-3.0/settings.ini" << EOF
[Settings]
gtk-theme-name=Adwaita
gtk-icon-theme-name=Adwaita
gtk-font-name=Source Sans Pro 11
EOF

mkdir -p "$MOCK_ROOT/config/dconf"
cat > "$MOCK_ROOT/config/dconf/user" << EOF
# Fake dconf database
[/org/gnome/desktop/interface]
gtk-theme='Adwaita'
icon-theme='Adwaita'
font-name='Source Sans Pro 11'
[/org/gnome/desktop/background]
picture-uri='file:///usr/share/backgrounds/default.jpg'
EOF

# 5. Fake KDE Config
echo "🖥️  Erstelle Fake ~/.config (KDE Plasma)..."
mkdir -p "$MOCK_ROOT/config/plasma"
cat > "$MOCK_ROOT/config/plasma/plasmashellrc" << EOF
[General]
shellPackage=org.kde.plasma.desktop
[Theme]
name=default
EOF

cat > "$MOCK_ROOT/config/kdeglobals" << EOF
[General]
[KDE]
LookAndFeelPackage=org.kde.breeze.desktop
[Icons]
Theme=breeze
EOF

# 6. Fake Hyprland Config
echo "🖥️  Erstelle Fake ~/.config (Hyprland)..."
mkdir -p "$MOCK_ROOT/config/hypr"
cat > "$MOCK_ROOT/config/hypr/hyprland.conf" << EOF
# Fake Hyprland config
source=~/.config/hypr/hyprland.conf.d

general {
    gaps_in=5
    gaps_out=10
    border_size=2
}

decoration {
    rounding=10
}

$mod=SUPER
EOF

mkdir -p "$MOCK_ROOT/config/hypr/hyprland.conf.d"
cat > "$MOCK_ROOT/config/hypr/hyprland.conf.d/waybar.conf" << EOF
# Waybar integration
exec-once=waybar
EOF

# 7. Fake Sway Config
echo "🖥️  Erstelle Fake ~/.config (Sway)..."
mkdir -p "$MOCK_ROOT/config/sway"
cat > "$MOCK_ROOT/config/sway/config" << EOF
# Fake Sway config
set $mod Mod4

output * bg /usr/share/backgrounds/sway/Sway_Wallpaper_Blue.png fill
EOF

# 8. Fake XFCE Config
echo "🖥️  Erstelle Fake ~/.config (XFCE)..."
mkdir -p "$MOCK_ROOT/config/xfce4/xfconf/xfce-perchannel-xml"
cat > "$MOCK_ROOT/config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="image-path" type="string" value="/usr/share/backgrounds/xfce/xfce-blue.jpg"/>
      </property>
    </property>
  </property>
</channel>
EOF

# 9. Fake Presets
echo "🎨 Erstelle Fake Presets..."
mkdir -p "$MOCK_ROOT/presets"
cat > "$MOCK_ROOT/presets/cyberpunk.json" << EOF
{
  "name": "Cyberpunk",
  "description": "Neon colors, dark theme, futuristic fonts",
  "themes": {
    "gtk": "Catppuccin-Mocha-Blue",
    "icon": "Tela-circle-dracula",
    "cursor": "Bibata-Modern-Ice",
    "font": "JetBrains Mono Nerd Font"
  },
  "wallpaper": "https://w.wallhaven.cc/full/wq/wallhaven-wqve6r.jpg",
  "settings": {
    "gnome": {
      "gtk-theme": "Catppuccin-Mocha-Blue",
      "icon-theme": "Tela-circle-dracula",
      "font-name": "JetBrains Mono 11"
    },
    "kde": {
      "plasma-theme": "Catppuccin-Mocha-Blue",
      "icon-theme": "Tela-circle-dracula"
    },
    "hyprland": {
      "waybar-style": "cyberpunk",
      "rofi-theme": "cyberpunk"
    }
  }
}
EOF

cat > "$MOCK_ROOT/presets/minimal_dark.json" << EOF
{
  "name": "Minimal Dark",
  "description": "Clean dark theme with minimal distractions",
  "themes": {
    "gtk": "Adwaita-dark",
    "icon": "Adwaita",
    "cursor": "Adwaita",
    "font": "Inter 11"
  },
  "wallpaper": "https://w.wallhaven.cc/full/dg/dgwallhaven-dg6oo3.jpg",
  "settings": {
    "gnome": {
      "gtk-theme": "Adwaita-dark",
      "icon-theme": "Adwaita",
      "font-name": "Inter 11"
    },
    "kde": {
      "plasma-theme": "Breeze Dark",
      "icon-theme": "Breeze"
    }
  }
}
EOF

cat > "$MOCK_ROOT/presets/nordic_productivity.json" << EOF
{
  "name": "Nordic Productivity",
  "description": "Nord color scheme optimized for focus",
  "themes": {
    "gtk": "Nordic",
    "icon": "Nordic",
    "cursor": "Vimix",
    "font": "Fira Code 11"
  },
  "wallpaper": "https://w.wallhaven.cc/full/xj/xjwallhaven-xjdm7y.jpg",
  "settings": {
    "gnome": {
      "gtk-theme": "Nordic",
      "icon-theme": "Nordic",
      "font-name": "Fira Code 11"
    },
    "kde": {
      "plasma-theme": "Nordic",
      "icon-theme": "Nordic"
    }
  }
}
EOF

# 10. Fake Environment Variables
echo "🔧 Erstelle Fake Environment-Datei..."
cat > "$MOCK_ROOT/env.sh" << EOF
export MOCK_ROOT="$MOCK_ROOT"
export XDG_CURRENT_DESKTOP="GNOME"
export XDG_CONFIG_HOME="$MOCK_ROOT/config"
export XDG_DATA_HOME="$MOCK_ROOT/share"
export PATH="$MOCK_ROOT/bin:$PATH"
EOF

# 11. Symlink Struktur für Tests
echo "🔗 Erstelle Symlinks für Tests..."
mkdir -p "$MOCK_ROOT/bin"
ln -sf "$MOCK_ROOT/sys" "$MOCK_ROOT/sys_link"

echo "✅ Mock-Umgebung erstellt!"
echo ""
echo "Verwendung für Tests:"
echo "  source $MOCK_ROOT/env.sh"
echo "  export SYSFS_ROOT=\$MOCK_ROOT/sys"
echo ""
echo "Struktur:"
tree "$MOCK_ROOT" 2>/dev/null || find "$MOCK_ROOT" -type f | head -20
