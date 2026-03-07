"""
CLI commands for cursor-server-deployer
"""

import sys
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from cursor_server_deployer.config import ConfigManager, ServerConfig, ExecutionRecord
from cursor_server_deployer.version import VersionDetector
from cursor_server_deployer.download import DownloadManager
from cursor_server_deployer.ssh import KeyManager, SSHConnectionPool
from cursor_server_deployer.deploy import DeployManager
from cursor_server_deployer.utils import Logger

app = typer.Typer(
    name="cursor-server-deployer",
    help="Cursor Remote Server Deployment Tool",
    add_completion=False
)


# Global options
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
check_update_option = typer.Option(False, "--check-update", help="Check for updates")


@app.callback()
def main(verbose: bool = verbose_option, check_update: bool = check_update_option):
    """Cursor Server Deployer - Deploy Cursor remote servers to Linux machines"""
    global logger
    logger = Logger(verbose=verbose)

    # Check for updates if requested
    if check_update:
        _check_for_updates()


@app.command()
def check_update():
    """Check for available updates"""
    _check_for_updates()
def main(verbose: bool = verbose_option):
    """Cursor Server Deployer - Deploy Cursor remote servers to Linux machines"""
    global logger
    logger = Logger(verbose=verbose)


# Main deploy command
@app.command()
def deploy(
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Remote host"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Remote username"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    arch: str = typer.Option("x64", "--arch", "-a", help="Target architecture (x64 or arm64)"),
    server_id: Optional[str] = typer.Option(None, "--server-id", "-s", help="Server ID from config"),
    servers: Optional[str] = typer.Option(None, "--servers", help="Comma-separated server IDs"),
    silent: bool = typer.Option(False, "--silent", help="Silent mode (no prompts, uses last config)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive server selection"),
    force_download: bool = typer.Option(False, "--force-download", "-f", help="Force re-download"),
):
    """
    Deploy Cursor server to remote server(s)
    """
    config = ConfigManager()

    # Handle silent mode
    if silent:
        last_execution = config.get_last_execution()
        if not last_execution:
            logger.error("No previous execution found for silent mode")
            raise typer.Exit(1)

        # Use servers from last execution
        servers_to_deploy = []
        for sid in last_execution.servers:
            server = config.get_server(sid)
            if server:
                servers_to_deploy.append(server)

        if not servers_to_deploy:
            logger.error("No valid servers found from last execution")
            raise typer.Exit(1)

        logger.info(f"Silent mode: Using {len(servers_to_deploy)} server(s) from last execution")

    # Handle server selection
    elif interactive:
        servers_to_deploy = _select_servers_interactive(config)
        if not servers_to_deploy:
            logger.warning("No servers selected")
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
                    logger.error(f"Server not found: {sid}")
                    raise typer.Exit(1)
        elif server_id:
            # Single server by ID
            server = config.get_server(server_id)
            if not server:
                logger.error(f"Server not found: {server_id}")
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
        logger.section("Detecting Cursor version")
        detector = VersionDetector()
        version_info = detector.get_version_info()
        logger.success(f"Cursor {version_info.version} (commit: {version_info.commit[:8]})")
    except Exception as e:
        logger.error(f"Failed to detect Cursor version: {e}")
        raise typer.Exit(1)

    # Download Cursor server
    try:
        logger.section("Downloading Cursor server")
        downloader = DownloadManager()

        # Check cache for each architecture
        download_needed = True
        local_file = None

        if not force_download:
            for server in servers_to_deploy:
                cached = downloader.get_cached_file(version_info, server.arch)
                if cached:
                    local_file = cached
                    logger.info(f"Using cached file for {server.arch}")
                    break

        if download_needed or not local_file:
            # Use first server's architecture (or x64 as default)
            target_arch = servers_to_deploy[0].arch
            local_file = downloader.download(version_info, target_arch, force=force_download)

    except Exception as e:
        logger.error(f"Failed to download Cursor server: {e}")
        raise typer.Exit(1)

    # Deploy to servers
    logger.section("Deploying to remote server(s)")

    if silent:
        # Silent mode - only key auth allowed
        deploy_manager = DeployManager()
        success = deploy_manager.deploy_silent(servers_to_deploy, local_file, version_info)

        if success:
            logger.success(f"Deployed to {len(servers_to_deploy)} server(s)")
            _record_execution(config, servers_to_deploy, version_info, True)
        else:
            logger.error("Some deployments failed")
            _record_execution(config, servers_to_deploy, version_info, False)
            raise typer.Exit(1)

    else:
        # Normal mode - may require passwords
        deployed, failed = _deploy_with_prompts(servers_to_deploy, local_file, version_info, config)

        # Summary
        logger.section("Deployment Summary")
        logger.success(f"Successfully deployed to {len(deployed)} server(s)")

        if deployed:
            for server in deployed:
                config.set_server_deployed(server.id, version_info.version, version_info.commit)
                logger.info(f"  - {server.name}")

        if failed:
            logger.error(f"Failed to deploy to {len(failed)} server(s)")
            for server, error in failed:
                logger.info(f"  - {server.name}: {error}")

        _record_execution(config, deployed, version_info, len(failed) == 0)


