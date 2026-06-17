"""
Main Application - Linux Tweaker v2.0.0

Integrates SystemChecker, FileManager, and UIBuilder to provide
a robust ricing manager for Linux desktop environments.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.system_checker import SystemChecker, WindowManager
from src.file_manager import FileManager
from src.ui_builder import UIBuilder, Menu, MenuItem, MenuAction


class LinuxTweakerApp:
    """
    Main application class for Linux Tweaker v2.0.0.
    
    Coordinates between SystemChecker, FileManager, and UIBuilder
    to provide a complete ricing management experience.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.system_checker = SystemChecker()
        self.file_manager = FileManager()
        self.ui = UIBuilder()
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the application by running system checks.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        """
        try:
            # Check write permissions
            write_ok = self.system_checker.check_write_permissions()
            if not write_ok:
                self.ui.add_error("Write permissions check failed")
                return False
            
            # Detect window manager
            wm = self.system_checker.detect_window_manager()
            if wm == WindowManager.UNKNOWN:
                self.ui.add_warning("Unknown window manager detected")
            
            # Check dependencies
            deps = self.system_checker.check_critical_dependencies()
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.ui.add_error(f"Initialization failed: {e}")
            return False
    
    def show_system_status(self):
        """Display system status information."""
        try:
            self.ui.print_header("System Status")
            
            # Write permissions
            write_ok = self.system_checker.check_write_permissions()
            self.ui.print_success("Write permissions" if write_ok else "Write permissions failed")
            
            # Window manager
            wm = self.system_checker.detect_window_manager()
            self.ui.print_info(f"Window Manager: {wm.value}")
            
            # Dependencies
            deps = self.system_checker.check_critical_dependencies()
            self.ui.print_info("\nDependencies:")
            for dep, status in deps.items():
                status_str = status.value
                if status_str == "installed":
                    self.ui.print_success(f"  {dep}")
                elif status_str == "not_installed":
                    self.ui.print_warning(f"  {dep} (not installed)")
                else:
                    self.ui.print_error(f"  {dep} (error)")
            
            # Errors
            errors = self.system_checker.get_errors()
            if errors:
                self.ui.print_errors()
            
        except Exception as e:
            self.ui.add_error(f"Error showing system status: {e}")
    
    def show_backups(self):
        """Display available backups."""
        try:
            self.ui.print_header("Backup Management")
            
            backups = self.file_manager.list_backups()
            
            if not backups:
                self.ui.print_info("No backups found")
                return
            
            self.ui.print_info(f"Found {len(backups)} backup(s):")
            for i, backup in enumerate(backups, 1):
                self.ui.print_info(f"{i}. {backup['name']}")
                self.ui.print_info(f"   Original: {backup['original_name']}")
                self.ui.print_info(f"   Timestamp: {backup['timestamp']}")
                self.ui.print_info(f"   Type: {backup['type']}")
            
        except Exception as e:
            self.ui.add_error(f"Error showing backups: {e}")
    
    def create_main_menu(self) -> Menu:
        """
        Create the main application menu.
        
        Returns:
            Menu: Main menu with all options.
        """
        items = [
            MenuItem(
                "System Check",
                MenuAction.EXECUTE,
                callback=self.show_system_status,
                description="Check system environment and dependencies"
            ),
            MenuItem(
                "Manage Backups",
                MenuAction.EXECUTE,
                callback=self.show_backups,
                description="View and manage configuration backups"
            ),
            MenuItem(
                "Apply Preset",
                MenuAction.EXECUTE,
                callback=self.apply_preset_menu,
                description="Apply a ricing preset"
            ),
            MenuItem(
                "Reset Configs",
                MenuAction.EXECUTE,
                callback=self.reset_configs,
                description="Reset configurations to defaults"
            ),
            MenuItem(
                "Exit",
                MenuAction.EXIT,
                description="Exit the application"
            )
        ]
        
        return Menu("Linux Tweaker v2.0.0 - Main Menu", items)
    
    def apply_preset_menu(self):
        """Show preset application menu (placeholder)."""
        self.ui.print_header("Apply Preset")
        self.ui.print_info("Preset application coming soon...")
        self.ui.print_info("This feature will be implemented in the next phase.")
        return True
    
    def reset_configs(self):
        """Reset configurations (placeholder)."""
        self.ui.print_header("Reset Configurations")
        self.ui.print_info("Configuration reset coming soon...")
        self.ui.print_info("This feature will be implemented in the next phase.")
        return True
    
    def run(self):
        """Run the main application."""
        try:
            # Initialize
            if not self.initialize():
                self.ui.print_error("Failed to initialize application")
                return 1
            
            # Create and run main menu
            main_menu = self.create_main_menu()
            self.ui.run_menu(main_menu)
            
            return 0
            
        except KeyboardInterrupt:
            self.ui.print_info("\nInterrupted by user")
            return 130
        except Exception as e:
            self.ui.print_error(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point."""
    try:
        app = LinuxTweakerApp()
        exit_code = app.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
