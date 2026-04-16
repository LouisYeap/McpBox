"""Core Pydantic data models for MCPBox."""

from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Definition of a single MCP tool."""

    name: str = Field(description="Tool name in snake_case")
    description: str = Field(default="", description="Human-readable description")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for tool input",
    )
    group: Optional[str] = Field(default=None, description="Tool group/tag")
    tags: List[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)
    handler: Any = Field(default=None, exclude=True)  # Callable, not serialised


class ToolCallContext(BaseModel):
    """Context passed through a tool call lifecycle."""

    tool_name: str
    arguments: Dict[str, Any]
    trace_id: Optional[str] = None


class CallToolResult(BaseModel):
    """Result returned by a tool call (MCP protocol format)."""

    content: List[Dict[str, Any]]
    isError: bool = False


class ToolListItem(BaseModel):
    """A single tool entry in tools/list response."""

    name: str
    description: str
    inputSchema: Dict[str, Any]


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request object."""

    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response object."""

    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ServerConfig(BaseModel):
    """MCPBox server configuration."""

    name: str = "mcpbox"
    version: str = "0.1.0"
    description: Optional[str] = None


# ── Middleware config models ──────────────────────────────────────────────


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    max_calls: int = Field(default=100, ge=1)
    window_seconds: int = Field(default=60, ge=1)


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = Field(default=5, ge=1)
    recovery_timeout: float = Field(default=30.0, ge=0)


class TimeoutConfig(BaseModel):
    """Timeout configuration."""

    seconds: float = Field(default=30.0, gt=0)
