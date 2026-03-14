'''
CLI commands for cursor-server-deployer
'''

import sys
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

from cursor_server_deployer import __version__
from cursor_server_deployer.config import ConfigManager, ServerConfig, ExecutionRecord
from cursor_server_deployer.version import VersionDetector
from cursor_server_deployer.download import DownloadManager
from cursor_server_deployer.ssh import KeyManager, SSHConnectionPool
from cursor_server_deployer.deploy import DeployManager
from cursor_server_deployer.utils import Logger
from cursor_server_deployer.utils.interactive_menu import InteractiveMenu

app = typer.Typer(
    name='cursor-server-deployer',
    help='Cursor Remote Server Deployment Tool',
    add_completion=False
)


# Global options
verbose_option = typer.Option(False, '--verbose', '-v', help='Enable verbose output')
check_update_option = typer.Option(False, '--check-update', help='Check for updates')


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = verbose_option,
    check_update: bool = check_update_option,
):
    '''Cursor Server Deployer - Deploy Cursor remote servers to Linux machines'''
    global logger
    logger = Logger(verbose=verbose)

    # Check for updates if requested
    if check_update:
        _check_for_updates()

    # If no subcommand was invoked, launch the interactive menu
    if ctx.invoked_subcommand is None:
        _interactive_menu()
        raise typer.Exit(0)


@app.command()
def check_update():
    '''Check for available updates'''
    _check_for_updates()


