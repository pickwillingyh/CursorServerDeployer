"""
Unit tests for configuration management
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from cursor_server_deployer.config.models import ServerConfig, ExecutionRecord
from cursor_server_deployer.config.manager import ConfigManager


class TestServerConfig:
    """Tests for ServerConfig model"""

    def test_server_config_creation(self):
        """Test creating a server configuration"""
        server = ServerConfig(
            id="test-id",
            name="Test Server",
            host="example.com",
            user="testuser",
            port=22,
            arch="x64",
        )

        assert server.id == "test-id"
        assert server.name == "Test Server"
        assert server.host == "example.com"
        assert server.user == "testuser"
        assert server.port == 22
        assert server.arch == "x64"
        assert server.auth_method == "password"  # Default value
        assert server.remote_path == "~/.cursor-server"  # Default value

    def test_connection_string(self):
        """Test connection string property"""
        server = ServerConfig(
            id="test-id",
            name="Test Server",
            host="example.com",
            user="testuser",
            port=2222,
            arch="x64",
        )

        assert server.connection_string == "testuser@example.com:2222"

    def test_unique_key(self):
        """Test unique key property"""
        server = ServerConfig(
            id="test-id",
            name="Test Server",
            host="example.com",
            user="testuser",
            port=2222,
            arch="x64",
        )

        assert server.unique_key == "example.com:2222:testuser"

    def test_port_validation(self):
        """Test port validation"""
        with pytest.raises(ValueError):
            ServerConfig(
                id="test-id",
                name="Test Server",
                host="example.com",
                user="testuser",
                port=0,  # Invalid port
                arch="x64",
            )

        with pytest.raises(ValueError):
            ServerConfig(
                id="test-id",
                name="Test Server",
                host="example.com",
                user="testuser",
                port=70000,  # Invalid port
                arch="x64",
            )

    def test_valid_arch_values(self):
        """Test valid architecture values"""
        server_x64 = ServerConfig(
            id="test-id",
            name="Test",
            host="example.com",
            user="testuser",
            arch="x64",
        )
        assert server_x64.arch == "x64"

        server_arm64 = ServerConfig(
            id="test-id",
            name="Test",
            host="example.com",
            user="testuser",
            arch="arm64",
        )
        assert server_arm64.arch == "arm64"


class TestExecutionRecord:
    """Tests for ExecutionRecord model"""

    def test_execution_record_creation(self):
        """Test creating an execution record"""
        record = ExecutionRecord(
            action="deploy",
            servers=["server1", "server2"],
            cursor_version="0.42.1",
            cursor_commit="abc123",
            success=True,
        )

        assert record.action == "deploy"
        assert record.servers == ["server1", "server2"]
        assert record.cursor_version == "0.42.1"
        assert record.success is True

    def test_execution_record_valid_actions(self):
        """Test valid action types"""
        for action in ["deploy", "download", "setup-key"]:
            record = ExecutionRecord(
                action=action,
                servers=[],
                success=True,
            )
            assert record.action == action


class TestConfigManager:
    """Tests for ConfigManager"""

    def test_add_server(self, tmp_path):
        """Test adding a server configuration"""
        # Use environment variable to override config directory
        env_key = "CURSOR_SERVER_DEPLOYER_CONFIG_DIR"
        old_value = os.environ.get(env_key)

        try:
            os.environ[env_key] = str(tmp_path)

            # Create a subclass that uses the temp directory
            class TestConfigManager(ConfigManager):
                CONFIG_DIR = tmp_path
                CONFIG_FILE = tmp_path / "config.json"
                HISTORY_FILE = tmp_path / "history.json"

            config = TestConfigManager()
            server = config.add_server(
                host="example.com",
                user="testuser",
                port=22,
                arch="x64",
            )

            assert server.host == "example.com"
            assert server.user == "testuser"
            assert len(config.servers) == 1
            assert config.servers[0].id == server.id
        finally:
            if old_value is not None:
                os.environ[env_key] = old_value
            elif env_key in os.environ:
                del os.environ[env_key]

    def test_get_server(self, tmp_path):
        """Test getting a server by ID"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()
        added_server = config.add_server(
            host="example.com",
            user="testuser",
        )

        server = config.get_server(added_server.id)
        assert server is not None
        assert server.host == "example.com"

        # Test non-existent server
        assert config.get_server("non-existent-id") is None

    def test_remove_server(self, tmp_path):
        """Test removing a server"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()
        server = config.add_server(
            host="example.com",
            user="testuser",
        )

        assert len(config.servers) == 1
        result = config.remove_server(server.id)
        assert result is True
        assert len(config.servers) == 0

    def test_list_servers(self, tmp_path):
        """Test listing all servers"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()
        config.add_server(host="server1.com", user="user1")
        config.add_server(host="server2.com", user="user2")

        servers = config.list_servers()
        assert len(servers) == 2

    def test_get_server_by_connection(self, tmp_path):
        """Test getting server by connection details"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()
        config.add_server(host="example.com", user="testuser", port=2222)

        server = config.get_server_by_connection("example.com", 2222, "testuser")
        assert server is not None

        server = config.get_server_by_connection("example.com", 22, "testuser")
        assert server is None

    def test_update_server(self, tmp_path):
        """Test updating server configuration"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()
        server = config.add_server(host="example.com", user="testuser")

        updated = config.update_server(server.id, auth_method="key", key_setup=True)
        assert updated.auth_method == "key"
        assert updated.key_setup is True

    def test_execution_history(self, tmp_path):
        """Test execution history management"""
        class TestConfigManager(ConfigManager):
            CONFIG_DIR = tmp_path
            CONFIG_FILE = tmp_path / "config.json"
            HISTORY_FILE = tmp_path / "history.json"

        config = TestConfigManager()

        record = ExecutionRecord(
            action="deploy",
            servers=["server1"],
            cursor_version="0.42.1",
            success=True,
        )

        config.add_execution_record(record)

        last = config.get_last_execution()
        assert last is not None
        assert last.action == "deploy"
        assert last.success is True

        recent = config.get_recent_executions()
        assert len(recent) >= 1
