# Maintainer: Peter <your.email@example.com>
pkgname=linux-tweaker
pkgver=1.2.2
pkgrel=1
pkgdesc="Rice & Optimize Tool for Linux - theming for Hyprland, GNOME, KDE, XFCE and more"
arch=('any')
url="https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker"
license=('MIT')
depends=('python' 'python-rich' 'python-yaml' 'python-psutil' 'git' 'curl')
optdepends=(
    'hyprland: For Hyprland theming'
    'sway: For Sway theming'
    'i3-wm: For i3 theming'
    'gnome-shell: For GNOME theming'
    'plasma-workspace: For KDE Plasma theming'
    'xfce4-session: For XFCE theming'
    'rofi: Application launcher'
    'waybar: Status bar for Wayland'
    'swww: Wallpaper daemon'
    'hyprpaper: Wallpaper daemon for Hyprland'
    'pavucontrol: Volume control'
    'thunar: File manager'
    'foot: Terminal emulator'
    'wlogout: Logout menu'
    'grimblast: Screenshot tool'
    'wl-clipboard: Clipboard for Wayland'
    'mako: Notification daemon'
    'polkit-kde-agent: Authentication agent'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$pkgname-$pkgver"
    
    # Install main script and source
    install -Dm755 main.py "$pkgdir/usr/share/$pkgname/main.py"
    cp -r src presets tests "$pkgdir/usr/share/$pkgname/"
    
    # Create wrapper script in /usr/bin
    install -Dm755 /dev/stdin "$pkgdir/usr/bin/linux-tweaker" <<EOF
#!/usr/bin/env bash
exec python3 /usr/share/$pkgname/main.py "\$@"
EOF
    
    # Symlink shorter command
    ln -sf linux-tweaker "$pkgdir/usr/bin/tweak"
    
    # Desktop entry
    install -Dm644 linux-tweaker.desktop "$pkgdir/usr/share/applications/linux-tweaker.desktop"
    
    # Documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 requirements.txt "$pkgdir/usr/share/doc/$pkgname/requirements.txt"
}