# Main deploy command
@app.command()
def deploy(
    host: Optional[str] = typer.Option(None, '--host', '-h', help='Remote host'),
    user: Optional[str] = typer.Option(None, '--user', '-u', help='Remote username'),
    port: int = typer.Option(22, '--port', '-p', help='SSH port'),
    arch: str = typer.Option('x64', '--arch', '-a', help='Target architecture (x64 or arm64)'),
    server_id: Optional[str] = typer.Option(None, '--server-id', '-s', help='Server ID from config'),
    servers: Optional[str] = typer.Option(None, '--servers', help='Comma-separated server IDs'),
    silent: bool = typer.Option(False, '--silent', help='Silent mode (no prompts, uses last config)'),
    interactive: bool = typer.Option(False, '--interactive', '-i', help='Interactive server selection'),
    force_download: bool = typer.Option(False, '--force-download', '-f', help='Force re-download'),
  ):
    '''
    Deploy Cursor server and CLI package to remote server(s)
    '''
    config = ConfigManager()

    # Handle silent mode
    if silent:
        last_execution = config.get_last_execution()
        if not last_execution:
            # No previous execution: fall back to interactive selection
            logger.warning('No previous execution found for silent mode, showing server list for selection.')
            servers_to_deploy = _select_servers_interactive(config)
            if not servers_to_deploy:
                logger.warning('No servers selected')
                raise typer.Exit(0)
        else:
            # Use servers from last execution
            servers_to_deploy = []
            for sid in last_execution.servers:
                server = config.get_server(sid)
                if server:
                    servers_to_deploy.append(server)

            if not servers_to_deploy:
                logger.error('No valid servers found from last execution')
                raise typer.Exit(1)

            logger.info(f'Silent mode: Using {len(servers_to_deploy)} server(s) from last execution')

    # Handle server selection
    elif interactive:
        servers_to_deploy = _select_servers_interactive(config)
        if not servers_to_deploy:
            logger.warning('No servers selected')
            raise typer.Exit(0)
    else:
        # Handle command line server specification
        if servers:
            # Multiple servers
            server_ids = [s.strip() for s in servers.split(',')]
            servers_to_deploy = []
            for sid in server_ids:
                server = config.get_server(sid)
                if server:
                    servers_to_deploy.append(server)
                else:
                    logger.error(f'Server not found: {sid}')
                    raise typer.Exit(1)
        elif server_id:
            # Single server by ID
            server = config.get_server(server_id)
            if not server:
                logger.error(f'Server not found: {server_id}')
                raise typer.Exit(1)
            servers_to_deploy = [server]
        elif host and user:
            # Create ad-hoc server from parameters
            server = config.get_server_by_connection(host, port, user)
            if not server:
                server = config.add_server(host=host, user=user, port=port, arch=arch)
            servers_to_deploy = [server]
        else:
            # No server specified - show menu
            servers_to_deploy = _select_servers_interactive(config)
            if not servers_to_deploy:
                raise typer.Exit(0)

    # Get Cursor version
    try:
        logger.section('Detecting Cursor version')
        detector = VersionDetector()
        version_info = detector.get_version_info()
        logger.success(f'Cursor {version_info.version} (commit: {version_info.commit[:8]})')
    except Exception as e:
        logger.error(f'Failed to detect Cursor version: {e}')
        raise typer.Exit(1)

    # Download Cursor server and CLI package
    logger.section('Downloading packages')
    downloader = DownloadManager()

    # Check cache for each architecture
    download_server_needed = True
    download_cli_needed = True
    local_server_file = None
    local_cli_file = None

    if not force_download:
      logger.debug('Checking cache for each server architecture:')
      for server in servers_to_deploy:
        arch = server.arch
        # Check server package
        cached = downloader.get_cached_file(version_info, arch, package_type='server')
        if cached:
          local_server_file = cached
          logger.info(f'Using cached server package for {arch}: {cached.name}')
          logger.debug(f'Cache found at: {cached}')
          logger.debug(f'Cache directory: {cached.parent}')
          logger.debug(f'Cache file exists: {cached.exists()}')
          download_server_needed = False

        # Check CLI package
        cli_cached = downloader.get_cached_file(version_info, arch, package_type='cli')
        if cli_cached:
          local_cli_file = cli_cached
          logger.info(f'Using cached CLI package for {arch}: {cli_cached.name}')
          download_cli_needed = False

        if not download_server_needed and not download_cli_needed:
          break

      if not local_server_file:
        logger.debug('No cached server package found for any architecture, will download')
        logger.debug(f'Cache directory: {downloader.cache_dir}')
        logger.debug(f'Cache directory exists: {downloader.cache_dir.exists()}')

    # Download server package if needed
    if download_server_needed or force_download:
      target_arch = servers_to_deploy[0].arch
      local_server_file = downloader.download(version_info, target_arch, force=force_download, package_type='server')
      if local_server_file:
        logger.success('Server package downloaded')
      else:
        logger.error('Server package download failed')
        logger.warning('Will proceed without server package')

    # Download CLI package if needed
    if download_cli_needed or force_download:
      target_arch = servers_to_deploy[0].arch
      local_cli_file = downloader.download_cli_package(version_info, target_arch, force=force_download)
      if local_cli_file:
        logger.success('CLI package downloaded')
      else:
        logger.warning('CLI package download failed')

    # Check if we have at least one package to deploy
    if not local_server_file and not local_cli_file:
      logger.error('No packages were successfully downloaded')
      raise typer.Exit(1)

    # Deploy to servers
    logger.section('Deploying to remote server(s)')

    if silent:
        # Silent mode - only key auth allowed
        deploy_manager = DeployManager()
        success = deploy_manager.deploy_silent(servers_to_deploy, local_server_file, local_cli_file, version_info)

        if success:
            logger.success(f'Deployed to {len(servers_to_deploy)} server(s)')
            _record_execution(config, servers_to_deploy, version_info, True)
        else:
            logger.error('Some deployments failed')
            _record_execution(config, servers_to_deploy, version_info, False)
            raise typer.Exit(1)

    else:
        # Normal mode - may require passwords
        deployed, failed = _deploy_with_prompts(servers_to_deploy, local_server_file, local_cli_file, version_info, config)

        # Summary
        logger.section('Deployment Summary')
        logger.success(f'Successfully deployed to {len(deployed)} server(s)')

        if deployed:
            for server in deployed:
                config.set_server_deployed(server.id, version_info.version, version_info.commit)
                logger.info(f'  - {server.name}')

        if failed:
            logger.error(f'Failed to deploy to {len(failed)} server(s)')
            for server, error in failed:
                logger.info(f'  - {server.name}: {error}')

        _record_execution(config, deployed, version_info, len(failed) == 0)


@app.command()
def add_server(
    host: str = typer.Option(..., '--host', '-h', help='Remote host'),
    user: str = typer.Option(..., '--user', '-u', help='Remote username'),
    port: int = typer.Option(22, '--port', '-p', help='SSH port'),
    arch: str = typer.Option('x64', '--arch', '-a', help='Target architecture'),
    name: Optional[str] = typer.Option(None, '--name', help='Server display name'),
    remote_path: str = typer.Option('~/.cursor-server', '--remote-path', help='Remote installation path'),
):
    '''Add a new server configuration'''
    config = ConfigManager()

    server = config.add_server(
        host=host,
        user=user,
        port=port,
        arch=arch,
        name=name,
        remote_path=remote_path
    )

    logger.success(f'Added server: {server.name}')
    logger.info(f'  ID: {server.id}')
    logger.info(f'  Connection: {server.connection_string}')
    logger.info(f'  Architecture: {server.arch}')


