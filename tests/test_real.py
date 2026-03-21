#!/usr/bin/env python3
"""
Test with real server using password authentication
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.manager import DownloadManager
from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config import ServerConfig, ConfigManager

def test_real_deployment():
    """Test deployment to a real server"""

    # Create a mock CursorVersion (in real scenario, this would be detected from local Cursor)
    version_info = CursorVersion(
        version="0.42.1",  # Replace with actual version
        commit="60faf7b51077ed1df1db718157bbfed740d2e168",  # Replace with actual commit
        arch="x64",
        full_output="cursor 0.42.1\n60faf7b51077ed1df1db718157bbfed740d2e168"
    )

    print("=== Real Server Deployment Test ===")
    print(f"Server: localhost (for testing)")
    print(f"Username: test")
    print(f"Password: dev")
    print(f"Version: {version_info.version}")

    try:
        # 1. Add server configuration
        print("\n1. Adding server configuration...")
        config_manager = ConfigManager()

        server = ServerConfig(
            id="test-server",
            name="Test Server",
            host="localhost",  # For testing, use your actual server
            user="test",       # Use your actual username
            port=22,          # Use your actual port
            arch="x64",
            auth_method="password",
            remote_path="/home/test/.cursor-server"
        )

        # Save server config
        config_manager.add_server(server)
        print(f"✓ Added server: {server.name}")

        # 2. Test download
        print("\n2. Testing downloads...")
        cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
        download_manager = DownloadManager(cache_dir=cache_dir)

        # Download server package
        server_file = download_manager.download(
            version_info=version_info,
            arch="x64",
            os_type="linux",
            force=False,  # Use cache if available
            package_type="server"
        )

        if server_file:
            print(f"✓ Server package: {server_file.name}")
        else:
            print("✗ Server package download failed")
            return

        # Download CLI package
        cli_file = download_manager.download_cli_package(
            version_info=version_info,
            arch="x64",
            force=False
        )

        if cli_file:
            print(f"✓ CLI package: {cli_file.name}")
        else:
            print("✗ CLI package download failed")
            return

        # 3. Test deployment (this would fail for localhost without proper setup)
        print("\n3. Testing deployment...")
        deploy_manager = DeployManager()

        # This would normally ask for password
        print("Note: For actual deployment, you would need:")
        print("- A real server accessible via SSH")
        print("- The correct username and password")
        print("- Proper permissions on the remote server")

        # Mock the password input
        # password = getpass.getpass("Enter password for test@localhost: ")

        # For now, just show what would happen
        print("\nExpected deployment flow:")
        print("1. Connect to server via SSH")
        print("2. Upload server package to remote server")
        print("3. Extract server package to /home/test/.cursor-server/cursor-{commit}/")
        print("4. Upload CLI package to remote server")
        print("5. Extract CLI package to /home/test/.cursor-server/cursor-{commit}/cli/")
        print("6. Set up proper permissions")
        print("7. Verify deployment")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_deployment()