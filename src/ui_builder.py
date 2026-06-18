"""
UIBuilder - Terminal User Interface builder for the ricing manager.

This module provides a beautiful TUI using the rich library for menu navigation
and user interaction. All operations are wrapped in try/except blocks for zero-crash policy.
"""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.layout import Layout
    from rich.align import Align
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class MenuAction(Enum):
    """Menu action types."""
    NAVIGATE = "navigate"
    EXECUTE = "execute"
    BACK = "back"
    EXIT = "exit"


class MenuItem:
    """Represents a menu item."""
    
    def __init__(
        self,
        name: str,
        action: MenuAction,
        callback: Optional[Callable] = None,
        submenu: Optional['Menu'] = None,
        description: str = ""
    ):
        """
        Initialize a menu item.
        
        Args:
            name: Display name of the item.
            action: Type of action this item performs.
            callback: Function to call if action is EXECUTE.
            submenu: Submenu to navigate to if action is NAVIGATE.
            description: Description of the menu item.
        """
        self.name = name
        self.action = action
        self.callback = callback
        self.submenu = submenu
        self.description = description


class Menu:
    """Represents a menu with items."""
    
    def __init__(self, title: str, items: List[MenuItem]):
        """
        Initialize a menu.
        
        Args:
            title: Menu title.
            items: List of menu items.
        """
        self.title = title
        self.items = items
        self.parent: Optional['Menu'] = None


