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

    @abstractmethod
    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for CLI package

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)

        Returns:
            Download URL for CLI package
        """
        pass

    @abstractmethod
    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get filename for the CLI package

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS

        Returns:
            Filename for CLI package
        """
        pass


class DefaultStrategy(DownloadStrategy):
    """
    Default download strategy for Cursor versions
    Uses downloads.cursor.com
    """

    BASE_URL = "https://downloads.cursor.com/production"

    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for Cursor server

        URL format:
        https://downloads.cursor.com/production/{commit}/{os}/{arch}/cursor-reh-{os}-{arch}.tar.gz
        """
        return (
            f"{self.BASE_URL}/"
            f"{version_info.commit}/"
            f"{os_type}/{arch}/"
            f"cursor-reh-{os_type}-{arch}.tar.gz"
        )

    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """Get filename for the downloaded file"""
        # Use the actual filename from downloads.cursor.com
        return f"cursor-reh-{os_type}-{arch}.tar.gz"

    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for CLI package

        URL format:
        https://downloads.cursor.com/production/{commit}/{os}/{arch}/cli-{os}-{arch}.tar.gz
        """
        return (
            f"{self.BASE_URL}/"
            f"{version_info.commit}/"
            f"{os_type}/{arch}/"
            f"cli-{os_type}-{arch}.tar.gz"
        )

    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """Get filename for the CLI package"""
        # Use the actual filename from downloads.cursor.com
        return f"cli-{os_type}-{arch}.tar.gz"


class AzureStrategy(DownloadStrategy):
    """
    Azure blob storage strategy for Cursor versions
    Uses Azure blob storage for older versions
    """

    BASE_URL = "https://cursor.blob.core.windows.net/remote-releases"

    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for Cursor server from downloads.cursor.com
        Use a known working commit hash
        """
        working_commit = "60faf7b51077ed1df1db718157bbfed740d2e168"
        return f"https://downloads.cursor.com/production/{working_commit}/{os_type}/{arch}/cursor-reh-{os_type}-{arch}.tar.gz"

    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """Get filename for the downloaded file from Azure"""
        return f"cursor-reh-{os_type}-{arch}.tar.gz"

    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """
        Get download URL for CLI package from Azure
        """
        # Azure uses different filenames for CLI packages
        # Some versions use alpine-x64, others use linux-x64
        azure_commit = "61e99179e4080fecf9d8b92c6e2e3e00fbfb53f0"
        if os_type == "linux":
            return (
                f"{self.BASE_URL}/"
                f"{azure_commit}/"
                f"cli-alpine-{arch}.tar.gz"
            )
        else:
            return (
                f"{self.BASE_URL}/"
                f"{azure_commit}/"
                f"cli-{os_type}-{arch}.tar.gz"
            )

    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = "linux") -> str:
        """Get filename for the CLI package from Azure"""
        if os_type == "linux":
            return f"cli-alpine-{arch}.tar.gz"
        else:
            return f"cli-{os_type}-{arch}.tar.gz"


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
        # For now, try Azure first since it's known to work
        return AzureStrategy()
