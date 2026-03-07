"""
Configuration models using Pydantic
"""

from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Server configuration"""
    id: str = Field(..., description="Unique server ID")
    name: str = Field(..., description="Server display name")
    host: str = Field(..., description="Server hostname or IP")
    port: int = Field(default=22, description="SSH port")
    user: str = Field(..., description="SSH username")
    arch: Literal["x64", "arm64"] = Field(default="x64", description="Server architecture")
    remote_path: str = Field(default="~/.cursor-server", description="Remote installation path")
    auth_method: Literal["password", "key"] = Field(default="password", description="Authentication method")
    key_path: Optional[str] = Field(None, description="SSH key path (if using key auth)")
    ssh_config_alias: Optional[str] = Field(None, description="SSH config alias")
    key_setup: bool = Field(default=False, description="Whether SSH key is set up")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_deployed: Optional[str] = Field(None, description="Last deployment timestamp")
    cursor_version: Optional[str] = Field(None, description="Last deployed Cursor version")
    cursor_commit: Optional[str] = Field(None, description="Last deployed Cursor commit")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @property
    def connection_string(self) -> str:
        """Return connection string for display"""
        return f"{self.user}@{self.host}:{self.port}"

    @property
    def unique_key(self) -> str:
        """Return unique key for password/cache purposes"""
        return f"{self.host}:{self.port}:{self.user}"


class DeploymentHistory(BaseModel):
    """Deployment history"""
    last_execution: Optional["ExecutionRecord"] = None
    recent_executions: List["ExecutionRecord"] = Field(default_factory=list)

    def add_execution(self, record: "ExecutionRecord"):
        """Add execution record to history"""
        self.last_execution = record
        self.recent_executions.insert(0, record)
        # Keep only last 50 executions
        self.recent_executions = self.recent_executions[:50]


class ExecutionRecord(BaseModel):
    """Single execution record"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    action: Literal["deploy", "download", "setup-key"] = Field(..., description="Action performed")
    servers: List[str] = Field(default_factory=list, description="Server IDs involved")
    cursor_version: Optional[str] = Field(None, description="Cursor version used")
    cursor_commit: Optional[str] = Field(None, description="Cursor commit used")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# Forward reference resolution
DeploymentHistory.model_rebuild()
