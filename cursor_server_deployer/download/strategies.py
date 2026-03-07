"""
Download strategies for different Cursor versions
"""

from abc import ABC, abstractmethod

from cursor_server_deployer.version.detector import CursorVersion


class DownloadStrategy(ABC):
    """Base class for download strategies"""

    @abstractmethod
    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for Cursor server

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)

        Returns:
            Download URL
        """
        pass

    @abstractmethod
    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get filename for the downloaded file

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS

        Returns:
            Filename
        """
        pass


class DefaultStrategy(DownloadStrategy):
    """
    Default download strategy for Cursor 2.x versions
    Uses Azure Blob storage
    """

    BASE_URL = "https://cursor.blob.core.windows.net/remote-releases"

    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for Cursor server

        URL format:
        https://cursor.blob.core.windows.net/remote-releases/{version}-{commit}/vscode-reh-{os}-{arch}.tar.gz
        """
        return (
            f"{self.BASE_URL}/"
            f"{version_info.version}-{version_info.commit}/"
            f"vscode-reh-{os_type}-{arch}.tar.gz"
        )

    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """Get filename for the downloaded file"""
        return (
            f"cursor-server-"
            f"{version_info.version}-{version_info.commit}-"
            f"{os_type}-{arch}.tar.gz"
        )


class StrategyFactory:
    """Factory for selecting download strategy based on version"""

    def get_strategy(self, version: str) -> DownloadStrategy:
        """
        Get appropriate download strategy for version

        Args:
            version: Cursor version string

        Returns:
            Appropriate download strategy
        """
        # Check version and return appropriate strategy
        # Currently, we only have the default strategy for version 2.x
        if version.startswith("1."):
            return DefaultStrategy()
        elif version.startswith("2."):
            return DefaultStrategy()
        elif version.startswith("3."):
            return DefaultStrategy()
        else:
            # Default for unknown versions
            return DefaultStrategy()
