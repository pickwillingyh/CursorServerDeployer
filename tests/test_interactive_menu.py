#!/usr/bin/env python3
"""
Test script for interactive menu improvements
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.utils.interactive_menu import InteractiveMenu
from rich.console import Console

def test_interactive_menu():
    """Test the improved interactive menu"""
    print("Testing Interactive Menu...")

    menu = InteractiveMenu()
    console = Console()

    # Test single select
    console.print("\n[bold cyan]Testing single selection:[/bold cyan]")
    choices = [
        {"name": "Option 1 - Deploy", "value": "deploy"},
        {"name": "Option 2 - Add Server", "value": "add"},
        {"name": "Option 3 - Exit", "value": "exit"},
    ]

    try:
        result = menu.select_single(
            "Test Menu - Select an option:",
            choices,
            "Use ↑/↓ to move, Enter to confirm, Esc to cancel"
        )
        console.print(f"[green]Selected: {result}[/green]")
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled by user[/yellow]")

    # Test multi-select
    console.print("\n[bold cyan]Testing multi-selection:[/bold cyan]")
    try:
        selected = menu.select_multiple(
            "Test Menu - Select multiple options:",
            choices,
            "Use ↑/↓ to move, Space to select, Enter to confirm, Esc to cancel"
        )
        console.print(f"[green]Selected: {selected}[/green]")
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled by user[/yellow]")

    # Test confirmation
    console.print("\n[bold cyan]Testing confirmation:[/bold cyan]")
    try:
        confirm = menu.confirm("Proceed with deployment?", default=False)
        console.print(f"[green]Confirmed: {confirm}[/green]")
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled by user[/yellow]")

    # Test prompt
    console.print("\n[bold cyan]Testing prompt:[/bold cyan]")
    try:
        text = menu.prompt("Enter server host:")
        console.print(f"[green]Input: {text}[/green]")
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled by user[/yellow]")

if __name__ == "__main__":
    test_interactive_menu()