@app.command()
def list_servers():
    '''List all configured servers'''
    config = ConfigManager()
    servers = config.list_servers()

    if not servers:
        logger.info('No servers configured')
        return

    table = Table(title='Configured Servers')
    table.add_column('ID', style='dim')
    table.add_column('Name')
    table.add_column('Connection')
    table.add_column('Arch')
    table.add_column('Auth')
    table.add_column('Key Setup')

    for server in servers:
        key_status = '[green]YES[/green]' if server.key_setup else '[red]NO[/red]'
        table.add_row(
            server.id,
            server.name,
            server.connection_string,
            server.arch,
            server.auth_method,
            key_status
        )

    logger.console.print(table)


@app.command()
def remove_server(
    server_id: str = typer.Option(..., '--server-id', '-s', help='Server ID to remove')
):
    '''Remove a server configuration'''
    config = ConfigManager()
    server = config.get_server(server_id)

    if not server:
        logger.error(f'Server not found: {server_id}')
        raise typer.Exit(1)

    if config.remove_server(server_id):
        logger.success(f'Removed server: {server.name}')
    else:
        logger.error('Failed to remove server')
        raise typer.Exit(1)


@app.command()
def setup_key(
    server_id: str = typer.Option(..., '--server-id', '-s', help='Server ID')
):
    '''Setup SSH key authentication for a server'''
    config = ConfigManager()
    server = config.get_server(server_id)

    if not server:
        logger.error(f'Server not found: {server_id}')
        raise typer.Exit(1)

    if server.auth_method == 'key':
        logger.info(f'SSH key already configured for {server.name}')
        return

    logger.section(f'Setting up SSH key for {server.name}')

    # Get password
    import getpass
    password = getpass.getpass(
        f'Enter current password for {server.connection_string}: '
    )

    # Setup key
    key_manager = KeyManager()
    if key_manager.setup_key_auth(server, password):
        config.update_server(
            server_id,
            auth_method='key',
            key_path=server.key_path,
            ssh_config_alias=server.ssh_config_alias,
            key_setup=True
        )
        logger.success(f'SSH key authentication enabled for {server.name}')

        if server.ssh_config_alias:
            logger.info(f'You can now connect using: ssh {server.ssh_config_alias}')
    else:
        logger.error('Failed to setup SSH key authentication')
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, '--limit', '-l', help='Number of recent executions to show')
):
    '''Show deployment history'''
    config = ConfigManager()
    executions = config.get_recent_executions(limit)

    if not executions:
        logger.info('No deployment history found')
        return

    logger.section('Recent Deployments')

    for i, exec_record in enumerate(executions, 1):
        status = '[green]OK[/green]' if exec_record.success else '[red]ERROR[/red]'
        logger.info(f'{status} {exec_record.timestamp}')
        logger.info(f'    Action: {exec_record.action}')
        logger.info(f'    Servers: {", ".join(exec_record.servers)}')
        if exec_record.cursor_version:
            logger.info(f'    Version: {exec_record.cursor_version}')
        logger.blank()


@app.command()
def cache(
    clear: bool = typer.Option(False, '--clear', help='Clear cache'),
    older_than: Optional[int] = typer.Option(None, '--older-than', help='Clear files older than N days'),
):
    '''Manage download cache'''
    downloader = DownloadManager()

    if clear:
        downloader.clear_cache(older_than)
    else:
        cache_dir = downloader.cache_dir
        files = list(cache_dir.glob('*.tar.gz'))

        if not files:
            logger.info('Cache is empty')
        else:
            logger.info(f'Cache directory: {cache_dir}')
            logger.info(f'Files: {len(files)}')
            for f in files:
                size_mb = f.stat().st_size / (1024 * 1024)
                logger.info(f'  - {f.name} ({size_mb:.1f} MB)')