@app.command()
def add_server(
    host: str = typer.Option(..., "--host", "-h", help="Remote host"),
    user: str = typer.Option(..., "--user", "-u", help="Remote username"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    arch: str = typer.Option("x64", "--arch", "-a", help="Target architecture"),
    name: Optional[str] = typer.Option(None, "--name", help="Server display name"),
    remote_path: str = typer.Option("~/.cursor-server", "--remote-path", help="Remote installation path"),
):
    """Add a new server configuration"""
    config = ConfigManager()

    server = config.add_server(
        host=host,
        user=user,
        port=port,
        arch=arch,
        name=name,
        remote_path=remote_path
    )

    logger.success(f"Added server: {server.name}")
    logger.info(f"  ID: {server.id}")
    logger.info(f"  Connection: {server.connection_string}")
    logger.info(f"  Architecture: {server.arch}")


@app.command()
def list_servers():
    """List all configured servers"""
    config = ConfigManager()
    servers = config.list_servers()

    if not servers:
        logger.info("No servers configured")
        return

    table = Table(title="Configured Servers")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Connection")
    table.add_column("Arch")
    table.add_column("Auth")
    table.add_column("Key Setup")

    for server in servers:
        key_status = "[green]✓[/green]" if server.key_setup else "[red]✗[/red]"
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
    server_id: str = typer.Option(..., "--server-id", "-s", help="Server ID to remove")
):
    """Remove a server configuration"""
    config = ConfigManager()
    server = config.get_server(server_id)

    if not server:
        logger.error(f"Server not found: {server_id}")
        raise typer.Exit(1)

    if config.remove_server(server_id):
        logger.success(f"Removed server: {server.name}")
    else:
        logger.error("Failed to remove server")
        raise typer.Exit(1)


@app.command()
def setup_key(
    server_id: str = typer.Option(..., "--server-id", "-s", help="Server ID")
):
    """Setup SSH key authentication for a server"""
    config = ConfigManager()
    server = config.get_server(server_id)

    if not server:
        logger.error(f"Server not found: {server_id}")
        raise typer.Exit(1)

    if server.auth_method == "key":
        logger.info(f"SSH key already configured for {server.name}")
        return

    logger.section(f"Setting up SSH key for {server.name}")

    # Get password
    import getpass
    password = getpass.getpass(
        f"Enter current password for {server.connection_string}: "
    )

    # Setup key
    key_manager = KeyManager()
    if key_manager.setup_key_auth(server, password):
        config.update_server(
            server_id,
            auth_method="key",
            key_path=server.key_path,
            ssh_config_alias=server.ssh_config_alias,
            key_setup=True
        )
        logger.success(f"SSH key authentication enabled for {server.name}")

        if server.ssh_config_alias:
            logger.info(f"You can now connect using: ssh {server.ssh_config_alias}")
    else:
        logger.error("Failed to setup SSH key authentication")
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent executions to show")
):
    """Show deployment history"""
    config = ConfigManager()
    executions = config.get_recent_executions(limit)

    if not executions:
        logger.info("No deployment history found")
        return

    logger.section("Recent Deployments")

    for i, exec_record in enumerate(executions, 1):
        status = "[green]✓[/green]" if exec_record.success else "[red]✗[/red]"
        logger.info(f"{status} {exec_record.timestamp}")
        logger.info(f"    Action: {exec_record.action}")
        logger.info(f"    Servers: {', '.join(exec_record.servers)}")
        if exec_record.cursor_version:
            logger.info(f"    Version: {exec_record.cursor_version}")
        logger.blank()


