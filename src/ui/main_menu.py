"""
Main Menu UI
Rich TUI for Linux Tweaker
"""

import sys
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from de_detector import DEInfo
from engines import (
    GnomeThemeEngine, HyprlandThemeEngine, PlasmaThemeEngine, XfceThemeEngine,
    SwayThemeEngine, I3ThemeEngine, BspwmThemeEngine, LxqtThemeEngine, MateThemeEngine,
    GenericThemeEngine,
)
from hardware_monitor import HardwareMonitor
from power_tuner import PowerTuner
from preset_manager import PresetManager
from theme_engine import GenericThemeEngine, ThemeEngine
from version import __version__


ASCII_LOGO = """
    ███████╗██╗  ██╗███████╗██╗     ██╗
    ██╔════╝██║  ██║██╔════╝██║     ██║
    ███████╗███████║█████╗  ██║     ██║
    ╚════██║██╔══██║██╔══╝  ██║     ██║
    ███████║██║  ██║███████╗███████╗███████╗
    ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
    ╔═════════════════════════════════════╗
    ║              ENGINE                 ║
    ╚═════════════════════════════════════╝
"""


class MainMenu:
    """Main menu with Rich TUI."""

    def __init__(self, de_info: DEInfo):
        self.de_info = de_info
        self.console = Console()
        self.preset_manager = PresetManager()
        self.hardware_monitor = HardwareMonitor()
        self.power_tuner = PowerTuner()
        self.theme_engine = self._get_theme_engine()

    def _get_theme_engine(self) -> ThemeEngine:
        """Select the appropriate theme engine for the detected DE."""
        engine_map = {
            "GnomeThemeEngine": GnomeThemeEngine,
            "PlasmaThemeEngine": PlasmaThemeEngine,
            "HyprlandThemeEngine": HyprlandThemeEngine,
            "XfceThemeEngine": XfceThemeEngine,
            "SwayThemeEngine": SwayThemeEngine,
            "I3ThemeEngine": I3ThemeEngine,
            "BspwmThemeEngine": BspwmThemeEngine,
            "LxqtThemeEngine": LxqtThemeEngine,
            "MateThemeEngine": MateThemeEngine,
        }
        engine_class = engine_map.get(self.de_info.engine)
        if engine_class:
            return engine_class()
        return GenericThemeEngine()
    
    def run(self):
        """Run the main menu loop."""
        while True:
            self._show_header()
            self._show_menu()

            choice = Prompt.ask(
                "\n[bold cyan]Choose an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "q"],
                default="1"
            )

            if choice == "1":
                self._show_presets()
            elif choice == "2":
                self._apply_preset()
            elif choice == "3":
                self._show_monitoring()
            elif choice == "4":
                self._show_power_tuning()
            elif choice == "5":
                self._show_backups()
            elif choice == "6":
                self._auto_tune()
            elif choice == "7":
                self._reset_configs()
            elif choice == "8":
                self._health_check()
            elif choice == "9" or choice == "q":
                self.console.print("[yellow]Goodbye![/yellow]")
                break
    
    def _show_header(self):
        """Show header with system info."""
        self.console.clear()
        self.console.print(ASCII_LOGO, style="bold cyan")

        info_panel = Panel(
            f"[bold green]v{__version__}[/bold green]\n\n"
            f"[cyan]┌─ DE/WM:[/cyan] [bold yellow]{self.de_info.name}[/bold yellow]\n"
            f"[cyan]├─ Type:[/cyan] [bold yellow]{self.de_info.type}[/bold yellow]\n"
            f"[cyan]└─ Engine:[/cyan] [bold magenta]{self.de_info.engine}[/bold magenta]",
            title="[bold white]SYSTEM INFO[/bold white]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(info_panel)
    
    def _show_menu(self):
        """Show main menu."""
        menu_table = Table(
            title="[bold white]╔═══════════════════════════════════════╗[/bold white]",
            title_style="bold white",
            show_header=True,
            header_style="bold white",
            box=None,
            padding=(0, 2)
        )
        menu_table.add_column("[bold cyan]#[/bold cyan]", style="cyan", width=4)
        menu_table.add_column("[bold cyan]OPTION[/bold cyan]", style="white")

        menu_table.add_row("[1]", "[bold green]🎨[/bold green] List Presets")
        menu_table.add_row("[2]", "[bold green]⚡[/bold green] Apply Preset")
        menu_table.add_row("[3]", "[bold yellow]📊[/bold yellow] Hardware Monitoring")
        menu_table.add_row("[4]", "[bold yellow]🔋[/bold yellow] Power Tuning")
        menu_table.add_row("[5]", "[bold magenta]💾[/bold magenta] Manage Backups")
        menu_table.add_row("[6]", "[bold magenta]🤖[/bold magenta] Auto-Tune")
        menu_table.add_row("[7]", "[bold red]🧹[/bold red] Reset Configs")
        menu_table.add_row("[8]", "[bold cyan]🏥[/bold cyan] Health Check")
        menu_table.add_row("[9]", "[bold red]🚪[/bold red] Quit")

        self.console.print(menu_table)
        self.console.print("[bold white]╚═══════════════════════════════════════╝[/bold white]")
    
    def _show_presets(self):
        """Show available presets."""
        presets = self.preset_manager.list_presets()

        if not presets:
            self.console.print("\n[bold red]✗ No presets found[/bold red]")
            Prompt.ask("\n[dim]Press Enter...[/dim]")
            return

        table = Table(
            title="[bold green]╔═══════════════════════════════════════╗[/bold green]\n[bold green]║        AVAILABLE PRESETS                ║[/bold green]\n[bold green]╚═══════════════════════════════════════╝[/bold green]",
            show_header=True,
            header_style="bold white",
            box=None
        )
        table.add_column("[bold cyan]NAME[/bold cyan]", style="cyan", width=20)
        table.add_column("[bold cyan]DESCRIPTION[/bold cyan]", style="white")

        for i, preset in enumerate(presets, 1):
            table.add_row(f"[bold yellow]{i}.[/bold yellow] {preset.name}", preset.description)

        self.console.print(table)
        Prompt.ask("\n[dim]Press Enter...[/dim]")
    
    def _apply_preset(self):
        """Apply a preset."""
        presets = self.preset_manager.list_presets()

        if not presets:
            self.console.print("\n[bold red]✗ No presets found[/bold red]")
            Prompt.ask("\n[dim]Press Enter...[/dim]")
            return

        preset_names = [p.name for p in presets]
        self.console.print("\n[bold cyan]Choose a preset:[/bold cyan]")
        for i, name in enumerate(preset_names, 1):
            self.console.print(f"  [bold yellow]{i}.[/bold yellow] {name}")

        choice = Prompt.ask("\n[cyan]Enter number[/cyan]", choices=[str(i) for i in range(1, len(preset_names) + 1)])
        preset = presets[int(choice) - 1]

        self.console.print(f"\n[bold green]╔═══════════════════════════════════════╗[/bold green]")
        self.console.print(f"[bold green]║           PREVIEW: {preset.name}{' ' * (21 - len(preset.name))}║[/bold green]")
        self.console.print(f"[bold green]╚═══════════════════════════════════════╝[/bold green]")
        self.theme_engine.preview_preset(preset)

        if Confirm.ask("\n[bold yellow]Apply preset?[/bold yellow]"):
            success = self.theme_engine.apply_preset(preset)
            if success:
                self.console.print("\n[bold green]✓ Preset applied successfully![/bold green]")
            else:
                self.console.print("\n[bold red]✗ Error applying preset[/bold red]")

        Prompt.ask("\n[dim]Press Enter...[/dim]")
    
    def _show_monitoring(self):
        """Show hardware monitoring."""
        stats = self.hardware_monitor.get_all_stats()

        self.console.print(f"\n[bold yellow]╔═══════════════════════════════════════╗[/bold yellow]")
        self.console.print(f"[bold yellow]║         HARDWARE MONITORING            ║[/bold yellow]")
        self.console.print(f"[bold yellow]╚═══════════════════════════════════════╝[/bold yellow]\n")

        temps = stats.get("temperatures", {})
        if temps:
            table = Table(show_header=True)
            table.add_column("[bold cyan]SENSOR[/bold cyan]", style="cyan")
            table.add_column("[bold cyan]TEMPERATURE[/bold cyan]", style="yellow")

            for name, temp in temps.items():
                temp_color = "green" if temp < 50 else "yellow" if temp < 70 else "red"
                table.add_row(name, f"[{temp_color}]{temp}°C[/{temp_color}]")

            self.console.print(table)

        battery = stats.get("battery", {})
        if "error" not in battery:
            bat_color = "green" if battery['capacity'] > 50 else "yellow" if battery['capacity'] > 20 else "red"
            status_icon = "🔌" if battery['status'] == "Charging" else "🔋"
            self.console.print(f"\n[bold]Battery:[/bold] [{bat_color}]{battery['capacity']}%[/{bat_color}] {status_icon} ({battery['status']})")

        zram = stats.get("zram", {})
        if "error" not in zram:
            zram_color = "green" if zram['usage_percent'] < 50 else "yellow" if zram['usage_percent'] < 80 else "red"
            self.console.print(f"[bold]zRAM:[/bold] [{zram_color}]{zram['used_gb']}/{zram['total_gb']} GB ({zram['usage_percent']}%)[/{zram_color}]")

        Prompt.ask("\n[dim]Press Enter...[/dim]")
    
    def _show_power_tuning(self):
        """Show power-tuning options."""
        profiles = self.power_tuner.get_available_profiles()
        current = self.power_tuner.get_current_profile()

        self.console.print(f"\n[bold magenta]╔═══════════════════════════════════════╗[/bold magenta]")
        self.console.print(f"[bold magenta]║            POWER TUNING               ║[/bold magenta]")
        self.console.print(f"[bold magenta]╚═══════════════════════════════════════╝[/bold magenta]\n")

        profile_colors = {"power-saver": "green", "balanced": "yellow", "performance": "red"}
        current_color = profile_colors.get(current, "white")

        self.console.print(f"[bold]Current profile:[/bold] [{current_color}]{current.upper()}[/{current_color}]")
        self.console.print(f"[bold]Available profiles:[/bold] {', '.join(profiles)}\n")

        if Confirm.ask("[bold yellow]Change profile?[/bold yellow]"):
            new_profile = Prompt.ask("[cyan]New profile[/cyan]", choices=profiles)
            self.power_tuner.set_power_profile(new_profile)

        Prompt.ask("\n[dim]Press Enter...[/dim]")
    
    def _show_backups(self):
        """Show available backups."""
        from pathlib import Path

        backup_dir = Path.home() / ".config" / "linux-tweaker" / "backups"

        self.console.print(f"\n[bold magenta]╔═══════════════════════════════════════╗[/bold magenta]")
        self.console.print(f"[bold magenta]║           BACKUP MANAGER             ║[/bold magenta]")
        self.console.print(f"[bold magenta]╚═══════════════════════════════════════╝[/bold magenta]\n")

        if not backup_dir.exists():
            self.console.print("[bold red]✗ No backups found[/bold red]")
            Prompt.ask("\n[dim]Press Enter...[/dim]")
            return

        backups = list(backup_dir.glob("*"))

        if not backups:
            self.console.print("[bold red]✗ No backups found[/bold red]")
            Prompt.ask("\n[dim]Press Enter...[/dim]")
            return

        table = Table(show_header=True)
        table.add_column("[bold cyan]NAME[/bold cyan]", style="cyan")

        for i, backup in enumerate(backups, 1):
            table.add_row(f"[bold yellow]{i}.[/bold yellow] {backup.name}")

        self.console.print(table)

        if Confirm.ask("\n[bold yellow]Restore a backup?[/bold yellow]"):
            backup_name = Prompt.ask("[cyan]Backup number or name[/cyan]")
            if backup_name.isdigit():
                backup = backups[int(backup_name) - 1]
                backup_name = backup.name
            # Extract backup_id: gnome_20260612_174204.json -> 20260612_174204
            for prefix in ["gnome_", "hyprland_", "plasma_", "xfce_"]:
                if backup_name.startswith(prefix):
                    backup_id = backup_name.replace(prefix, "").replace(".json", "")
                    break
            else:
                backup_id = backup_name.split(".")[0]
            self.theme_engine.restore_backup(backup_id)

        Prompt.ask("\n[dim]Press Enter...[/dim]")
    
    def _auto_tune(self):
        """Run auto-tune."""
        self.console.print(f"\n[bold magenta]╔═══════════════════════════════════════╗[/bold magenta]")
        self.console.print(f"[bold magenta]║              AUTO-TUNE                 ║[/bold magenta]")
        self.console.print(f"[bold magenta]╚═══════════════════════════════════════╝[/bold magenta]\n")

        self.console.print("[bold yellow]⚙️  Running auto-tune...[/bold yellow]")
        self.power_tuner.auto_tune()
        self.console.print("\n[bold green]✓ Auto-Tune complete![/bold green]")
        Prompt.ask("\n[dim]Press Enter...[/dim]")

    def _health_check(self):
        """Run a system health check for ricing dependencies."""
        import shutil
        self.console.print(f"\n[bold cyan]╔═══════════════════════════════════════╗[/bold cyan]")
        self.console.print(f"[bold cyan]║           HEALTH CHECK                ║[/bold cyan]")
        self.console.print(f"[bold cyan]╚═══════════════════════════════════════╝[/bold cyan]\n")

        checks = [
            ("Python 3.8+", sys.version_info >= (3, 8)),
            ("git", shutil.which("git") is not None),
            ("curl", shutil.which("curl") is not None),
            ("pip3", shutil.which("pip3") is not None),
        ]

        # DE-specific checks
        if self.de_info.engine == "HyprlandThemeEngine":
            checks.extend([
                ("hyprctl", shutil.which("hyprctl") is not None),
                ("swww", shutil.which("swww") is not None),
                ("waybar", shutil.which("waybar") is not None),
                ("rofi", shutil.which("rofi") is not None),
            ])
        elif self.de_info.engine == "GnomeThemeEngine":
            checks.extend([
                ("gsettings", shutil.which("gsettings") is not None),
            ])

        table = Table(show_header=True)
        table.add_column("[bold cyan]Dependency[/bold cyan]", style="cyan")
        table.add_column("[bold cyan]Status[/bold cyan]", style="white")

        all_ok = True
        for name, ok in checks:
            status = "[bold green]✓ OK[/bold green]" if ok else "[bold red]✗ Missing[/bold red]"
            if not ok:
                all_ok = False
            table.add_row(name, status)

        self.console.print(table)

        if all_ok:
            self.console.print("\n[bold green]✓ All dependencies satisfied![/bold green]")
        else:
            self.console.print("\n[bold yellow]⚠ Some dependencies are missing. Install them with your package manager.[/bold yellow]")

        Prompt.ask("\n[dim]Press Enter...[/dim]")

    def _reset_configs(self):
        """Reset desktop configs to clean defaults."""
        self.console.print(f"\n[bold red]╔═══════════════════════════════════════╗[/bold red]")
        self.console.print(f"[bold red]║         RESET CONFIGS                  ║[/bold red]")
        self.console.print(f"[bold red]╚═══════════════════════════════════════╝[/bold red]\n")

        if not Confirm.ask("[bold red]This will BACKUP and WIPE your current configs. Continue?[/bold red]"):
            return

        if hasattr(self.theme_engine, 'reset_configs'):
            self.theme_engine.reset_configs()
            self.console.print("\n[bold green]✓ Configs reset to clean defaults![/bold green]")
            self.console.print("[yellow]Reload your session (Mod+Shift+R for Hyprland) to apply.[/yellow]")
        else:
            self.console.print("[bold red]✗ Reset not supported for this engine[/bold red]")

        Prompt.ask("\n[dim]Press Enter...[/dim]")
