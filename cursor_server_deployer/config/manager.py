"""
Configuration manager for servers and history
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional

from .models import ServerConfig, DeploymentHistory, ExecutionRecord


class ConfigManager:
    """Manages server configurations and deployment history"""

    CONFIG_DIR = Path.home() / ".cursor-server-deployer"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    HISTORY_FILE = CONFIG_DIR / "history.json"

    def __init__(self):
        self._ensure_directories()
        self.servers: List[ServerConfig] = []
        self.history = DeploymentHistory()
        self._load_config()

    def _ensure_directories(self):
        """Ensure configuration directories exist"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        (self.CONFIG_DIR / "logs").mkdir(exist_ok=True)
        (self.CONFIG_DIR / "cache").mkdir(exist_ok=True)

    def _load_config(self):
        """Load configuration from files"""
        # Load servers
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.servers = [
                        ServerConfig(**server_data)
                        for server_data in data.get("servers", [])
                    ]
            except Exception as e:
                # If config is corrupted, start fresh
                self.servers = []

        # Load history
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = DeploymentHistory(**data)
            except Exception:
                self.history = DeploymentHistory()

    def _save_config(self):
        """Save configuration to files"""
        # Save servers
        config_data = {
            "servers": [server.model_dump() for server in self.servers],
            "default_server_id": self.get_default_server_id()
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        # Save history
        with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history.model_dump(), f, indent=2, ensure_ascii=False)

    # Server management

    def add_server(
        self,
        host: str,
        user: str,
        port: int = 22,
        arch: str = "x64",
        name: Optional[str] = None,
        remote_path: str = "~/.cursor-server"
    ) -> ServerConfig:
        """Add a new server configuration"""
        server_id = str(uuid.uuid4())[:8]
        if not name:
            name = f"{user}@{host}"

        server = ServerConfig(
            id=server_id,
            name=name,
            host=host,
            port=port,
            user=user,
            arch=arch,
            remote_path=remote_path
        )

        self.servers.append(server)
        self._save_config()
        return server

    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get server by ID"""
        for server in self.servers:
            if server.id == server_id:
                return server
        return None

    def get_server_by_connection(self, host: str, port: int, user: str) -> Optional[ServerConfig]:
        """Get server by connection details"""
        for server in self.servers:
            if server.host == host and server.port == port and server.user == user:
                return server
        return None

    def list_servers(self) -> List[ServerConfig]:
        """List all servers"""
        return self.servers.copy()

    def remove_server(self, server_id: str) -> bool:
        """Remove a server"""
        server = self.get_server(server_id)
        if server:
            self.servers.remove(server)
            self._save_config()
            return True
        return False

    def update_server(self, server_id: str, **kwargs) -> Optional[ServerConfig]:
        """Update server configuration"""
        server = self.get_server(server_id)
        if server:
            for key, value in kwargs.items():
                if hasattr(server, key):
                    setattr(server, key, value)
            self._save_config()
            return server
        return None

    def get_default_server_id(self) -> Optional[str]:
        """Get default server ID (last used or first)"""
        if not self.servers:
            return None
        if self.history.last_execution and self.history.last_execution.servers:
            # Return last used server
            return self.history.last_execution.servers[0]
        return self.servers[0].id

    def set_server_deployed(self, server_id: str, version: str, commit: str):
        """Mark server as deployed"""
        server = self.get_server(server_id)
        if server:
            server.last_deployed = ExecutionRecord().timestamp
            server.cursor_version = version
            server.cursor_commit = commit
            self._save_config()

    # History management

    def add_execution_record(self, record: ExecutionRecord):
        """Add an execution record to history"""
        self.history.add_execution(record)
        self._save_config()

    def get_last_execution(self) -> Optional[ExecutionRecord]:
        """Get last execution record"""
        return self.history.last_execution

    def get_recent_executions(self, limit: int = 10) -> List[ExecutionRecord]:
        """Get recent executions"""
        return self.history.recent_executions[:limit]

    # Utility methods

    def get_servers_for_deployment(self, server_ids: Optional[List[str]] = None) -> List[ServerConfig]:
        """Get servers for deployment"""
        if server_ids:
            servers = []
            for server_id in server_ids:
                server = self.get_server(server_id)
                if server:
                    servers.append(server)
            return servers
        elif self.servers:
            # Use default server
            default_id = self.get_default_server_id()
            if default_id:
                server = self.get_server(default_id)
                return [server] if server else []
        return []
