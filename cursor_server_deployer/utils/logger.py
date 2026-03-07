"""
Logger utility for console output
"""

from rich.console import Console


class Logger:
    """
    Logger with support for simple and verbose output modes
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console()

    def info(self, message: str):
        """Print info message"""
        self.console.print(message)

    def debug(self, message: str):
        """Print debug message (only in verbose mode)"""
        if self.verbose:
            self.console.print(f"[dim]{message}[/dim]")

    def success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✓[/green] {message}")

    def error(self, message: str):
        """Print error message"""
        self.console.print(f"[red]✗[/red] {message}")

    def warning(self, message: str):
        """Print warning message"""
        self.console.print(f"[yellow]![/yellow] {message}")

    def progress(self, message: str, percentage: Optional[int] = None):
        """Print progress message"""
        if percentage is not None:
            self.console.print(f"[yellow]→[/yellow] {message} [{percentage}%]")
        else:
            self.console.print(f"[yellow]→[/yellow] {message}")

    def section(self, message: str):
        """Print section header"""
        self.console.print(f"\n[bold cyan]{message}[/bold cyan]")

    def blank(self):
        """Print blank line"""
        self.console.print("")

    def print(self, message: str):
        """Print raw message"""
        self.console.print(message)

    def set_verbose(self, verbose: bool):
        """Set verbose mode"""
        self.verbose = verbose
