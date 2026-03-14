'''
Deployment manager for Cursor server
'''

import os
from pathlib import Path
from typing import List, Tuple, Optional

from rich.console import Console

from cursor_server_deployer.ssh.connection import SSHConnectionPool
from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.config.models import ServerConfig


class DeployManager:
    '''Manages deployment of Cursor server to remote servers'''

    def __init__(self, connection_pool: Optional[SSHConnectionPool] = None):
        self.console = Console()
        self.connection_pool = connection_pool or SSHConnectionPool()

    def deploy(
        self,
        server: ServerConfig,
        local_server_file: Path,
        local_cli_file: Optional[Path] = None,
        version_info: Optional[CursorVersion] = None,
        password: str = None
    ) -> bool:
        '''
        Deploy Cursor server to a single server

        Args:
            server: Server configuration
            local_server_file: Path to local server tar.gz file
            local_cli_file: Path to local CLI tar.gz file (optional)
            version_info: Cursor version information
            password: Password (if using password authentication)

        Returns:
            True if successful, False otherwise
        '''
        try:
            self.console.print(f'\n[cyan]Deploying to {server.name}...[/cyan]')

            # Check if we have server package to deploy
            if local_server_file:
                # Get connection
                if server.auth_method == 'key':
                    client = self.connection_pool.get_connection(server)
                else:
                    if not password:
                        raise RuntimeError('Password required for password authentication')
                    client = self._connect_with_password(server, password)

                # 1. Create remote directory structure
                remote_base_path = server.remote_path
                if version_info:
                    remote_server_path = f'{remote_base_path}/cli/servers/Stable-{version_info.commit}/server/'
                else:
                    remote_server_path = f'{remote_base_path}/cli/servers/default/'

                self.console.print('[yellow]→[/yellow] Creating remote directory structure...')
                client.exec_command(f"mkdir -p '{remote_server_path}'")

                # 2. Upload server file
                remote_tar_path = f'{remote_base_path}/cursor-server.tar.gz'
                self.console.print(f'[yellow]→[/yellow] Uploading server package to {remote_tar_path}...')

                sftp = client.open_sftp()
                sftp.put(str(local_server_file), remote_tar_path)
                sftp.close()

                # 3. Extract server file
                self.console.print('[yellow]→[/yellow] Extracting server files...')
                stdin, stdout, stderr = client.exec_command(
                    f"tar -xzf '{remote_tar_path}' -C '{remote_server_path}' --strip-components=1"
                )

            # Check for errors
            error = stderr.read().decode()
            if error:
                raise RuntimeError(f'Server extraction failed: {error}')

            # 4. Cleanup server temporary file
            self.console.print('[yellow]→[/yellow] Cleaning up server package...')
            client.exec_command(f"rm '{remote_tar_path}'")

            # 5. Upload CLI file if provided
            if local_cli_file:
                remote_cli_tar_path = f'{remote_base_path}/cursor-cli.tar.gz'
                self.console.print(f'[yellow]→[/yellow] Uploading CLI package to {remote_cli_tar_path}...')

                sftp = client.open_sftp()
                sftp.put(str(local_cli_file), remote_cli_tar_path)
                sftp.close()

                # 6. Extract CLI file
                self.console.print('[yellow]→[/yellow] Extracting CLI files...')
                stdin, stdout, stderr = client.exec_command(
                    f"tar -xzf '{remote_cli_tar_path}' -C '{remote_base_path}/cli/' --strip-components=1"
                )

                # Check for errors
                error = stderr.read().decode()
                if error:
                    raise RuntimeError(f'CLI extraction failed: {error}')

                # 7. Cleanup CLI temporary file
                self.console.print('[yellow]→[/yellow] Cleaning up CLI package...')
                client.exec_command(f"rm '{remote_cli_tar_path}'")

            # Report what was deployed
            self.console.print(f'[green]OK[/green] Successfully deployed to {server.name}')
            if local_server_file and local_cli_file:
                self.console.print(f'[dim]  Deployed: Server package + CLI package[/dim]')
            elif local_server_file:
                self.console.print(f'[dim]  Deployed: Server package only[/dim]')
            else:
                self.console.print(f'[dim]  Deployed: CLI package only[/dim]')

            return True

        except Exception as e:
            self.console.print(
                f'[red]ERROR[/red] Deployment failed for {server.name}: {e}'
            )
            return False

    def deploy_to_multiple_servers(
        self,
        servers: List[ServerConfig],
        local_file: Path,
        version_info: CursorVersion
    ) -> Tuple[List[ServerConfig], List[Tuple[ServerConfig, str]]]:
        '''
        Deploy to multiple servers

        Args:
            servers: List of server configurations
            local_file: Path to local tar.gz file
            version_info: Cursor version information

        Returns:
            Tuple of (successful_servers, failed_servers_with_errors)
        '''
        deployed_servers = []
        failed_servers = []

        for server in servers:
            try:
                # Get password for password authentication
                password = None
                if server.auth_method == 'password':
                    from cursor_server_deployer.ssh.connection import SSHConnectionPool
                    password = getpass.getpass(
                        f'[{server.name}] Enter password for {server.connection_string}: '
                    )

                if self.deploy(server, local_file, version_info, password):
                    deployed_servers.append(server)
                else:
                    failed_servers.append((server, 'Deployment failed'))

            except Exception as e:
                self.console.print(
                    f'[red]ERROR[/red] Failed to deploy to {server.name}: {e}'
                )
                failed_servers.append((server, str(e)))

        return deployed_servers, failed_servers

    def deploy_silent(
        self,
        servers: List[ServerConfig],
        local_server_file: Path,
        local_cli_file: Optional[Path] = None,
        version_info: Optional[CursorVersion] = None
    ) -> bool:
        '''
        Deploy in silent mode (minimal output).

        Args:
            servers: List of server configurations
            local_server_file: Path to local server tar.gz file
            local_cli_file: Path to local CLI tar.gz file (optional)
            version_info: Cursor version information

        Returns:
            True if all deployments successful, False otherwise
        '''
        all_success = True

        for server in servers:
            password = None

            if server.auth_method == 'password':
                # 即使在 silent 模式下，也允许通过一次性密码输入完成部署，
                # 只是打印更少的日志。
                import getpass

                password = getpass.getpass(
                    f'[silent] Enter password for {server.connection_string}: '
                )

            if not self.deploy(server, local_server_file, local_cli_file, version_info, password=password):
                all_success = False

        return all_success

    def _connect_with_password(
        self,
        server: ServerConfig,
        password: str
    ):
        '''Connect using password (helper method)'''
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server.host,
            port=server.port,
            username=server.user,
            password=password,
            timeout=30
        )
        return client

    def get_remote_cursor_version(self, server: ServerConfig) -> dict:
        '''
        Get Cursor version installed on remote server

        Args:
            server: Server configuration

        Returns:
            Dictionary with version info or None
        '''
        try:
            client = self.connection_pool.get_connection(server)

            # Check version file
            remote_path = f'{server.remote_path}/cli/servers/'
            stdin, stdout, stderr = client.exec_command(f"ls -d '{remote_path}'* 2>/dev/null")

            output = stdout.read().decode().strip()
            if not output:
                return None

            # Parse version from directory name (e.g., Stable-abc123)
            dirs = [d for d in output.split('\n') if d.strip()]
            if not dirs:
                return None

            latest_dir = dirs[-1]  # Assuming last one is latest
            commit = latest_dir.split('-')[-1] if '-' in latest_dir else ''

            return {
                'commit': commit,
                'path': latest_dir
            }

        except Exception:
            return None
