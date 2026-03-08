#!/usr/bin/env python3
"""
Simple test without console output
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursor_server_deployer.version.detector import CursorVersion

def test():
    print("=== Simple Test ===")

    # Create version info
    version = CursorVersion(
        version="2.6.13",
        commit="60faf7b51077ed1df1db718157bbfed740d2e160",
        arch="x64",
        full_output="2.6.13\n60faf7b51077ed1df1db718157bbfed740d2e160\nx64"
    )

    print(f"Version: {version.version}")
    print(f"Commit: {version.commit}")
    print(f"Arch: {version.arch}")

    # Test URL generation
    from cursor_server_deployer.download.strategies import StrategyFactory

    strategy = StrategyFactory().get_strategy(version.version)

    # Test server URL
    server_url = strategy.get_download_url(version, "x64", "linux")
    print(f"\nServer URL: {server_url}")

    # Test CLI URL
    cli_url = strategy.get_cli_download_url(version, "x64", "linux")
    print(f"CLI URL: {cli_url}")

    # Test filenames
    server_filename = strategy.get_filename(version, "x64", "linux")
    cli_filename = strategy.get_cli_filename(version, "x64", "linux")

    print(f"\nServer filename: {server_filename}")
    print(f"CLI filename: {cli_filename}")

    return True

if __name__ == "__main__":
    test()