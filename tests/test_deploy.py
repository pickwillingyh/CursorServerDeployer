#!/usr/bin/env python3
"""
Test deployment functionality with a mock server
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.manager import DownloadManager
from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config import ServerConfig
from cursor_server_deployer.utils.logger import Logger

def test_deploy():
    """Test the deployment functionality"""

    # Create a mock CursorVersion
    version_info = CursorVersion(
        version="0.42.1",
        commit="60faf7b51077ed1df1db718157bbfed740d2e168",
        arch="x64",
        full_output="cursor 0.42.1\n60faf7b51077ed1df1db718157bbfed740d2e168"
    )

    # Create directories
    test_dir = Path(__file__).parent / "test_deploy"
    cache_dir = test_dir / "cache"
    remote_dir = test_dir / "remote"
    cache_dir.mkdir(parents=True, exist_ok=True)
    remote_dir.mkdir(parents=True, exist_ok=True)

    print("=== Testing Deployment Flow ===")
    print(f"Version: {version_info.version}")
    print(f"Commit: {version_info.commit}")
    print(f"Cache directory: {cache_dir}")
    print(f"Remote directory: {remote_dir}")

    try:
        # 1. Test downloads
        print("\n1. Testing downloads...")
        download_manager = DownloadManager(cache_dir=cache_dir)

        # Download server package
        server_file = download_manager.download(
            version_info=version_info,
            arch="x64",
            os_type="linux",
            force=True,
            package_type="server"
        )

        if server_file:
            print(f"✓ Server package: {server_file.name} ({server_file.stat().st_size} bytes)")
        else:
            print("✗ Server package download failed")

        # Download CLI package
        cli_file = download_manager.download_cli_package(
            version_info=version_info,
            arch="x64",
            force=True
        )

        if cli_file:
            print(f"✓ CLI package: {cli_file.name} ({cli_file.stat().st_size} bytes)")
        else:
            print("✗ CLI package download failed")

        # 2. Test deployment (without actual SSH)
        print("\n2. Testing deployment...")

        # Create mock server config
        server = ServerConfig(
            id="test-server",
            name="Test Server",
            host="test.example.com",
            user="testuser",
            port=22,
            arch="x64",
            auth_method="key",
            remote_path=str(remote_dir / "cursor-test")
        )

        # Mock SSH connection
        deploy_manager = DeployManager()

        # Mock the SSH client
        mock_client = MagicMock()
        mock_sftp = MagicMock()

        # Setup mocks
        mock_client.open_sftp.return_value = mock_sftp
        deploy_manager.connection_pool = MagicMock()
        deploy_manager.connection_pool.get_connection.return_value = mock_client

        # Mock file upload
        def mock_put(local, remote):
            # Create the directory structure
            remote_path = Path(remote)
            remote_path.parent.mkdir(parents=True, exist_ok=True)
            # Copy the file
            import shutil
            shutil.copy2(local, remote)

        mock_sftp.put.side_effect = mock_put

        # Test deployment
        success = deploy_manager.deploy(
            server=server,
            local_server_file=server_file,
            local_cli_file=cli_file,
            version_info=version_info
        )

        if success:
            print("✓ Deployment successful")

            # Check what was deployed
            if remote_dir.exists():
                files = list(remote_dir.rglob("*"))
                print(f"Deployed {len(files)} files/directories:")
                for f in sorted(files):
                    if f.is_file():
                        print(f"  - {f.relative_to(remote_dir)} ({f.stat().st_size} bytes)")
                    else:
                        print(f"  - {f.relative_to(remote_dir)}/ (directory)")
        else:
            print("✗ Deployment failed")

    except Exception as e:
        print(f"Error during test: {e}")
        if "UnicodeEncodeError" not in str(e):
            import traceback
            traceback.print_exc()

    finally:
        # Clean up
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\n3. Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_deploy()