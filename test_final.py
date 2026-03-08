#!/usr/bin/env python3
"""
Final test script for Cursor server download functionality
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.manager import DownloadManager

def test_download():
    """Test the download functionality"""

    # Create a mock CursorVersion (using a known working commit)
    version_info = CursorVersion(
        version="0.42.1",  # Use a recent version
        commit="60faf7b51077ed1df1db718157bbfed740d2e168",  # This is just an example
        arch="x64",
        full_output="cursor 0.42.1\n60faf7b51077ed1df1db718157bbfed740d2e168"
    )

    # Create download manager with a temporary cache
    cache_dir = Path(__file__).parent / "test_cache"
    download_manager = DownloadManager(cache_dir=cache_dir)

    print("=== Testing Cursor Server Download ===")
    print(f"Version: {version_info.version}")
    print(f"Commit: {version_info.commit}")
    print(f"Cache directory: {cache_dir}")

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
            print(f"SUCCESS: Server package downloaded to: {server_file}")
            print(f"File size: {server_file.stat().st_size} bytes")
        else:
            print("FAILED: Server package download failed")

        # Test CLI package download
        print("\n2. Testing CLI package download...")
        cli_file = download_manager.download_cli_package(
            version_info=version_info,
            arch="x64",
            force=True  # Force download to test
        )

        if cli_file:
            print(f"SUCCESS: CLI package downloaded to: {cli_file}")
            print(f"File size: {cli_file.stat().st_size} bytes")
        else:
            print("FAILED: CLI package download failed")

        # Check what's in cache
        print(f"\n3. Cache contents:")
        if cache_dir.exists():
            files = list(cache_dir.glob("*.tar.gz"))
            print(f"Found {len(files)} files in cache:")
            for f in files:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        else:
            print("Cache directory doesn't exist")

    except Exception as e:
        print(f"Error during test: {e}")
        # Don't print traceback for Unicode errors
        if "UnicodeEncodeError" not in str(e):
            import traceback
            traceback.print_exc()

    finally:
        # Clean up test cache
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print(f"\n4. Cleaned up test cache: {cache_dir}")

if __name__ == "__main__":
    test_download()