#!/usr/bin/env python3
"""
Robust test download functionality with proper cleanup
"""

import sys
from pathlib import Path
import time
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.manager import DownloadManager

def cleanup_cache():
    """Clean up cache directory"""
    cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
    if cache_dir.exists():
        # Remove any .downloading files
        for downloading_file in cache_dir.glob("*.downloading"):
            try:
                downloading_file.unlink()
                print(f"Cleaned up: {downloading_file}")
            except:
                pass

        # Remove any existing tar.gz files for fresh start
        for tar_file in cache_dir.glob("*.tar.gz"):
            try:
                tar_file.unlink()
                print(f"Removed: {tar_file}")
            except:
                pass

def test_download():
    print("=== Testing Robust Download ===")

    # Clean up cache first
    cleanup_cache()
    time.sleep(1)  # Give some time for file operations to complete

    # Create version info
    version = CursorVersion(
        version="2.6.13",
        commit="60faf7b51077ed1df1db718157bbfed740d2e160",
        arch="x64",
        full_output="2.6.13\n60faf7b51077ed1df1db718157bbfed740d2e168\nx64"
    )

    # Create download manager
    cache_dir = Path.home() / ".cursor-server-deployer" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Cache directory: {cache_dir}")

    download_manager = DownloadManager(cache_dir=cache_dir)
    download_manager.console = None

    try:
        # Test server package download
        print("\n1. Testing server package download...")
        server_file = download_manager.download(
            version_info=version,
            arch="x64",
            os_type="linux",
            force=True,
            package_type="server"
        )

        if server_file and server_file.exists():
            print(f"OK: Server package downloaded to: {server_file}")
            print(f"  Size: {server_file.stat().st_size} bytes")
        else:
            print("ERROR: Server package download failed")

        # Test CLI package download
        print("\n2. Testing CLI package download...")
        cli_file = download_manager.download_cli_package(
            version_info=version,
            arch="x64",
            force=True
        )

        if cli_file and cli_file.exists():
            print(f"OK: CLI package downloaded to: {cli_file}")
            print(f"  Size: {cli_file.stat().st_size} bytes")
        else:
            print("ERROR: CLI package download failed")

        # Check cache contents
        print(f"\n3. Final cache contents:")
        if cache_dir.exists():
            files = list(cache_dir.glob("*.tar.gz"))
            print(f"Found {len(files)} files in cache:")
            for f in sorted(files):
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        else:
            print("Cache directory doesn't exist")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up any remaining .downloading files
        cleanup_cache()

if __name__ == "__main__":
    test_download()