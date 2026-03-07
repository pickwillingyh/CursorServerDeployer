"""
Download manager for Cursor server
"""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
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
    """Manages Cursor server downloads"""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            self.cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
        else:
            self.cache_dir = cache_dir

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()

    def download(
        self,
        version_info: CursorVersion,
        arch: str = "x64",
        os_type: str = "linux",
        force: bool = False
    ) -> Path:
        """
        Download Cursor server for given version and architecture

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)
            force: Force re-download even if file exists

        Returns:
            Path to downloaded file
        """
        strategy = StrategyFactory().get_strategy(version_info.version)
        url = strategy.get_download_url(version_info, arch, os_type)
        filename = strategy.get_filename(version_info, arch, os_type)
        local_path = self.cache_dir / filename

        # Check if file already exists
        if local_path.exists() and not force:
            self.console.print(
                f"[green]✓[/green] Using cached file: {local_path}"
            )
            return local_path

        # Download the file
        self.console.print(
            f"[yellow]→[/yellow] Downloading Cursor server..."
        )
        self.console.print(f"[dim]URL: {url}[/dim]")
        self.console.print(f"[dim]Destination: {local_path}[/dim]")

        try:
            self._download_file(url, local_path)
            self.console.print(
                f"[green]✓[/green] Download complete: {local_path}"
            )
            return local_path

        except requests.exceptions.RequestException as e:
            self.console.print(
                f"[red]✗[/red] Download failed: {e}"
            )
            raise RuntimeError(f"Failed to download Cursor server: {e}")

    def _download_file(self, url: str, local_path: Path):
        """Download file with progress bar"""
        # Parse URL for filename (fallback)
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "cursor-server.tar.gz"

        # Start download
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:

            task = progress.add_task(
                f"[cyan]Downloading {filename}[/cyan]",
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
        arch: str = "x64",
        os_type: str = "linux"
    ) -> Optional[Path]:
        """
        Get cached file if exists

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS

        Returns:
            Path to cached file or None
        """
        strategy = StrategyFactory().get_strategy(version_info.version)
        filename = strategy.get_filename(version_info, arch, os_type)
        local_path = self.cache_dir / filename

        if local_path.exists():
            return local_path
        return None

    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cache

        Args:
            older_than_days: Only clear files older than this many days.
                            None clears all files.
        """
        import time

        if older_than_days is None:
            # Clear all files
            for file in self.cache_dir.glob("*.tar.gz"):
                file.unlink()
            self.console.print(
                f"[green]✓[/green] Cache cleared ({self.cache_dir})"
            )
        else:
            # Clear old files
            cutoff_time = time.time() - (older_than_days * 86400)
            cleared_count = 0
            for file in self.cache_dir.glob("*.tar.gz"):
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    cleared_count += 1

            self.console.print(
                f"[green]✓[/green] Cleared {cleared_count} old cache files"
            )
