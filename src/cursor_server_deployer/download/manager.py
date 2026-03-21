'''
Download manager for Cursor server
'''

import os
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import requests
import typer
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn
)

from .strategies import DownloadStrategy, StrategyFactory
from cursor_server_deployer.version.detector import CursorVersion


class DownloadManager:
    '''Manages Cursor server downloads'''

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            self.cache_dir = Path.home() / '.cursor-server-deployer' / 'cache'
        else:
            self.cache_dir = cache_dir

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()

    def download(
        self,
        version_info: CursorVersion,
        arch: str = 'x64',
        os_type: str = 'linux',
        force: bool = False,
        package_type: str = 'server'
    ) -> Optional[Path]:
        '''
        Download Cursor server for given version and architecture

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)
            force: Force re-download even if file exists
            package_type: Type of package to download ('server' or 'cli')

        Returns:
            Path to downloaded file
        '''
        # Strategy and URL info
        strategy = StrategyFactory().get_strategy(version_info.version)

        # Determine package URL and filename based on package type
        if package_type == 'cli':
            url = strategy.get_cli_download_url(version_info, arch, os_type)
            filename = strategy.get_cli_filename(version_info, arch, os_type)
        else:
            url = strategy.get_download_url(version_info, arch, os_type)
            filename = strategy.get_filename(version_info, arch, os_type)

        local_path = self.cache_dir / filename
        temp_path = self.cache_dir / f'{filename}.downloading'

        # --- Current state output ---
        if self.console:
            self.console.print(f'[bold cyan]Current Download State:[/bold cyan]')
            self.console.print(f'[dim]Target file: {local_path}[/dim]')

            # Check if cache directory exists
            cache_exists = self.cache_dir.exists()
            self.console.print(f'[dim]Cache directory exists: {cache_exists}[/dim]')

        # Check if target file exists
        target_exists = local_path.exists()
        if self.console:
            self.console.print(f'[dim]Target file exists: {target_exists}[/dim]')

        # Force flag value
        if self.console:
            self.console.print(f'[dim]Force flag: {force}[/dim]')

        # If target file exists, show its size
        if target_exists:
            file_size = local_path.stat().st_size
            if self.console:
                self.console.print(f'[dim]File size: {file_size} bytes[/dim]')
            if file_size == 0:
                if self.console:
                    self.console.print('[yellow]Warning: Target file is empty![/yellow]')

        if self.console:
            self.console.print(f'[dim]Download URL: {url}[/dim]')

        # Check if file already exists
        if self.console:
            self.console.print(f'[dim]Cache check: Checking if {local_path} exists...[/dim]')
        if self.console:
            self.console.print(f'[dim]Cache directory: {self.cache_dir}[/dim]')
        if self.console:
            self.console.print(f'[dim]Cache directory exists: {self.cache_dir.exists()}[/dim]')
        if self.console:
            self.console.print(f'[dim]Force flag: {force}[/dim]')

        # First check: if force=True, always download
        if force:
            if self.console:
                self.console.print('[yellow]→[/yellow] Force download enabled, ignoring cache...')
            return self._download_file_with_fallback(url, temp_path, local_path, package_type, version_info)

        # Second check: if file exists, use cache
        if local_path.exists():
            if self.console:
                self.console.print(f'[dim]Cache check: File exists, checking size...[/dim]')
            if self.console:
                self.console.print(f'[dim]File size: {local_path.stat().st_size} bytes[/dim]')
            if local_path.stat().st_size > 0:
                if self.console:
                    self.console.print(f'[green]OK[/green] Using cached file: {local_path}')
                return local_path
            else:
                if self.console:
                    self.console.print('[yellow]→[/yellow] Cached file is empty, redownloading...')
                return self._download_file_with_fallback(url, temp_path, local_path, package_type, version_info)
        else:
            if self.console:
                self.console.print('[yellow]→[/yellow] No cached file found, downloading...')
            # List all files in cache directory for debugging
            if self.cache_dir.exists():
                files = list(self.cache_dir.glob('*.tar.gz'))
                if self.console:
                    self.console.print(f'[dim]Files in cache: {len(files)}[/dim]')
                for f in files:
                    if self.console:
                        self.console.print(f'[dim]  - {f.name} (size: {f.stat().st_size} bytes)[/dim]')
            return self._download_file_with_fallback(url, temp_path, local_path, package_type, version_info)

    def _download_file(self, url: str, local_path: Path, version_info: Optional[CursorVersion] = None, package_type: str = 'server'):
        '''Download file with progress bar'''
        # Parse URL for filename (fallback)
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or 'cursor-server.tar.gz'

        # Start download with proper User-Agent
        if version_info:
            headers = {
                'User-Agent': f'Cursor/{version_info.version} (Windows; Remote-SSH)'
            }
        else:
            # Fallback User-Agent if version_info is not available
            headers = {
                'User-Agent': 'Cursor/0.0.0 (Windows; Remote-SSH)'
            }
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with Progress(
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:

            package_name = 'CLI' if package_type == 'cli' else 'Server'
            task = progress.add_task(
                f'[cyan]Downloading Cursor {package_name}[/cyan]',
                total=total_size
            )

            # Write file in chunks
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

    def get_cached_file(
        self,
        version_info: CursorVersion,
        arch: str = 'x64',
        os_type: str = 'linux',
        package_type: str = 'server'
    ) -> Optional[Path]:
        '''
        Get cached file if exists

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS
            package_type: Type of package to get ('server' or 'cli')

        Returns:
            Path to cached file or None
        '''
        strategy = StrategyFactory().get_strategy(version_info.version)

        if package_type == 'cli':
            filename = strategy.get_cli_filename(version_info, arch, os_type)
        else:
            filename = strategy.get_filename(version_info, arch, os_type)

        local_path = self.cache_dir / filename

        if self.console:
            self.console.print(f'[dim]Cache check: Looking for {filename} in {self.cache_dir}[/dim]')
        if self.console:
            self.console.print(f'[dim]Full path: {local_path}[/dim]')
        if self.console:
            self.console.print(f'[dim]Cache directory exists: {self.cache_dir.exists()}[/dim]')
        if self.console:
            self.console.print(f'[dim]Cache file exists: {local_path.exists()}[/dim]')

        if local_path.exists():
            if self.console:
                self.console.print(f'[dim]Cache check: Found cached file: {local_path}[/dim]')
            return local_path
        else:
            if self.console:
                self.console.print(f'[dim]Cache check: No cached file found: {local_path}[/dim]')
            return None

    def download_cli_package(
        self,
        version_info: CursorVersion,
        arch: str = 'x64',
        force: bool = False
    ) -> Optional[Path]:
        '''
        Download CLI package for given version

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            force: Force re-download even if file exists

        Returns:
            Path to downloaded CLI package or None if download failed
        '''
        try:
            # Strategy and URL info
            strategy = StrategyFactory().get_strategy(version_info.version)
            url = strategy.get_cli_download_url(version_info, arch, 'linux')
            filename = strategy.get_cli_filename(version_info, arch, 'linux')
            local_path = self.cache_dir / filename
            temp_path = self.cache_dir / f'{filename}.downloading'

            # Check if file already exists
            if force:
                if self.console:
                    self.console.print('[yellow]→[/yellow] Force download enabled, ignoring cache...')
                return self._download_file_with_fallback(url, temp_path, local_path, 'cli', version_info)

            if local_path.exists():
                if local_path.stat().st_size > 0:
                    if self.console:
                        self.console.print(f'[green]OK[/green] Using cached CLI package: {local_path}')
                    return local_path
                else:
                    if self.console:
                        self.console.print(f'[yellow]→[/yellow] Cached CLI package is empty, redownloading...')
                    return self._download_file_with_fallback(url, temp_path, local_path, 'cli', version_info)
            else:
                if self.console:
                    self.console.print('[yellow]→[/yellow] No cached CLI package found, downloading...')
                return self._download_file_with_fallback(url, temp_path, local_path, 'cli', version_info)
        except Exception as e:
            if self.console:
                self.console.print(f'[yellow]⚠[/yellow] CLI package download failed: {e}')
            if self.console:
                self.console.print('[dim]Continuing with server package only...[/dim]')
            return None

    def _download_file_with_fallback(self, url: str, temp_path: Path, local_path: Path, package_type: str = 'server', version_info: Optional[CursorVersion] = None) -> Optional[Path]:
        '''Download file with fallback handling'''
        # Download to temporary file
        if package_type == 'cli':
            if self.console:
                self.console.print(
                    f'[yellow]→[/yellow] Downloading Cursor CLI package...'
                )
        else:
            if self.console:
                self.console.print(
                    f'[yellow]→[/yellow] Downloading Cursor server...'
                )
        if self.console:
            self.console.print(f'[dim]URL: {url}[/dim]')
        if self.console:
            self.console.print(f'[dim]Temporary destination: {temp_path}[/dim]')

        try:
            self._download_file(url, temp_path, version_info, package_type)

            # Rename temporary file to final name
            try:
                temp_path.rename(local_path)
            except Exception as e:
                # If rename fails because file already exists, clean up temp file and return existing file
                if 'already exists' in str(e) and local_path.exists():
                    if temp_path.exists():
                        temp_path.unlink()
                    if self.console:
                        self.console.print(f'[green]OK[/green] Using existing file: {local_path}')
                    return local_path
                raise e

            if self.console:
                self.console.print(
                    f'[green]OK[/green] Download complete: {local_path}'
                )
            return local_path

        except requests.exceptions.RequestException as e:
            if self.console:
                self.console.print(
                    f'[yellow]⚠[/yellow] Download failed: {e}'
                )
            # Clean up temporary file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return None

    def clear_cache(self, older_than_days: Optional[Union[int, typer.models.OptionInfo]] = None):
        '''
        Clear cache

        Args:
            older_than_days: Only clear files older than this many days.
                            None clears all files.
        '''
        import time

        # Handle OptionInfo object from typer
        if hasattr(older_than_days, 'default'):
            # This is an OptionInfo object, use its default value
            days = older_than_days.default
        else:
            # This is the actual value
            days = older_than_days

        if days is None:
            # Clear all files
            for file in self.cache_dir.glob('*.tar.gz'):
                file.unlink()
            if self.console:
                self.console.print(
                    f'[green]OK[/green] Cache cleared ({self.cache_dir})'
                )
        else:
            # Clear old files
            cutoff_time = time.time() - (days * 86400)
            cleared_count = 0
            for file in self.cache_dir.glob('*.tar.gz'):
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    cleared_count += 1

            if self.console:
                self.console.print(
                    f'[green]OK[/green] Cleared {cleared_count} old cache files'
                )
