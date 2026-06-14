"""
Preview Renderer
Generates preview tables for presets.
"""

from typing import Dict, List

from rich.console import Console
from rich.table import Table

from theme_engine import Preset


class PreviewRenderer:
    """Renders side-by-side preset previews."""

    def __init__(self):
        self.console = Console()

    def render_preset(self, preset: Preset, current_settings: Dict[str, str]) -> None:
        """Render a preset preview against current settings."""
        self.console.print(f"\n[bold cyan]Preview: {preset.name}[/bold cyan]")
        self.console.print(f"[dim]{preset.description}[/dim]\n")

        table = Table()
        table.add_column("Setting", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")

        for key, value in preset.themes.items():
            current = current_settings.get(key, "N/A")
            table.add_row(key.capitalize(), current, value)

        self.console.print(table)
        self.console.print(f"\n[bold]Wallpaper:[/bold] {preset.wallpaper}")

        changes = self._count_changes(preset, current_settings)
        self.console.print(f"\n[yellow]{changes} changes will be applied[/yellow]")

    def _count_changes(self, preset: Preset, current_settings: Dict[str, str]) -> int:
        count = 0
        for key, value in preset.themes.items():
            if current_settings.get(key) != value:
                count += 1
        return count

    def render_changes(self, changes: List[Dict]) -> None:
        """Render a list of changes."""
        if not changes:
            self.console.print("[green]No changes[/green]")
            return

        table = Table(title="Changes")
        table.add_column("Setting", style="cyan")
        table.add_column("From", style="red")
        table.add_column("To", style="green")

        for change in changes:
            table.add_row(change["key"], change["current"], change["new"])

        self.console.print(table)
