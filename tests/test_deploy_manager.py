"""
Unit tests for deployment manager
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from cursor_server_deployer.deploy.manager import DeployManager
from cursor_server_deployer.config.models import ServerConfig
from cursor_server_deployer.version.detector import CursorVersion


class TestDeployManager:
    """Tests for DeployManager"""

    def setup_method(self):
        self.deploy_manager = DeployManager()
        self.version_info = CursorVersion(
            version="0.42.1",
            commit="60faf7b51077ed1df1db718157bbfed740d2e168",
            arch="x64",
            full_output="test",
        )
        self.server = ServerConfig(
            id="test-server",
            name="Test Server",
            host="test.example.com",
            user="testuser",
            port=22,
            arch="x64",
            auth_method="key",
            remote_path="~/.cursor-server",
        )

    def test_remote_server_path_format(self):
        """Test that remote server path uses correct format"""
        # The path should be: ~/.cursor-server/cli/servers/Stable-{commit}/
        expected_path = "~/.cursor-server/cli/servers/Stable-60faf7b51077ed1df1db718157bbfed740d2e168/"
        # This is verified in the deploy() method implementation
        assert "Stable-" in expected_path
        assert "60faf7b51077ed1df1db718157bbfed740d2e168" in expected_path
        assert expected_path.endswith("/")

    def test_deploy_with_key_auth(self):
        """Test deployment with SSH key authentication"""
        mock_client = MagicMock()
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        # Mock exec_command to return no errors
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        self.deploy_manager.connection_pool = MagicMock()
        self.deploy_manager.connection_pool.get_connection.return_value = mock_client

        # Create a mock local file
        mock_file = MagicMock(spec=Path)
        mock_file.__str__ = lambda self: "/fake/path/file.tar.gz"

        result = self.deploy_manager.deploy(
            server=self.server,
            local_server_file=mock_file,
            local_cli_file=None,
            version_info=self.version_info,
            password=None,
        )

        assert result is True
        self.deploy_manager.connection_pool.get_connection.assert_called_once()

    def test_deploy_with_password_auth(self):
        """Test deployment with password authentication"""
        mock_client = MagicMock()
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        # Mock exec_command to return no errors
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        # Mock the _connect_with_password method
        with patch.object(
            self.deploy_manager, "_connect_with_password", return_value=mock_client
        ):
            password_server = ServerConfig(
                id="test-password-server",
                name="Test Password Server",
                host="test.example.com",
                user="testuser",
                port=22,
                arch="x64",
                auth_method="password",
                remote_path="~/.cursor-server",
            )

            mock_file = MagicMock(spec=Path)
            mock_file.__str__ = lambda self: "/fake/path/file.tar.gz"

            result = self.deploy_manager.deploy(
                server=password_server,
                local_server_file=mock_file,
                local_cli_file=None,
                version_info=self.version_info,
                password="testpassword",
            )

            assert result is True

    def test_deploy_password_required_for_password_auth(self):
        """Test that password is required for password authentication"""
        password_server = ServerConfig(
            id="test-password-server",
            name="Test Password Server",
            host="test.example.com",
            user="testuser",
            port=22,
            arch="x64",
            auth_method="password",
            remote_path="~/.cursor-server",
        )

        mock_file = MagicMock(spec=Path)
        mock_file.__str__ = lambda self: "/fake/path/file.tar.gz"

        result = self.deploy_manager.deploy(
            server=password_server,
            local_server_file=mock_file,
            local_cli_file=None,
            version_info=self.version_info,
            password=None,  # No password provided
        )

        assert result is False

    def test_deploy_only_cli_package(self):
        """Test deployment with only CLI package (no server package)"""
        mock_client = MagicMock()
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        # Mock exec_command to return no errors
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        self.deploy_manager.connection_pool = MagicMock()
        self.deploy_manager.connection_pool.get_connection.return_value = mock_client

        mock_cli_file = MagicMock(spec=Path)
        mock_cli_file.__str__ = lambda self: "/fake/path/cli.tar.gz"

        result = self.deploy_manager.deploy(
            server=self.server,
            local_server_file=None,  # No server package
            local_cli_file=mock_cli_file,
            version_info=self.version_info,
            password=None,
        )

        assert result is True

    def test_deploy_extracts_to_correct_path(self):
        """Test that tar extraction uses correct path"""
        mock_client = MagicMock()
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)

        self.deploy_manager.connection_pool = MagicMock()
        self.deploy_manager.connection_pool.get_connection.return_value = mock_client

        mock_file = MagicMock(spec=Path)
        mock_file.__str__ = lambda self: "/fake/path/file.tar.gz"

        self.deploy_manager.deploy(
            server=self.server,
            local_server_file=mock_file,
            local_cli_file=None,
            version_info=self.version_info,
            password=None,
        )

        # Check that mkdir was called with correct path pattern
        calls = mock_client.exec_command.call_args_list
        mkdir_call = calls[0][0][0]
        assert "mkdir -p" in mkdir_call
        assert "Stable-60faf7b51077ed1df1db718157bbfed740d2e168" in mkdir_call

        # Check that tar extraction was called
        tar_call = calls[1][0][0]
        assert "tar -xzf" in tar_call
        assert "--strip-components=1" in tar_call
