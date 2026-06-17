"""
CLI Entry Point - System Check Command

Provides a command-line interface to run system checks and report status.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not installed. Using basic output.")


from src.system_checker import SystemChecker, WindowManager, DependencyStatus


class SystemCheckCLI:
    """CLI for system checking operations."""
    
    def __init__(self):
        """Initialize CLI with console."""
        self.console = Console() if RICH_AVAILABLE else None
        self.checker = SystemChecker()
    
    def print_header(self):
        """Print CLI header."""
        if RICH_AVAILABLE:
            header = Panel(
                Text("Linux Tweaker v2.0.0 - System Check", style="bold cyan"),
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(header)
        else:
            print("=" * 50)
            print("Linux Tweaker v2.0.0 - System Check")
            print("=" * 50)
    
    def print_check_result(self, name: str, status: bool, details: str = ""):
        """
        Print a single check result.
        
        Args:
            name: Name of the check.
            status: Pass/fail status.
            details: Additional details.
        """
        if RICH_AVAILABLE:
            status_text = "[green]✓[/green]" if status else "[red]✗[/red]"
            self.console.print(f"{status_text} {name}")
            if details:
                self.console.print(f"  {details}", style="dim")
        else:
            status_symbol = "✓" if status else "✗"
            print(f"{status_symbol} {name}")
            if details:
                print(f"  {details}")
    
    def print_dependency_table(self, dependencies: dict):
        """
        Print dependency check results in a table.
        
        Args:
            dependencies: Dictionary of dependency statuses.
        """
        if RICH_AVAILABLE:
            table = Table(title="Dependency Status")
            table.add_column("Dependency", style="cyan")
            table.add_column("Status", style="bold")
            
            for dep, status in dependencies.items():
                if status == DependencyStatus.INSTALLED:
                    status_text = "[green]Installed[/green]"
                elif status == DependencyStatus.NOT_INSTALLED:
                    status_text = "[red]Not Installed[/red]"
                else:
                    status_text = "[yellow]Error[/yellow]"
                table.add_row(dep, status_text)
            
            self.console.print(table)
        else:
            print("\nDependency Status:")
            print("-" * 40)
            for dep, status in dependencies.items():
                status_str = status.value if hasattr(status, 'value') else str(status)
                print(f"{dep}: {status_str}")
    
    def print_errors(self, errors: list):
        """
        Print any errors encountered.
        
        Args:
            errors: List of error messages.
        """
        if not errors:
            return
        
        if RICH_AVAILABLE:
            error_panel = Panel(
                "\n".join(errors),
                title="[red]Errors[/red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(error_panel)
        else:
            print("\nErrors:")
            print("-" * 40)
            for error in errors:
                print(f"  - {error}")
    
    def run_checks(self):
        """Run all system checks and display results."""
        self.print_header()
        
        # Check write permissions
        if RICH_AVAILABLE:
            self.console.print("\n[bold]Checking Write Permissions...[/bold]")
        else:
            print("\nChecking Write Permissions...")
        
        write_ok = self.checker.check_write_permissions()
        self.print_check_result(
            "Write permissions in home directory",
            write_ok,
            f"Home: {self.checker.home_dir}"
        )
        
        # Detect window manager
        if RICH_AVAILABLE:
            self.console.print("\n[bold]Detecting Window Manager...[/bold]")
        else:
            print("\nDetecting Window Manager...")
        
        wm = self.checker.detect_window_manager()
        self.print_check_result(
            "Window manager detection",
            wm != WindowManager.UNKNOWN,
            f"Detected: {wm.value}"
        )
        
        # Check dependencies
        if RICH_AVAILABLE:
            self.console.print("\n[bold]Checking Dependencies...[/bold]")
        else:
            print("\nChecking Dependencies...")
        
        dependencies = self.checker.check_critical_dependencies()
        self.print_dependency_table(dependencies)
        
        # Print errors if any
        errors = self.checker.get_errors()
        if errors:
            self.print_errors(errors)
        
        # Print summary
        if RICH_AVAILABLE:
            self.console.print("\n[bold]Summary[/bold]")
            summary = self.checker.get_summary()
            
            # Count installed dependencies
            installed = sum(1 for s in dependencies.values() if s == DependencyStatus.INSTALLED)
            total = len(dependencies)
            
            summary_text = f"""
Write Permissions: {'[green]OK[/green]' if write_ok else '[red]FAILED[/red]'}
Window Manager: {wm.value}
Dependencies: {installed}/{total} installed
            """
            self.console.print(Panel(summary_text.strip(), border_style="cyan"))
        else:
            print("\nSummary:")
            print("-" * 40)
            print(f"Write Permissions: {'OK' if write_ok else 'FAILED'}")
            print(f"Window Manager: {wm.value}")
            installed = sum(1 for s in dependencies.values() if s == DependencyStatus.INSTALLED)
            total = len(dependencies)
            print(f"Dependencies: {installed}/{total} installed")
        
        return write_ok and wm != WindowManager.UNKNOWN


def main():
    """Main entry point for system check CLI."""
    try:
        cli = SystemCheckCLI()
        success = cli.run_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            print("\n[yellow]Interrupted by user[/yellow]")
        else:
            print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        if RICH_AVAILABLE:
            print(f"\n[red]Unexpected error: {e}[/red]")
        else:
            print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