# Helper functions
def _interactive_menu():
    '''Top-level interactive menu shown when no command is given.'''
    interactive_menu = InteractiveMenu()

    while True:
        config = ConfigManager()

        choices = [
            {'name': 'Deploy to remote servers', 'value': 'deploy'},
            {'name': 'Add new server', 'value': 'add'},
            {'name': 'Manage server list', 'value': 'manage'},
            {'name': 'Setup SSH key authentication', 'value': 'ssh'},
            {'name': 'View deployment history', 'value': 'history'},
            {'name': 'Manage download cache', 'value': 'cache'},
            {'name': 'Exit', 'value': 'exit'},
        ]

        choice = interactive_menu.select_single(
            'Cursor Server Deployer - Interactive Menu',
            choices,
            'Use ↑/↓ to move, Enter to confirm, Esc to cancel'
        )

        if choice is None or choice == 'exit':
            return
        elif choice == 'deploy':
            # Use the existing interactive server selection + deploy flow
            # Reset force_download to False for interactive mode
            deploy(interactive=True, force_download=False, silent=False, host=None, user=None, port=22, arch='x64', server_id=None, servers=None)
        elif choice == 'add':
            # Prompt for basic server information, then call add_server()
            host = typer.prompt('Remote host (e.g. example.com)')
            user = typer.prompt('Remote username (e.g. root)')
            port = typer.prompt('SSH port', type=int, default=22)
            arch = typer.prompt('Architecture (x64/arm64)', default='x64')
            name = typer.prompt('Server display name', default='')
            remote_path = typer.prompt('Remote installation path', default='~/.cursor-server')

            add_server(
                host=host,
                user=user,
                port=port,
                arch=arch,
                name=name or None,
                remote_path=remote_path,
            )
        elif choice == 'manage':
            # Simple manage menu: list servers, optionally remove one
            list_servers()
            if typer.confirm('Remove a server?', default=False):
                server_id = typer.prompt('Server ID to remove')
                remove_server(server_id=server_id)
        elif choice == 'ssh':
            # List servers then allow selecting one for key setup
            list_servers()
            server_id = typer.prompt('Server ID to setup SSH key for')
            setup_key(server_id=server_id)
        elif choice == 'history':
            limit = typer.prompt('How many recent executions to show?', type=int, default=10)
            history(limit=limit)
        elif choice == 'cache':
            if typer.confirm('Clear download cache?', default=False):
                older = typer.prompt(
                    'Only clear files older than N days (0 = all)',
                    type=int,
                    default=0,
                )
                cache(clear=True, older_than=(older or None))
            else:
                cache()


