"""
Basic test to verify the package structure
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Test imports
    from cursor_server_deployer.config import ConfigManager, ServerConfig, DeploymentHistory
    from cursor_server_deployer.version import VersionDetector
    from cursor_server_deployer.download import DownloadManager
    from cursor_server_deployer.ssh import KeyManager, SSHConnectionPool
    from cursor_server_deployer.deploy import DeployManager
    from cursor_server_deployer.utils import Logger

    print("[OK] All imports successful")

    # Test basic functionality
    print("\nTesting basic functionality...")

    # Test ConfigManager
    config = ConfigManager()
    print(f"[OK] ConfigManager initialized")
    print(f"  Config dir: {config.CONFIG_DIR}")
    print(f"  Servers: {len(config.list_servers())}")

    # Test Logger
    logger = Logger(verbose=True)
    logger.info("Logger test successful")
    print("[OK] Logger working")

    # Test DownloadManager
    downloader = DownloadManager()
    print(f"[OK] DownloadManager initialized")
    print(f"  Cache dir: {downloader.cache_dir}")

    print("\n[PASS] Basic tests passed!")
    print("\nTo use the tool, run:")
    print("  python -m cursor_server_deployer --help")
    print("  or")
    print("  uvx cursor-server-deployer --help")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
