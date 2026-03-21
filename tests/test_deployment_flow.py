#!/usr/bin/env python3
"""
Test complete deployment flow
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import VersionDetector, CursorVersion
from cursor_server_deployer.download.manager import DownloadManager
from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config import ServerConfig, ConfigManager

def test_deployment_flow():
    print("=== Testing Complete Deployment Flow ===")

    # Step 1: Get real version
    print("\n1. Getting real Cursor version...")
    try:
        detector = VersionDetector()
        version_info = detector.get_version_info()
        print(f"OK: Version {version_info.version} ({version_info.commit})")
    except Exception as e:
        print(f"ERROR: {e}")
        version_info = CursorVersion(
            version="2.6.13",
            commit="60faf7b51077ed1df1db718157bbfed740d2e160",
            arch="x64",
            full_output="cursor 2.6.13\n60faf7b51077ed1df1db718157bbfed740d2e168\nx64"
        )

    # Step 2: Download packages
    print("\n2. Downloading packages...")
    cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    download_manager = DownloadManager(cache_dir=cache_dir)
    download_manager.console = None

    # Download server package
    server_file = download_manager.download(
        version_info=version_info,
        arch="x64",
        os_type="linux",
        force=False,
        package_type="server"
    )

    # Download CLI package
    cli_file = download_manager.download_cli_package(
        version_info=version_info,
        arch="x64",
        force=False
    )

    if server_file and cli_file:
        print(f"OK: Both packages downloaded")
        print(f"  - Server: {server_file.name} ({server_file.stat().st_size} bytes)")
        print(f"  - CLI: {cli_file.name} ({cli_file.stat().st_size} bytes)")
    else:
        print("ERROR: Failed to download packages")
        return

    # Step 3: Test deployment configuration
    print("\n3. Testing deployment configuration...")

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
    config_manager.add_server(
        host=server.host,
        user=server.user,
        port=server.port,
        arch=server.arch,
        name=server.name,
        remote_path=server.remote_path
    )
    print(f"OK: Server configuration saved")

    # Step 4: Show deployment steps
    print("\n4. Deployment Steps:")
    print("To test actual deployment:")
    print("1. Update server details in test_deployment_flow.py:")
    print("   - host: your-server.com")
    print("   - user: your-username")
    print("   - port: 22 (or your SSH port)")
    print("   - remote_path: /home/your-user/.cursor-server")
    print("\n2. Run deployment:")
    print("   python -m cursor_server_deployer deploy --host your-server.com --user your-username")
    print("\n3. When prompted for password, enter: dev")
    print("\nWhat the deployment will do:")
    print("- Connect to server via SSH with password 'dev'")
    print("- Create directory: /home/your-user/.cursor-server/cursor-{commit}/")
    print("- Upload server package (93 MB)")
    print("- Extract server package")
    print("- Upload CLI package (8.8 MB)")
    print("- Extract CLI package to cli/ directory")
    print("- Set proper permissions")
    print("- Verify deployment")

    # Step 5: Verify files exist
    print("\n5. Verification:")
    if cache_dir.exists():
        files = list(cache_dir.glob("*.tar.gz"))
        print(f"Cache contains {len(files)} files:")
        for f in sorted(files):
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

if __name__ == "__main__":
    test_deployment_flow()