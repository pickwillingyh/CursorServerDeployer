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

        Expected output format:
        Cursor 2.6.13
        Commit: 60faf7b51077ed1df1db718157bbfed740d2e160
        OS: win32 x64
        """
        try:
            # Use cursor --version command
            if self.cursor_path == Path("cursor"):
                # Use system command
                result = subprocess.run(
                    ["cursor", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # Use full path
                result = subprocess.run(
                    [str(self.cursor_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to get Cursor version: {result.stderr}"
                )

            output = result.stdout.strip()
            return self._parse_version_output(output)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Cursor --version command timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to detect Cursor version: {e}")

    def _parse_version_output(self, output: str) -> CursorVersion:
        """Parse cursor --version output"""
        lines = output.split('\n')

        version = ""
        commit = ""
        arch = ""

        for line in lines:
            line = line.strip()
            if line.startswith("Cursor "):
                version = line.replace("Cursor ", "").strip()
            elif line.startswith("Commit:"):
                commit = line.replace("Commit:", "").strip()
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

    def _get_commit_from_product_json(self) -> str:
        """Get commit hash from product.json as fallback"""
        if sys.platform == "win32":
            product_json = Path("C:/Program Files/cursor/resources/app/product.json")
        elif sys.platform == "darwin":
            product_json = Path("/Applications/Cursor.app/Contents/Resources/app/product.json")
        else:
            # Linux - try common locations
            product_json = Path("/opt/cursor/resources/app/product.json")
            if not product_json.exists():
                product_json = Path.home() / ".cursor/resources/app/product.json"

        if product_json.exists():
            try:
                import json
                with open(product_json, 'r') as f:
                    data = json.load(f)
                    return data.get("commit", "")
            except Exception:
                pass

        return ""
