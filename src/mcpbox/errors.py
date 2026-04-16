"""Typed error definitions for MCPBox."""

from typing import Any, Dict, Optional


class MCPBoxError(Exception):
    """Base exception for MCPBox errors."""

    code: int = -32603
    message: str = "Internal error"

    def to_rpc_error(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
        }


class ToolNotFoundError(MCPBoxError):
    """Raised when a requested tool is not registered."""

    code = -32602
    message = "Tool not found"


class ValidationError(MCPBoxError):
    """Raised when tool arguments fail validation."""

    code = -32602
    message = "Invalid arguments"


class ToolExecutionError(MCPBoxError):
    """Raised when a tool raises an unexpected exception during execution."""

    code = -32603
    message = "Tool execution failed"

    def __init__(self, detail: str):
        self.message = f"Tool execution failed: {detail}"
        super().__init__(self.message)


class TimeoutError(MCPBoxError):
    """Raised when a tool call exceeds its timeout."""

    code = -32000
    message = "Tool call timed out"


class RateLimitError(MCPBoxError):
    """Raised when rate limit is exceeded."""

    code = -32001
    message = "Rate limit exceeded"


class CircuitBreakerOpenError(MCPBoxError):
    """Raised when circuit breaker is open (service unavailable)."""

    code = -32002
    message = "Service temporarily unavailable (circuit breaker open)"


class AuthenticationError(MCPBoxError):
    """Raised when authentication fails."""

    code = -32003
    message = "Authentication required"


class TransportError(MCPBoxError):
    """Raised when transport layer encounters an error."""

    code = -32004
    message = "Transport error"