def _select_servers_interactive(config: ConfigManager) -> List[ServerConfig]:
    '''Select servers interactively (支持单选、多选、新建/全部/上次选择/退出等菜单项)'''
    interactive_menu = InteractiveMenu()

    while True:
        servers = config.list_servers()

        if not servers:
            logger.info("No servers configured yet. Let's add a new server first.")
            # Reuse the add_server prompts from the interactive menu
            # Reuse the add_server prompts from the interactive menu
            host = typer.prompt('Remote host (e.g. example.com)')
            user = typer.prompt('Remote username (e.g. root)')
            port = typer.prompt('SSH port', type=int, default=22)
            arch = typer.prompt('Architecture (x64/arm64)', default='x64')
            name = typer.prompt('Server display name', default='')
            remote_path = typer.prompt('Remote installation path', default='~/.cursor-server')
            add_server(
                host=host,
                user=user,
                port=port,
                arch=arch,
                name=name or None,
                remote_path=remote_path,
            )
            # Loop back and reload servers
            continue

        # Primary menu: 单选当前项 + 特殊操作
        primary_choices = []
        for server in servers:
            key_status = "(key)" if server.key_setup else "(password)"
            label = f"{server.name} - {server.connection_string} {key_status}"
            primary_choices.append({"name": label, "value": ("single", server)})

        # Extra menu items
        extra_choices = [
            {"name": "[+] New server...", "value": ("action", "new")},
            {"name": "[*] All servers", "value": ("action", "all")},
        ]

        # 如果有上一次执行记录，则增加"直接应用上一次选择"的选项
        last_execution = config.get_last_execution()
        if last_execution and last_execution.servers:
            extra_choices.insert(
                1,
                {
                    "name": "[⟳] Use last selected servers",
                    "value": ("action", "last"),
                },
            )

        # 进入多选模式的入口，具体空格说明放在下一步的多选界面里
        extra_choices.extend(
            [
                {"name": "Multi-select servers...", "value": ("action", "multi")},
                {"name": "[x] Quit", "value": ("action", "quit")},
            ]
        )

        primary_choices.extend(extra_choices)

        result = interactive_menu.select_single(
            "Select server(s) to deploy:",
            primary_choices,
            "Use ↑/↓ to move, Enter to confirm, Esc to cancel"
        )

        if result is None:
            # User cancelled
            return []

        mode, payload = result

        # Handle primary selection result
        if mode == 'single':
            # 直接回车，选择当前 server（单选）
            server = payload
            return [server]

        action = payload
        if action == 'quit':
            return []
        elif action == 'all':
            return list(servers)
        elif action == 'last':
            # 直接复用上一次部署时使用的服务器列表，但仍然走常规（非 silent）部署流程
            last_execution = config.get_last_execution()
            if not last_execution or not last_execution.servers:
                logger.warning('No previous execution found, please select servers manually.')
                continue

            selected_servers: List[ServerConfig] = []
            for sid in last_execution.servers:
                server = config.get_server(sid)
                if server:
                    selected_servers.append(server)

            if not selected_servers:
                logger.warning('No valid servers found from last execution, please select servers manually.')
                continue

            return selected_servers
        elif action == 'new':
            # 新建 server 后回到菜单
            host = typer.prompt('Remote host (e.g. example.com)')
            user = typer.prompt('Remote username (e.g. root)')
            port = typer.prompt('SSH port', type=int, default=22)
            arch = typer.prompt('Architecture (x64/arm64)', default='x64')
            name = typer.prompt('Server display name', default='')
            remote_path = typer.prompt('Remote installation path', default='~/.cursor-server')

            add_server(
                host=host,
                user=user,
                port=port,
                arch=arch,
                name=name or None,
                remote_path=remote_path,
            )
            continue
        elif action == 'multi':
            # 进入多选界面，支持空格选择
            checkbox_choices = []
            for server in servers:
                key_status = '(key)' if server.key_setup else '(password)'
                label = f'{server.name} - {server.connection_string} {key_status}'
                checkbox_choices.append({'name': label, 'value': server})

            selected = interactive_menu.select_multiple(
                'Select server(s) to deploy (multi-select):',
                checkbox_choices,
                'Use ↑/↓ to move, Space to select, Enter to confirm, Esc to cancel'
            )

            return selected


def _deploy_with_prompts(
    servers: List[ServerConfig],
    local_server_file,
    local_cli_file,
    version_info,
    config: ConfigManager
):
    '''Deploy with password prompts'''
    deploy_manager = DeployManager()
    deployed = []
    failed = []

    for server in servers:
        try:
            # Get password if needed
            password = None
            if server.auth_method == 'password':
                import getpass
                password = getpass.getpass(
                    f'Enter password for {server.connection_string}: '
                )

            if deploy_manager.deploy(server, local_server_file, local_cli_file, version_info, password):
                deployed.append(server)
            else:
                failed.append((server, 'Deployment failed'))

        except Exception as e:
            failed.append((server, str(e)))

    return deployed, failed


def _record_execution(
    config: ConfigManager,
    servers: List[ServerConfig],
    version_info,
    success: bool
):
    '''Record execution to history'''
    record = ExecutionRecord(
        action='deploy',
        servers=[s.id for s in servers],
        cursor_version=version_info.version,
        cursor_commit=version_info.commit,
        success=success
    )
    config.add_execution_record(record)


# Global logger instance
logger = Logger()


def _check_for_updates():
    '''Check for available updates'''
    try:
        import requests
        import json
        from packaging import version

        # Get current version
        current_version = __version__

        # Check PyPI for latest version
        pypi_url = 'https://pypi.org/pypi/cursor-server-deployer/json'
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        latest_version = data['info']['version']

        if version.parse(latest_version) > version.parse(current_version):
            logger.info(f'[yellow]New version available![/yellow]')
            logger.info(f'  Current: {current_version}')
            logger.info(f'  Latest: {latest_version}')
            logger.info('  Run: uvx cursor-server-deployer --help')
            logger.info('  to see how to update')
        else:
            logger.info(f'[green]You are using the latest version: {current_version}[/green]')

    except Exception as e:
        logger.debug(f'Update check failed: {e}')
        logger.info('Could not check for updates')


def main_entry():
    '''Entry point for the CLI'''
    app()


if __name__ == '__main__':
    main_entry()
