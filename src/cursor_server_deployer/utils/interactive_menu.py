'''
Interactive menu utilities with better cross-platform compatibility
'''

import sys
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


class InteractiveMenu:
    '''Cross-platform interactive menu with better compatibility'''

    def __init__(self):
        self.console = Console()

    def select_single(
        self,
        message: str,
        choices: List[Dict[str, Any]],
        instruction: str = 'Use ↑/↓ to move, Enter to confirm, Esc to cancel'
    ) -> Optional[Any]:
        '''Single select menu'''
        if QUESTIONARY_AVAILABLE:
            try:
                return questionary.select(
                    message=message,
                    choices=[choice['name'] for choice in choices],
                    qmark='◆',
                    pointer='➤',
                    instruction=instruction
                ).ask()
            except (KeyboardInterrupt, EOFError):
                return None

        # Fallback to simple typer prompts
        self.console.print(f'\n[bold]{message}[/bold]')
        for i, choice in enumerate(choices, 1):
            self.console.print(f'  {i}. {choice['name']}')

        try:
            answer = input(f'\n{instruction}\n> ')
            if answer.lower() in ['q', 'quit', 'exit']:
                return None

            try:
                index = int(answer) - 1
                if 0 <= index < len(choices):
                    return choices[index]['value']
                else:
                    self.console.print('[red]Invalid selection[/red]')
                    return None
            except ValueError:
                self.console.print('[red]Please enter a number[/red]')
                return None
        except (KeyboardInterrupt, EOFError):
            return None

    def select_multiple(
        self,
        message: str,
        choices: List[Dict[str, Any]],
        instruction: str = 'Use ↑/↓ to move, Space to select, Enter to confirm, Esc to cancel'
    ) -> List[Any]:
        '''Multi-select menu'''
        if QUESTIONARY_AVAILABLE:
            try:
                selected_names = questionary.checkbox(
                    message=message,
                    choices=[choice['name'] for choice in choices],
                    qmark='◆',
                    instruction=instruction
                ).ask()

                if selected_names is None:
                    return []

                # Map names back to values
                selected_values = []
                for choice in choices:
                    if choice['name'] in selected_names:
                        selected_values.append(choice['value'])
                return selected_values
            except (KeyboardInterrupt, EOFError):
                return []

        # Fallback to simple selection
        self.console.print(f'\n[bold]{message}[/bold]')
        for i, choice in enumerate(choices, 1):
            self.console.print(f'  {i}. {choice['name']}')

        try:
            answer = input(f'\n{instruction}\n> ')
            if answer.lower() in ['q', 'quit', 'exit']:
                return []

            selected_values = []
            for item in answer.split(','):
                try:
                    index = int(item.strip()) - 1
                    if 0 <= index < len(choices):
                        selected_values.append(choices[index]['value'])
                except ValueError:
                    continue
            return selected_values
        except (KeyboardInterrupt, EOFError):
            return []

    def confirm(self, message: str, default: bool = False) -> bool:
        '''Yes/No confirmation'''
        if QUESTIONARY_AVAILABLE:
            try:
                return questionary.confirm(message, default=default).ask()
            except (KeyboardInterrupt, EOFError):
                return False

        # Fallback
        try:
            answer = input(f'{message} [Y/n]: ').strip().lower()
            if answer in ['', 'y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            return default
        except (KeyboardInterrupt, EOFError):
            return False

    def prompt(self, message: str, default: Optional[str] = None) -> Optional[str]:
        '''Text input prompt'''
        if QUESTIONARY_AVAILABLE:
            try:
                return questionary.text(message, default=default).ask()
            except (KeyboardInterrupt, EOFError):
                return None

        # Fallback
        try:
            if default:
                answer = input(f'{message} [{default}]: ').strip()
                return answer if answer else default
            else:
                return input(f'{message}: ').strip()
        except (KeyboardInterrupt, EOFError):
            return None