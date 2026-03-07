"""
SSH connection management
"""

import getpass
from pathlib import Path
from typing import Optional

import paramiko
from rich.console import Console

from cursor_server_deployer.config.models import ServerConfig


class SSHConnectionPool:
    """
    Manages SSH connections to remote servers

    IMPORTANT: Passwords are NOT cached. Each connection requires
    password input unless SSH key authentication is configured.
    """

    def __init__(self):
        self.console = Console()
        self.connections = {}

    def get_connection(self, server_config: ServerConfig) -> paramiko.SSHClient:
        """
        Get SSH connection to server

        Args:
            server_config: Server configuration

        Returns:
            Connected SSH client
        """
        cache_key = server_config.unique_key

        # Check if we already have a connection
        if cache_key in self.connections:
            # Test if connection is still alive
            if self._is_connection_alive(self.connections[cache_key]):
                return self.connections[cache_key]
            else:
                # Remove dead connection
                del self.connections[cache_key]

        # Create new connection
        if server_config.auth_method == "key":
            connection = self._connect_with_key(server_config)
        else:
            # Password auth - always ask for password (no caching)
            password = self._get_password(server_config)
            connection = self._connect_with_password(server_config, password)

        self.connections[cache_key] = connection
        return connection

    def _connect_with_password(
        self,
        server_config: ServerConfig,
        password: str
    ) -> paramiko.SSHClient:
        """Connect using password authentication"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server_config.host,
                port=server_config.port,
                username=server_config.user,
                password=password,
                timeout=30
            )

            self.console.print(
                f"[green]✓[/green] Connected to {server_config.connection_string}"
            )
            return client

        except paramiko.AuthenticationException:
            self.console.print(
                f"[red]✗[/red] Authentication failed for {server_config.connection_string}"
            )
            raise RuntimeError(
                f"Authentication failed for {server_config.connection_string}"
            )
        except Exception as e:
            self.console.print(
                f"[red]✗[/red] Connection failed to {server_config.connection_string}: {e}"
            )
            raise RuntimeError(
                f"Failed to connect to {server_config.connection_string}: {e}"
            )

    def _connect_with_key(self, server_config: ServerConfig) -> paramiko.SSHClient:
        """Connect using SSH key authentication"""
        try:
            # Load private key
            if not server_config.key_path:
                raise RuntimeError("No key path configured")

            key_path = Path(server_config.key_path).expanduser()
            if not key_path.exists():
                raise RuntimeError(f"Key file not found: {key_path}")

            private_key = paramiko.Ed25519Key.from_private_key_file(str(key_path))

            # Connect with key
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server_config.host,
                port=server_config.port,
                username=server_config.user,
                pkey=private_key,
                timeout=30
            )

            self.console.print(
                f"[green]✓[/green] Connected to {server_config.connection_string} (SSH key)"
            )
            return client

        except Exception as e:
            self.console.print(
                f"[red]✗[/red] SSH key connection failed for {server_config.connection_string}: {e}"
            )
            raise RuntimeError(
                f"Failed to connect with SSH key to {server_config.connection_string}: {e}"
            )

    def _get_password(self, server_config: ServerConfig) -> str:
        """
        Get password for server

        IMPORTANT: This asks for password every time. No caching.
        Password is unique per host+port+user combination.
        """
        return getpass.getpass(
            f"Enter password for {server_config.connection_string}: "
        )

    def _is_connection_alive(self, client: paramiko.SSHClient) -> bool:
        """Test if SSH connection is still alive"""
        try:
            transport = client.get_transport()
            if transport and transport.is_active():
                transport.send_ignore()
                return True
            return False
        except Exception:
            return False

    def close_all(self):
        """Close all active connections"""
        for cache_key, client in self.connections.items():
            try:
                client.close()
            except Exception:
                pass
        self.connections.clear()

    def close_connection(self, server_config: ServerConfig):
        """Close connection to specific server"""
        cache_key = server_config.unique_key
        if cache_key in self.connections:
            try:
                self.connections[cache_key].close()
            except Exception:
                pass
            del self.connections[cache_key]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()
