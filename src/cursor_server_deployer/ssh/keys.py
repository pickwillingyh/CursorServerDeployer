'''
SSH key management module
'''

import os
import socket
from pathlib import Path
from typing import Optional, Tuple

import paramiko
from rich.console import Console

from cursor_server_deployer.config.models import ServerConfig


class KeyManager:
    '''Manages SSH keys for remote server authentication'''

    STANDARD_SSH_DIR = Path.home() / '.ssh'

    def __init__(self):
        self.console = Console()
        self._ensure_ssh_dir()

    def _ensure_ssh_dir(self):
        '''Ensure standard SSH directory exists with correct permissions'''
        self.STANDARD_SSH_DIR.mkdir(mode=0o700, exist_ok=True)

    def get_key_path(self, server_config: ServerConfig) -> Tuple[Path, Path]:
        '''
        Get standard SSH key paths for a server

        Args:
            server_config: Server configuration

        Returns:
            Tuple of (private_key_path, public_key_path)
        '''
        # Use safe key name with host and port
        key_name = f'id_ed25519_cursor_{server_config.host}_{server_config.port}'
        private_key_path = self.STANDARD_SSH_DIR / key_name
        public_key_path = Path(str(private_key_path) + '.pub')

        return private_key_path, public_key_path

    def generate_key_pair(self) -> Tuple[paramiko.Ed25519Key, paramiko.Ed25519Key]:
        '''
        Generate ED25519 key pair (modern and secure)

        Returns:
            Tuple of (private_key, public_key)
        '''
        private_key = paramiko.Ed25519Key.generate()
        public_key = private_key.publickey()
        return private_key, public_key

    def save_keys(
        self,
        server_config: ServerConfig,
        private_key: paramiko.Ed25519Key,
        public_key: paramiko.Ed25519Key
    ) -> Tuple[Path, Path]:
        '''
        Save key pair to standard ~/.ssh directory

        Args:
            server_config: Server configuration
            private_key: Private key object
            public_key: Public key object

        Returns:
            Tuple of (private_key_path, public_key_path)
        '''
        private_path, public_path = self.get_key_path(server_config)

        # Save private key with permissions 600
        private_key.write_private_key_file(private_path)
        private_path.chmod(0o600)

        # Save public key with permissions 644
        with open(public_path, 'w') as f:
            f.write(f'{public_key.get_name()} {public_key.get_base64()}')
        public_path.chmod(0o644)

        self.console.print(
            f'[green]OK[/green] Keys saved to standard location:'
        )
        self.console.print(f'[dim]  Private: {private_path}[/dim]')
        self.console.print(f'[dim]  Public: {public_path}[/dim]')

        return private_path, public_path

    def setup_key_auth(
        self,
        server_config: ServerConfig,
        password: str
    ) -> bool:
        '''
        Setup SSH key authentication for a server

        Args:
            server_config: Server configuration (will be updated)
            password: Current password for the server

        Returns:
            True if setup successful, False otherwise
        '''
        try:
            self.console.print(
                f'\n[yellow]→[/yellow] Setting up SSH key authentication for {server_config.name}'
            )

            # 1. Generate key pair
            private_key, public_key = self.generate_key_pair()
            self.console.print('[green]OK[/green] Generated ED25519 key pair')

            # 2. Save keys to standard location
            private_path, public_path = self.save_keys(server_config, private_key, public_key)

            # 3. Upload public key to remote server
            self._upload_public_key(server_config, password, public_key)
            self.console.print('[green]OK[/green] Uploaded public key to server')

            # 4. Update ~/.ssh/config
            ssh_config_alias = self._update_ssh_config(server_config, private_path)
            self.console.print(f'[green]OK[/green] Updated SSH config (alias: {ssh_config_alias})')

            # 5. Test key login
            self.console.print('[yellow]→[/yellow] Testing SSH key login...')
            if self._test_key_login(server_config):
                self.console.print('[green]OK[/green] SSH key login successful!')

                # 6. Update server config
                server_config.auth_method = 'key'
                server_config.key_path = str(private_path)
                server_config.ssh_config_alias = ssh_config_alias
                server_config.key_setup = True

                return True
            else:
                self.console.print(
                    '[red]ERROR[/red] SSH key login failed. Rolling back...'
                )
                # Remove keys on failure
                private_path.unlink(missing_ok=True)
                public_path.unlink(missing_ok=True)
                return False

        except Exception as e:
            self.console.print(
                f'[red]ERROR[/red] Failed to setup SSH key: {e}'
            )
            return False

    def _upload_public_key(
        self,
        server_config: ServerConfig,
        password: str,
        public_key: paramiko.Ed25519Key
    ):
        '''Upload public key to remote server's authorized_keys'''
        try:
            # Connect with password
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server_config.host,
                port=server_config.port,
                username=server_config.user,
                password=password,
                timeout=30
            )

            # Ensure ~/.ssh directory exists
            client.exec_command('mkdir -p ~/.ssh && chmod 700 ~/.ssh')

            # Add public key to authorized_keys
            public_key_str = f'{public_key.get_name()} {public_key.get_base64()}'
            client.exec_command(
                f"echo '{public_key_str}' >> ~/.ssh/authorized_keys && "
                f'chmod 600 ~/.ssh/authorized_keys'
            )

            client.close()

        except Exception as e:
            raise RuntimeError(f'Failed to upload public key: {e}')

    def _update_ssh_config(
        self,
        server_config: ServerConfig,
        private_key_path: Path
    ) -> str:
        '''
        Update ~/.ssh/config for easy access with other SSH tools

        Args:
            server_config: Server configuration
            private_key_path: Path to private key

        Returns:
            SSH config alias
        '''
        ssh_config_path = self.STANDARD_SSH_DIR / 'config'

        # Create alias
        alias = f'cursor-{server_config.host}-{server_config.port}'

        # Build config entry
        config_entry = f'''

# Cursor Server Deployer - {server_config.name}
Host {alias}
    HostName {server_config.host}
    Port {server_config.port}
    User {server_config.user}
    IdentityFile {private_key_path}
    IdentitiesOnly yes
'''

        # Update config file
        if ssh_config_path.exists():
            with open(ssh_config_path, 'r+') as f:
                content = f.read()
                # Check if entry already exists
                if f'Host {alias}' not in content:
                    f.write(config_entry)
        else:
            ssh_config_path.touch(mode=0o600)
            with open(ssh_config_path, 'w') as f:
                f.write(config_entry)

        # Ensure correct permissions
        ssh_config_path.chmod(0o600)

        return alias

    def _test_key_login(self, server_config: ServerConfig) -> bool:
        '''Test SSH key login to server'''
        try:
            private_path, _ = self.get_key_path(server_config)

            if not private_path.exists():
                return False

            # Load private key
            private_key = paramiko.Ed25519Key.from_private_key_file(str(private_path))

            # Try to connect with key
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server_config.host,
                port=server_config.port,
                username=server_config.user,
                pkey=private_key,
                timeout=30
            )

            # Test with simple command
            stdin, stdout, stderr = client.exec_command("echo 'connection test'")
            output = stdout.read().decode().strip()
            client.close()

            return output == 'connection test'

        except Exception:
            return False

    def remove_key_auth(self, server_config: ServerConfig, password: str) -> bool:
        '''
        Remove SSH key authentication from a server

        Args:
            server_config: Server configuration
            password: Password for authentication

        Returns:
            True if successful, False otherwise
        '''
        try:
            self.console.print(
                f'\n[yellow]→[/yellow] Removing SSH key authentication from {server_config.name}'
            )

            # Get public key
            private_path, public_path = self.get_key_path(server_config)
            if not public_path.exists():
                self.console.print('[yellow]![/yellow] No key found to remove')
                return False

            with open(public_path, 'r') as f:
                public_key_str = f.read().strip()

            # Connect with password
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=server_config.host,
                port=server_config.port,
                username=server_config.user,
                password=password,
                timeout=30
            )

            # Remove key from authorized_keys
            client.exec_command(
                f"sed -i \"/{public_key_str.split()[1]}/d\" ~/.ssh/authorized_keys"
            )

            client.close()

            # Remove local key files
            private_path.unlink(missing_ok=True)
            public_path.unlink(missing_ok=True)

            self.console.print('[green]OK[/green] SSH key removed from server')

            return True

        except Exception as e:
            self.console.print(f'[red]ERROR[/red] Failed to remove SSH key: {e}')
            return False