@app.command()
def cache(
    clear: bool = typer.Option(False, "--clear", help="Clear cache"),
    older_than: Optional[int] = typer.Option(None, "--older-than", help="Clear files older than N days"),
):
    """Manage download cache"""
    downloader = DownloadManager()

    if clear:
        downloader.clear_cache(older_than)
    else:
        cache_dir = downloader.cache_dir
        files = list(cache_dir.glob("*.tar.gz"))

        if not files:
            logger.info("Cache is empty")
        else:
            logger.info(f"Cache directory: {cache_dir}")
            logger.info(f"Files: {len(files)}")
            for f in files:
                size_mb = f.stat().st_size / (1024 * 1024)
                logger.info(f"  - {f.name} ({size_mb:.1f} MB)")


# Helper functions
def _select_servers_interactive(config: ConfigManager) -> List[ServerConfig]:
    """Select servers interactively"""
    servers = config.list_servers()

    if not servers:
        logger.error("No servers configured. Add a server first.")
        raise typer.Exit(1)

    logger.section("Select server(s) to deploy to")

    for i, server in enumerate(servers, 1):
        key_status = "[dim](key)[/dim]" if server.key_setup else "[dim](password)[/dim]"
        logger.info(f"  {i}. {server.name} - {server.connection_string} {key_status}")

    logger.info(f"  {len(servers) + 1}. All servers")
    logger.info(f"  0. Cancel")

    choice = typer.prompt("Select", type=int)

    if choice == 0:
        return []
    elif choice == len(servers) + 1:
        return servers
    elif 1 <= choice <= len(servers):
        return [servers[choice - 1]]
    else:
        logger.error("Invalid selection")
        raise typer.Exit(1)


def _deploy_with_prompts(
    servers: List[ServerConfig],
    local_file,
    version_info,
    config: ConfigManager
):
    """Deploy with password prompts"""
    deploy_manager = DeployManager()
    deployed = []
    failed = []

    for server in servers:
        try:
            # Get password if needed
            password = None
            if server.auth_method == "password":
                import getpass
                password = getpass.getpass(
                    f"Enter password for {server.connection_string}: "
                )

            if deploy_manager.deploy(server, local_file, version_info, password):
                deployed.append(server)
            else:
                failed.append((server, "Deployment failed"))

        except Exception as e:
            failed.append((server, str(e)))

    return deployed, failed


def _record_execution(
    config: ConfigManager,
    servers: List[ServerConfig],
    version_info,
    success: bool
):
    """Record execution to history"""
    record = ExecutionRecord(
        action="deploy",
        servers=[s.id for s in servers],
        cursor_version=version_info.version,
        cursor_commit=version_info.commit,
        success=success
    )
    config.add_execution_record(record)


# Global logger instance
logger = Logger()


def _check_for_updates():
    """Check for available updates"""
    try:
        import requests
        import json
        from packaging import version

        # Get current version
        current_version = __version__

        # Check PyPI for latest version
        pypi_url = "https://pypi.org/pypi/cursor-server-deployer/json"
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        latest_version = data["info"]["version"]

        if version.parse(latest_version) > version.parse(current_version):
            logger.info(f"[yellow]New version available![/yellow]")
            logger.info(f"  Current: {current_version}")
            logger.info(f"  Latest: {latest_version}")
            logger.info("  Run: uvx cursor-server-deployer --help")
            logger.info("  to see how to update")
        else:
            logger.info(f"[green]You are using the latest version: {current_version}[/green]")

    except Exception as e:
        logger.debug(f"Update check failed: {e}")
        logger.info("Could not check for updates")


def main_entry():
    """Entry point for the CLI"""
    app()


if __name__ == "__main__":
    main_entry()
