"""
Cursor version detection module
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
        # Try 'cursor --version' first (if in PATH)
        try:
            result = subprocess.run(
                ["cursor", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return Path("cursor")  # Use system command
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check common installation paths
        common_paths = []

        if sys.platform == "win32":
            common_paths = [
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

        for path in common_paths:
            if path.exists():
                return path

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
            # Use cursor --version command
            if self.cursor_path == Path("cursor"):
                # Use system command
                kwargs = dict(
                    args=["cursor", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                # 在 Windows 上尽量避免弹出额外窗口
                if sys.platform == "win32":
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    # 对于 Electron 应用，避免 GUI 弹出只能尽量控制窗口标志，
                    # 如果用户仍然看到窗口，可以通过环境变量强制禁用 CLI 调用。
                    if os.environ.get("CURSOR_SERVER_DEPLOYER_NO_CURSOR_CLI") == "1":
                        raise RuntimeError("Cursor CLI invocation disabled by environment variable")
                result = subprocess.run(**kwargs)
            else:
                # Use full path
                kwargs = dict(
                    args=[str(self.cursor_path), "--version"],
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
