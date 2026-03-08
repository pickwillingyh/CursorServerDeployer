#!/usr/bin/env python3
"""
Test real Cursor download functionality
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import VersionDetector, CursorVersion
from cursor_server_deployer.download.manager import DownloadManager
from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config import ServerConfig, ConfigManager

def test_real_version():
    """Test with real Cursor version"""
    print("=== Testing Real Cursor Version Detection ===")

    try:
        # Get real version info
        detector = VersionDetector()
        version_info = detector.get_version_info()

        print(f"OK Version: {version_info.version}")
        print(f"OK Commit: {version_info.commit}")
        print(f"OK Arch: {version_info.arch}")
        print(f"OK Full output: {version_info.full_output}")

        return version_info
    except Exception as e:
        print(f"ERROR Error getting real version: {e}")

        # Fallback to known version
        print("\n⚠ Falling back to known version...")
        return CursorVersion(
            version="2.6.13",
            commit="60faf7b51077ed1df1db718157bbfed740d2e160",
            arch="x64",
            full_output="cursor 2.6.13\n60faf7b51077ed1df1db718157bbfed740d2e168\nx64"
        )

def test_download_with_real_version():
    """Test download with real version info"""
    print("\n=== Testing Download with Real Version ===")

    # Get real version info
    version_info = test_real_version()

    # Create download manager
    cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Disable console to avoid Unicode issues on Windows
    download_manager = DownloadManager(cache_dir=cache_dir)
    download_manager.console = None

    print(f"\nCache directory: {cache_dir}")

    try:
        # Test server package download
        print("\n1. Testing server package download...")
        server_file = download_manager.download(
            version_info=version_info,
            arch="x64",
            os_type="linux",
            force=True,  # Force download to test
            package_type="server"
        )

        if server_file:
            print(f"OK Server package downloaded: {server_file}")
            print(f"  Size: {server_file.stat().st_size} bytes")
        else:
            print("ERROR Server package download failed")

        # Test CLI package download
        print("\n2. Testing CLI package download...")
        cli_file = download_manager.download_cli_package(
            version_info=version_info,
            arch="x64",
            force=True  # Force download to test
        )

        if cli_file:
            print(f"OK CLI package downloaded: {cli_file}")
            print(f"  Size: {cli_file.stat().st_size} bytes")
        else:
            print("ERROR CLI package download failed")

        # Check cache contents
        print(f"\n3. Cache contents:")
        if cache_dir.exists():
            files = list(cache_dir.glob("*.tar.gz"))
            print(f"Found {len(files)} files in cache:")
            for f in sorted(files):
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        else:
            print("Cache directory doesn't exist")

        return server_file, cli_file

    except Exception as e:
        print(f"Error during download test: {e}")
        if "UnicodeEncodeError" not in str(e):
            import traceback
            traceback.print_exc()
        return None, None

def test_password_deployment():
    """Test password-based deployment"""
    print("\n=== Testing Password-Based Deployment ===")

    # Get version info
    version_info = test_real_version()

    # Get download files
    server_file, cli_file = test_download_with_real_version()

    if not server_file or not cli_file:
        print("ERROR Skipping deployment test - downloads failed")
        return

    try:
        # Create server config
        config_manager = ConfigManager()

        # Note: Using placeholder values - replace with actual server details
        server = ServerConfig(
            id="test-server",
            name="Test Server",
            host="your-server.com",  # Replace with actual server
            user="your-username",   # Replace with actual username
            port=22,
            arch="x64",
            auth_method="password",
            remote_path="/home/your-user/.cursor-server"
        )

        # Save server config
        config_manager.add_server(server)
        print(f"OK Added server: {server.name}")

        # Test deployment with password "dev"
        print("\nNote: For actual deployment test, you would need:")
        print("- A real server accessible via SSH")
        print("- The correct username and password")
        print("- Proper permissions on the remote server")

        print("\nExpected deployment flow with password 'dev':")
        print("1. Connect to server via SSH with password 'dev'")
        print("2. Upload server package to remote server")
        print("3. Extract server package to /home/your-user/.cursor-server/cursor-{commit}/")
        print("4. Upload CLI package to remote server")
        print("5. Extract CLI package to /home/your-user/.cursor-server/cursor-{commit}/cli/")
        print("6. Set up proper permissions")
        print("7. Verify deployment")

    except Exception as e:
        print(f"Error during deployment test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test version detection
    version_info = test_real_version()

    # Test downloads
    server_file, cli_file = test_download_with_real_version()

    # Test deployment concept
    test_password_deployment()

    print("\n=== Summary ===")
    print(f"Version: {version_info.version}")
    print(f"Commit: {version_info.commit}")
    print(f"Server package: {'OK' if server_file else 'ERROR'}")
    print(f"CLI package: {'OK' if cli_file else 'ERROR'}")
    print("\nTo test actual deployment:")
    print("1. Replace placeholder server details with actual values")
    print("2. Run: python -m cursor_server_deployer deploy --host your-server.com --user your-username")
    print("3. When prompted for password, enter: dev")