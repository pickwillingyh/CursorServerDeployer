"""
Cursor version detection module
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger

@dataclass
class CursorVersion:
    """Cursor version information"""
    version: str
    commit: str
    arch: str
    full_output: str


class VersionDetector:
    """Detects Cursor version information"""

    def __init__(self, cursor_path: Optional[Path] = None):
        self.cursor_path = cursor_path or self._find_cursor_executable()
        if not self.cursor_path:
            raise RuntimeError(
                "Cursor not found. Please ensure Cursor is installed and accessible."
            )

    def _find_cursor_executable(self) -> Optional[Path]:
        """Find Cursor executable on the system"""
        import sys
        import os
        import subprocess

        logger.info("Searching for Cursor executable...")

        # Try 'cursor --version' first (if in PATH)
        try:
            logger.debug("Trying to run 'cursor --version' from PATH")
            result = subprocess.run(
                ["cursor", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if result.returncode == 0:
                logger.info("✓ Found cursor in PATH")
                return Path("cursor")  # Use system command
            else:
                logger.debug(f"Cursor command returned non-zero exit code: {result.returncode}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Cursor not found in PATH: {e}")
            pass

        # Check common installation paths
        logger.info("Checking common installation paths...")
        common_paths = []
        if sys.platform == "win32":
            # Windows: Check multiple possible locations including the correct bin paths
            common_paths = [
                Path("C:/Program Files/cursor/resources/app/bin/cursor"),
                Path("C:/Program Files/cursor/resources/app/bin/cursor.cmd"),
                Path("C:/Program Files (x86)/cursor/resources/app/bin/cursor"),
                Path("C:/Program Files (x86)/cursor/resources/app/bin/cursor.cmd"),
                Path("C:/Program Files/cursor/Cursor.exe"),
                Path("C:/Program Files (x86)/cursor/Cursor.exe"),
            ]
        elif sys.platform == "darwin":
            common_paths = [
                Path("/Applications/Cursor.app/Contents/MacOS/Cursor"),
            ]
        else:  # Linux
            common_paths = [
                Path("/usr/bin/cursor"),
                Path("/usr/local/bin/cursor"),
            ]

        # Check each path and log the result
        for path in common_paths:
            if path.exists():
                logger.info(f"✓ Found cursor at: {path}")
                return path
            else:
                logger.debug(f"✗ Cursor not found at: {path}")

        # If still not found, try to find in PATH manually
        if sys.platform == "win32":
            logger.info("Searching PATH environment variable...")
            path_env = os.environ.get('PATH', '')
            path_dirs = path_env.split(';')
            for dir_path in path_dirs:
                cursor_path = Path(dir_path) / "cursor.exe"
                if cursor_path.exists():
                    logger.info(f"✓ Found cursor in PATH: {cursor_path}")
                    return cursor_path
                else:
                    logger.debug(f"✗ Cursor not found in PATH directory: {dir_path}")

        logger.error("✗ Cursor executable not found in any common locations")
        return None

    def get_version_info(self) -> CursorVersion:
        """
        Get Cursor version information using 'cursor --version'

        Supported output formats (will auto-detect):

        1) New simple format (current Cursor CLI):
           2.6.13
           60faf7b51077ed1df1db718157bbfed740d2e160
           x64

        2) Older verbose format:
           Cursor 2.6.13
           Commit: 60faf7b51077ed1df1db718157bbfed740d2e160
           OS: win32 x64
        """
        # 1) 优先尝试调用 `cursor --version`（跨平台一致）
        try:
            print('----')
            # Use cursor --version command
            if self.cursor_path == Path("cursor"):
                # Use system command
                kwargs = dict(
                    args=["cursor", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True,
                )
                import sys
                # 在 Windows 上尽量避免弹出额外窗口
                if sys.platform == "win32":
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    # 对于 Electron 应用，避免 GUI 弹出只能尽量控制窗口标志，
                    # 如果用户仍然看到窗口，可以通过环境变量强制禁用 CLI 调用。
                    import os
                    if os.environ.get("CURSOR_SERVER_DEPLOYER_NO_CURSOR_CLI") == "1":
                        raise RuntimeError("Cursor CLI invocation disabled by environment variable")
                logger.debug(f"Running system cursor command: {' '.join(kwargs['args'])}")
                result = subprocess.run(**kwargs)
            else:
                # Use full path - handle .cmd files on Windows
                import sys
                cursor_path_str = str(self.cursor_path)
                logger.debug(f"Running cursor from path: {cursor_path_str}")

                if sys.platform == "win32" and cursor_path_str.lower().endswith(".cmd"):
                    # For .cmd files on Windows, use cmd.exe to execute
                    logger.debug("Using cmd.exe to run .cmd file")
                    kwargs = dict(
                        args=["cmd.exe", "/c", cursor_path_str, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                else:
                    # Use direct execution for other files
                    logger.debug("Using direct execution")
                    kwargs = dict(
                        args=[cursor_path_str, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if sys.platform == "win32":
                        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                result = subprocess.run(**kwargs)

            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to get Cursor version: {result.stderr or result.stdout}"
                )

            # Some Cursor builds print version info to stderr instead of stdout.
            raw_output = result.stdout or result.stderr or ""
            output = raw_output.strip()
            if output:
                return self._parse_version_output(output)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Cursor --version command timed out")
        except Exception as e:
            # 失败时保留原始错误信息，方便在上层输出
            last_error = str(e)
            # 在 verbose 模式下输出详细的错误信息
            import sys
            if "--verbose" in sys.argv or "-v" in sys.argv:
                import traceback
                error_details = traceback.format_exc()
                raise RuntimeError(f"Cursor --version command failed: {e}\n{error_details}")
            # Ignore here and fall back to product.json
            pass

        # 2) 如果命令不可用或输出为空，则回退到 product.json
        version_info = self._get_version_info_from_product_json()
        if version_info:
            return version_info

        msg = "Failed to detect Cursor version from both CLI and product.json"
        if "last_error" in locals() and last_error:
            msg += f" (last CLI error: {last_error})"
        raise RuntimeError(msg)

    def _parse_version_output(self, output: str) -> CursorVersion:
        """Parse cursor --version output"""
        # Normalize lines: strip whitespace and drop empties
        lines = [line.strip() for line in output.splitlines() if line.strip()]

        version = ""
        commit = ""
        arch = ""

        # 1) Try new simple 3-line format:
        #    <version>\n<commit>\n<arch>
        if lines:
            first = lines[0]
            # Heuristic: version line looks like "2.6.13" (digits and dots only)
            if all(ch.isdigit() or ch == "." for ch in first):
                version = first
                if len(lines) >= 2:
                    commit = lines[1]
                if len(lines) >= 3:
                    arch = lines[2]

        # 2) Fallback to older verbose format parsing
        if not version:
            for line in lines:
                if line.startswith("Cursor "):
                    # e.g. "Cursor 2.6.13"
                    version = line[len("Cursor ") :].strip()
                elif line.startswith("Commit:"):
                    commit = line[len("Commit:") :].strip()
                elif "OS:" in line:
                    # Extract architecture from OS line (e.g., "OS: linux x64")
                    parts = line.split()
                    if len(parts) >= 3:
                        arch = parts[2].strip()

        if not version:
            raise RuntimeError(f"Could not parse version from output: {output}")

        if not commit:
            # Fallback: try to get commit from product.json
            commit = self._get_commit_from_product_json()

        return CursorVersion(
            version=version,
            commit=commit,
            arch=arch,
            full_output=output
        )

    def _get_version_info_from_product_json(self) -> Optional[CursorVersion]:
        """Try to build CursorVersion from product.json without invoking the binary."""
        product_json_path = self._find_product_json()
        if not product_json_path:
            return None

        try:
            import json

            with open(product_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            version = data.get("version", "") or data.get("productVersion", "")
            commit = data.get("commit", "")

            # Best-effort arch detection; if not present, fall back to platform defaults
            arch = data.get("targetArch", "")
            if not arch:
                if sys.platform == "win32":
                    arch = "x64"
                elif sys.platform == "darwin":
                    arch = "universal"
                else:
                    arch = ""

            if not version:
                return None

            return CursorVersion(
                version=version,
                commit=commit,
                arch=arch,
                full_output=f"product.json: version={version}, commit={commit}, arch={arch}",
            )
        except Exception:
            return None

    def _find_product_json(self) -> Optional[Path]:
        """Locate Cursor's product.json in common installation directories."""
        candidates = []

        if sys.platform == "win32":
            home = Path.home()
            candidates = [
                home / "AppData/Local/Programs/Cursor/resources/app/product.json",
                home / "AppData/Local/Cursor/resources/app/product.json",
                Path("C:/Program Files/Cursor/resources/app/product.json"),
                Path("C:/Program Files (x86)/Cursor/resources/app/product.json"),
            ]
        elif sys.platform == "darwin":
            candidates = [
                Path("/Applications/Cursor.app/Contents/Resources/app/product.json"),
            ]
        else:
            candidates = [
                Path("/opt/cursor/resources/app/product.json"),
                Path.home() / ".cursor/resources/app/product.json",
            ]

        for path in candidates:
            if path.exists():
                return path

        return None

    def _get_commit_from_product_json(self) -> str:
        """Get commit hash from product.json as fallback."""
        info = self._get_version_info_from_product_json()
        return info.commit if info else ""
