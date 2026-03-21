'''
Download strategies for different Cursor versions
'''

from abc import ABC, abstractmethod

from cursor_server_deployer.version.detector import CursorVersion


class DownloadStrategy(ABC):
    '''Base class for download strategies'''

    @abstractmethod
    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for Cursor server

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)

        Returns:
            Download URL
        '''
        pass

    @abstractmethod
    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get filename for the downloaded file

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS

        Returns:
            Filename
        '''
        pass

    @abstractmethod
    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for CLI package

        Args:
            version_info: Cursor version information
            arch: Target architecture (x64 or arm64)
            os_type: Target OS (usually linux)

        Returns:
            Download URL for CLI package
        '''
        pass

    @abstractmethod
    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get filename for the CLI package

        Args:
            version_info: Cursor version information
            arch: Target architecture
            os_type: Target OS

        Returns:
            Filename for CLI package
        '''
        pass


class DefaultStrategy(DownloadStrategy):
    '''
    Default download strategy for Cursor versions
    Uses downloads.cursor.com
    '''

    BASE_URL = 'https://downloads.cursor.com/production'

    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for Cursor server

        URL format:
        https://downloads.cursor.com/production/{commit}/{os}/{arch}/cursor-reh-{os}-{arch}.tar.gz
        '''
        return (
            f'{self.BASE_URL}/'
            f'{version_info.commit}/'
            f'{os_type}/{arch}/'
            f'cursor-reh-{os_type}-{arch}.tar.gz'
        )

    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''Get filename for the downloaded file (includes version for caching)'''
        # Include commit hash in filename to prevent cache collisions
        return f'cursor-reh-{os_type}-{arch}-{version_info.commit[:8]}.tar.gz'

    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for CLI package

        URL format:
        https://downloads.cursor.com/production/{commit}/{os}/{arch}/cli-{os}-{arch}.tar.gz
        '''
        return (
            f'{self.BASE_URL}/'
            f'{version_info.commit}/'
            f'{os_type}/{arch}/'
            f'cli-{os_type}-{arch}.tar.gz'
        )

    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''Get filename for the CLI package (includes version for caching)'''
        # Include commit hash in filename to prevent cache collisions
        return f'cli-{os_type}-{arch}-{version_info.commit[:8]}.tar.gz'


class AzureStrategy(DownloadStrategy):
    '''
    Azure blob storage strategy for Cursor versions (fallback for older versions)
    Uses Azure blob storage as fallback when downloads.cursor.com fails
    '''

    BASE_URL = 'https://cursor.blob.core.windows.net/remote-releases'

    def get_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for Cursor server
        Uses the actual commit from version_info
        '''
        return (
            f'https://downloads.cursor.com/production/'
            f'{version_info.commit}/'
            f'{os_type}/{arch}/'
            f'cursor-reh-{os_type}-{arch}.tar.gz'
        )

    def get_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''Get filename for the downloaded file (includes version for caching)'''
        return f'cursor-reh-{os_type}-{arch}-{version_info.commit[:8]}.tar.gz'

    def get_cli_download_url(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''
        Get download URL for CLI package
        Uses the actual commit from version_info
        '''
        return (
            f'https://downloads.cursor.com/production/'
            f'{version_info.commit}/'
            f'{os_type}/{arch}/'
            f'cli-{os_type}-{arch}.tar.gz'
        )

    def get_cli_filename(self, version_info: CursorVersion, arch: str, os_type: str = 'linux') -> str:
        '''Get filename for the CLI package (includes version for caching)'''
        return f'cli-{os_type}-{arch}-{version_info.commit[:8]}.tar.gz'


class StrategyFactory:
    '''Factory for selecting download strategy based on version'''

    def get_strategy(self, version: str) -> DownloadStrategy:
        '''
        Get appropriate download strategy for version

        Args:
            version: Cursor version string

        Returns:
            Appropriate download strategy (DefaultStrategy for all versions)
        '''
        # Use DefaultStrategy which uses the actual commit from version_info
        return DefaultStrategy()
