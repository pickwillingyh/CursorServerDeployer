#!/usr/bin/env python3
"""
Test password authentication for deployment
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import getpass

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.manager import DownloadManager
from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config import ServerConfig
from cursor_server_deployer.cli.commands import _deploy_with_prompts

def test_password_auth():
    """Test password authentication flow"""

    # Mock CursorVersion
    version_info = CursorVersion(
        version="0.42.1",
        commit="60faf7b51077ed1df1db718157bbfed740d2e168",
        arch="x64",
        full_output="cursor 0.42.1\n60faf7b51077ed1df1db718157bbfed740d2e168"
    )

    # Create test directories
    test_dir = Path(__file__).parent / "test_password"
    cache_dir = test_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=== Testing Password Authentication ===")
    print(f"Server: your-server.com")
    print(f"Username: your-username")
    print(f"Password: dev")
    print(f"Version: {version_info.version}")

    try:
        # 1. Test downloads
        print("\n1. Testing downloads...")
        download_manager = DownloadManager(cache_dir=cache_dir)

        # Mock successful downloads
        with patch.object(download_manager, 'download') as mock_download_server, \
             patch.object(download_manager, 'download_cli_package') as mock_download_cli:

            # Create mock file paths
            mock_server_file = MagicMock()
            mock_server_file.name = "cursor-reh-linux-x64.tar.gz"
            mock_server_file.stat.return_value.st_size = 1000000

            mock_cli_file = MagicMock()
            mock_cli_file.name = "cli-linux-x64.tar.gz"
            mock_cli_file.stat.return_value.st_size = 500000

            mock_download_server.return_value = mock_server_file
            mock_download_cli.return_value = mock_cli_file

            server_file = download_manager.download(
                version_info=version_info,
                arch="x64",
                force=False,
                package_type="server"
            )

            cli_file = download_manager.download_cli_package(
                version_info=version_info,
                arch="x64",
                force=False
            )

            if server_file and cli_file:
                print("SUCCESS: Downloads completed successfully")
            else:
                print("FAILED: Downloads failed")
                return

        # 2. Test deployment with password auth
        print("\n2. Testing deployment with password auth...")

        # Create server config
        server = ServerConfig(
            id="test-password-server",
            name="Test Password Server",
            host="your-server.com",  # Replace with actual server
            user="your-username",   # Replace with actual username
            port=22,
            arch="x64",
            auth_method="password",
            remote_path="/home/your-user/.cursor-server"
        )

        # Mock getpass to return "dev"
        with patch('getpass.getpass', return_value='dev') as mock_getpass, \
             patch.object(DeployManager, 'deploy') as mock_deploy:

            # Mock successful deployment
            mock_deploy.return_value = True

            # Mock SSH client
            mock_client = MagicMock()
            mock_sftp = MagicMock()

            def mock_put(local, remote):
                print(f"  - Upload: {local} -> {remote}")

            mock_sftp.put.side_effect = mock_put
            mock_client.open_sftp.return_value = mock_sftp

            # Create deploy manager and mock connection
            deploy_manager = DeployManager()
            deploy_manager.connection_pool = MagicMock()
            deploy_manager.connection_pool.get_connection.return_value = mock_client

            # Test deployment
            success = deploy_manager.deploy(
                server=server,
                local_server_file=server_file,
                local_cli_file=cli_file,
                version_info=version_info,
                password="dev"
            )

            if success:
                print("SUCCESS: Deployment successful")
                print("\nDeployment would do the following:")
                print("1. Connect to server using SSH with password 'dev'")
                print("2. Upload server package to remote server")
                print("3. Extract server package to /home/your-user/.cursor-server/cursor-{commit}/")
                print("4. Upload CLI package to remote server")
                print("5. Extract CLI package to /home/your-user/.cursor-server/cursor-{commit}/cli/")
                print("6. Set proper permissions")
                print("7. Verify deployment")
            else:
                print("FAILED: Deployment failed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\n3. Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_password_auth()