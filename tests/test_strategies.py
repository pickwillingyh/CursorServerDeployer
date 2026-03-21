"""
Unit tests for download strategies
"""

import pytest
from cursor_server_deployer.version.detector import CursorVersion
from cursor_server_deployer.download.strategies import (
    DefaultStrategy,
    AzureStrategy,
    StrategyFactory,
)


class TestDefaultStrategy:
    """Tests for DefaultStrategy"""

    def setup_method(self):
        self.strategy = DefaultStrategy()
        self.version_info = CursorVersion(
            version="0.42.1",
            commit="60faf7b51077ed1df1db718157bbfed740d2e168",
            arch="x64",
            full_output="test",
        )

    def test_get_download_url(self):
        """Test server download URL generation"""
        url = self.strategy.get_download_url(self.version_info, "x64", "linux")
        expected = "https://downloads.cursor.com/production/60faf7b51077ed1df1db718157bbfed740d2e168/linux/x64/cursor-reh-linux-x64.tar.gz"
        assert url == expected

    def test_get_download_url_arm64(self):
        """Test server download URL for arm64"""
        url = self.strategy.get_download_url(self.version_info, "arm64", "linux")
        assert "arm64" in url
        assert "linux" in url

    def test_get_filename_includes_commit(self):
        """Test that filename includes commit hash for cache uniqueness"""
        filename = self.strategy.get_filename(self.version_info, "x64", "linux")
        assert "60faf7b5" in filename  # First 8 chars of commit
        assert filename == "cursor-reh-linux-x64-60faf7b5.tar.gz"

    def test_get_cli_download_url(self):
        """Test CLI download URL generation"""
        url = self.strategy.get_cli_download_url(self.version_info, "x64", "linux")
        expected = "https://downloads.cursor.com/production/60faf7b51077ed1df1db718157bbfed740d2e168/linux/x64/cli-linux-x64.tar.gz"
        assert url == expected

    def test_get_cli_filename_includes_commit(self):
        """Test that CLI filename includes commit hash"""
        filename = self.strategy.get_cli_filename(self.version_info, "x64", "linux")
        assert "60faf7b5" in filename
        assert filename == "cli-linux-x64-60faf7b5.tar.gz"


class TestAzureStrategy:
    """Tests for AzureStrategy"""

    def setup_method(self):
        self.strategy = AzureStrategy()
        self.version_info = CursorVersion(
            version="0.42.1",
            commit="abc123def456789",
            arch="x64",
            full_output="test",
        )

    def test_get_download_url_uses_version_commit(self):
        """Test that AzureStrategy uses the actual commit from version_info"""
        url = self.strategy.get_download_url(self.version_info, "x64", "linux")
        assert "abc123def456789" in url
        assert "downloads.cursor.com" in url

    def test_get_filename_includes_commit(self):
        """Test that filename includes commit hash"""
        filename = self.strategy.get_filename(self.version_info, "x64", "linux")
        assert "abc123de" in filename  # First 8 chars

    def test_get_cli_download_url_uses_version_commit(self):
        """Test that CLI URL uses the actual commit from version_info"""
        url = self.strategy.get_cli_download_url(self.version_info, "x64", "linux")
        assert "abc123def456789" in url


class TestStrategyFactory:
    """Tests for StrategyFactory"""

    def test_factory_returns_default_strategy(self):
        """Test that factory returns DefaultStrategy"""
        factory = StrategyFactory()
        strategy = factory.get_strategy("0.42.1")
        assert isinstance(strategy, DefaultStrategy)

    def test_factory_ignores_version_parameter(self):
        """Test that factory works for any version string"""
        factory = StrategyFactory()
        strategy1 = factory.get_strategy("0.1.0")
        strategy2 = factory.get_strategy("99.99.99")
        assert isinstance(strategy1, DefaultStrategy)
        assert isinstance(strategy2, DefaultStrategy)


class TestVersionInfoInUrls:
    """Tests to ensure version_info.commit is used in all URLs"""

    def test_different_commits_produce_different_urls(self):
        """Test that different commits produce different URLs"""
        strategy = DefaultStrategy()

        version1 = CursorVersion(
            version="0.42.1",
            commit="aaaaaaaaaaaaaaaa",
            arch="x64",
            full_output="test",
        )
        version2 = CursorVersion(
            version="0.42.1",
            commit="bbbbbbbbbbbbbbbb",
            arch="x64",
            full_output="test",
        )

        url1 = strategy.get_download_url(version1, "x64", "linux")
        url2 = strategy.get_download_url(version2, "x64", "linux")

        assert url1 != url2
        assert "aaaaaaaaaaaaaaaa" in url1
        assert "bbbbbbbbbbbbbbbb" in url2