class UIBuilder:
    """
    Builds and manages the Terminal User Interface.
    
    Features:
    - Beautiful TUI with rich library
    - Hierarchical menu system
    - Interactive navigation
    - Error handling
    - Status display
    """
    
    def __init__(self):
        """Initialize UIBuilder."""
        self.console = Console() if RICH_AVAILABLE else None
        self.current_menu: Optional[Menu] = None
        self.menu_stack: List[Menu] = []
        self._errors: List[str] = []
        self._status_messages: List[str] = []
    
    def add_error(self, error: str):
        """
        Add an error message.
        
        Args:
            error: Error message to add.
        """
        self._errors.append(error)
    
    def add_status(self, status: str):
        """
        Add a status message.
        
        Args:
            status: Status message to add.
        """
        self._status_messages.append(status)
    
    def clear_messages(self):
        """Clear all error and status messages."""
        self._errors.clear()
        self._status_messages.clear()
    
    def print_header(self, title: str = "Linux Tweaker v2.0.0"):
        """
        Print the application header.
        
        Args:
            title: Header title.
        """
        if RICH_AVAILABLE and self.console:
            header = Panel(
                Text(title, style="bold cyan"),
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(header)
        else:
            print("=" * 50)
            print(title)
            print("=" * 50)
    
    def print_menu(self, menu: Menu):
        """
        Print a menu with its items.
        
        Args:
            menu: Menu to display.
        """
        if RICH_AVAILABLE and self.console:
            # Create table for menu items
            table = Table(title=menu.title, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Description", style="white")
            
            for i, item in enumerate(menu.items, 1):
                option_text = f"[{i}]"
                desc_text = f"{item.name}"
                if item.description:
                    desc_text += f" - {item.description}"
                table.add_row(option_text, desc_text)
            
            # Add back option if not root menu
            if menu.parent:
                table.add_row("[0]", "Back to previous menu")
            
            table.add_row("[q]", "Quit")
            
            self.console.print(table)
        else:
            print(f"\n{menu.title}")
            print("-" * 40)
            for i, item in enumerate(menu.items, 1):
                print(f"[{i}] {item.name}")
                if item.description:
                    print(f"     {item.description}")
            if menu.parent:
                print("[0] Back to previous menu")
            print("[q] Quit")
    
    def print_status(self):
        """Print status messages."""
        if not self._status_messages:
            return
        
        if RICH_AVAILABLE and self.console:
            status_text = "\n".join(self._status_messages)
            status_panel = Panel(
                status_text,
                title="[green]Status[/green]",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(status_panel)
        else:
            print("\nStatus:")
            print("-" * 40)
            for status in self._status_messages:
                print(f"  - {status}")
    
    def print_errors(self):
        """Print error messages."""
        if not self._errors:
            return
        
        if RICH_AVAILABLE and self.console:
            error_text = "\n".join(self._errors)
            error_panel = Panel(
                error_text,
                title="[red]Errors[/red]",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(error_panel)
        else:
            print("\nErrors:")
            print("-" * 40)
            for error in self._errors:
                print(f"  - {error}")
    
    def get_user_choice(self, menu: Menu) -> Optional[int]:
        """
        Get user choice from menu.
        
        Args:
            menu: Current menu.
            
        Returns:
            Optional[int]: Selected option number, or None for quit.
        """
        try:
            if RICH_AVAILABLE and self.console:
                choice = self.console.input(
                    "\n[cyan]Choose an option[/cyan] [cyan][0-{}][/cyan][cyan]/q[/cyan]: "
                    .format(len(menu.items))
                )
            else:
                choice = input(f"\nChoose an option [0-{len(menu.items)}]/q: ")
            
            choice = choice.strip().lower()
            
            # Handle quit
            if choice == 'q':
                return None
            
            # Handle back
            if choice == '0' and menu.parent:
                return 0
            
            # Handle number selection
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(menu.items):
                    return choice_num
                else:
                    self.add_error(f"Invalid choice: {choice_num}")
                    return None
            except ValueError:
                self.add_error(f"Invalid input: {choice}")
                return None
                
        except KeyboardInterrupt:
            return None
        except Exception as e:
            self.add_error(f"Error getting user choice: {e}")
            return None
    
    def execute_menu_item(self, item: MenuItem) -> bool:
        """
        Execute a menu item action.
        
        Args:
            item: Menu item to execute.
            
        Returns:
            bool: True if should continue, False if should exit.
        """
        try:
            if item.action == MenuAction.NAVIGATE and item.submenu:
                # Navigate to submenu
                item.submenu.parent = self.current_menu
                self.menu_stack.append(self.current_menu)
                self.current_menu = item.submenu
                return True
            
            elif item.action == MenuAction.EXECUTE and item.callback:
                # Execute callback
                try:
                    result = item.callback()
                    if result is False:
                        return False
                    return True
                except Exception as e:
                    self.add_error(f"Error executing {item.name}: {e}")
                    return True
            
            elif item.action == MenuAction.BACK:
                # Go back to previous menu
                if self.menu_stack:
                    self.current_menu = self.menu_stack.pop()
                return True
            
            elif item.action == MenuAction.EXIT:
                # Exit application
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Error executing menu item: {e}")
            return True
    
    def run_menu(self, menu: Menu):
        """
        Run a menu interactively.
        
        Args:
            menu: Menu to run.
        """
        self.current_menu = menu
        self.menu_stack.clear()
        
        while self.current_menu:
            # Clear screen
            if RICH_AVAILABLE and self.console:
                self.console.clear()
            else:
                print("\n" * 50)
            
            # Clear messages for new iteration
            self.clear_messages()
            
            # Print header
            self.print_header()
            
            # Print menu
            self.print_menu(self.current_menu)
            
            # Get user choice
            choice = self.get_user_choice(self.current_menu)
            
            # Handle quit
            if choice is None:
                break
            
            # Handle back
            if choice == 0 and self.current_menu.parent:
                self.current_menu = self.menu_stack.pop()
                continue
            
            # Execute menu item
            if 1 <= choice <= len(self.current_menu.items):
                item = self.current_menu.items[choice - 1]
                should_continue = self.execute_menu_item(item)
                
                if not should_continue:
                    break
                
                # Print any status/errors
                self.print_status()
                self.print_errors()
                
                # Wait for user to continue
                if RICH_AVAILABLE and self.console:
                    self.console.input("\nPress Enter to continue...")
                else:
                    input("\nPress Enter to continue...")
    
    def print_info(self, message: str):
        """
        Print an informational message.
        
        Args:
            message: Message to print.
        """
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[cyan]{message}[/cyan]")
        else:
            print(message)
    
    def print_success(self, message: str):
        """
        Print a success message.
        
        Args:
            message: Message to print.
        """
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[green]✓ {message}[/green]")
        else:
            print(f"✓ {message}")
    
    def print_warning(self, message: str):
        """
        Print a warning message.
        
        Args:
            message: Message to print.
        """
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[yellow]⚠ {message}[/yellow]")
        else:
            print(f"⚠ {message}")
    
    def print_error(self, message: str):
        """
        Print an error message.
        
        Args:
            message: Message to print.
        """
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[red]✗ {message}[/red]")
        else:
            print(f"✗ {message}")
    
    def confirm(self, message: str) -> bool:
        """
        Ask user for confirmation.
        
        Args:
            message: Confirmation message.
            
        Returns:
            bool: True if user confirms, False otherwise.
        """
        try:
            if RICH_AVAILABLE and self.console:
                choice = self.console.input(f"[yellow]{message} [y/N]:[/yellow] ")
            else:
                choice = input(f"{message} [y/N]: ")
            
            return choice.strip().lower() in ['y', 'yes']
            
        except KeyboardInterrupt:
            return False
        except Exception as e:
            self.add_error(f"Error getting confirmation: {e}")
            return False
    
    def get_input(self, message: str, default: str = "") -> str:
        """
        Get user input.
        
        Args:
            message: Prompt message.
            default: Default value if user just presses Enter.
            
        Returns:
            str: User input or default.
        """
        try:
            if RICH_AVAILABLE and self.console:
                if default:
                    prompt = f"[cyan]{message}[/cyan] [cyan][{default}][/cyan]: "
                else:
                    prompt = f"[cyan]{message}[/cyan]: "
                choice = self.console.input(prompt)
            else:
                if default:
                    prompt = f"{message} [{default}]: "
                else:
                    prompt = f"{message}: "
                choice = input(prompt)
            
            choice = choice.strip()
            if not choice and default:
                return default
            return choice
            
        except KeyboardInterrupt:
            return default
        except Exception as e:
            self.add_error(f"Error getting input: {e}")
            return default
