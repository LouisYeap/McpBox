"""MCPBox — the main Box class."""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from mcpbox.decorators import tool
from mcpbox.errors import MCPBoxError
from mcpbox.models import (
    CallToolResult,
    CircuitBreakerConfig,
    RateLimitConfig,
    ServerConfig,
    TimeoutConfig,
)
from mcpbox.registry import ToolRegistry


class TransportType(str, Enum):
    """Supported transport modes."""

    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


class Box:
    """MCPBox main class — register tools and run as an MCP server.

    Example::

        from mcpbox import Box

        box = Box(name="my-assistant")

        @box.tool(description="Say hello")
        async def hello(name: str) -> str:
            return f"Hello, {name}!"

        box.run(transport="stdio")
    """

    def __init__(
        self,
        name: str = "mcpbox",
        version: str = "0.1.0",
        description: Optional[str] = None,
    ) -> None:
        self.name = name
        self.version = version
        self._config = ServerConfig(
            name=name, version=version, description=description
        )
        self._registry = ToolRegistry()
        self._middleware: List[Any] = []

    # ── Tool Registration ────────────────────────────────────────────────────

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        group: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Callable:
        """Decorator to register a Python function as an MCP tool.

        See :func:`mcpbox.decorators.tool` for full documentation.
        """
        return tool(self, name=name, description=description, group=group, tags=tags)

    def import_from_openapi(
        self,
        spec: Union[str, Dict],
        *,
        base_url: Optional[str] = None,
    ) -> None:
        """Import tools from an OpenAPI 3.x document.

        Args:
            spec:      URL string, file path, or dict containing the OpenAPI spec.
            base_url:  Base URL for the API. Inferred from the spec if not given.
        """
        from mcpbox.openapi.parser import OpenAPIParser

        parser = OpenAPIParser(spec, base_url=base_url)
        for tool_def in parser.parse():
            self._registry.register(tool_def)

    def import_from_fastapi(
        self,
        app: Any,
        *,
        prefix: str = "",
    ) -> None:
        """Import routes from a FastAPI app as MCP tools.

        Args:
            app:    FastAPI application or router instance.
            prefix: Optional route prefix to strip from tool names.
        """
        from mcpbox.web.fastapi_importer import FastAPIImporter

        importer = FastAPIImporter(app, prefix=prefix)
        for tool_def in importer.parse():
            self._registry.register(tool_def)

    def import_from_flask(self, app: Any) -> None:
        """Import routes from a Flask app as MCP tools.

        Args:
            app: Flask application instance.
        """
        from mcpbox.web.flask_importer import FlaskImporter

        importer = FlaskImporter(app)
        for tool_def in importer.parse():
            self._registry.register(tool_def)

    # ── Tool Execution ──────────────────────────────────────────────────────

    def execute(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Execute a registered tool with the full middleware chain.

        This is the public API for programmatic tool execution.
        Unlike ``_handle_jsonrpc``, this does not speak JSON-RPC — it
        directly runs the tool and returns the result.
        """
        return self._registry.execute(
            name=name,
            arguments=arguments,
            middleware_chain=self._middleware,
        )

    # ── Middleware ───────────────────────────────────────────────────────────

    def with_auth(self, auth_handler: Any) -> "Box":
        """Add authentication middleware."""
        self._middleware.append(auth_handler)
        return self

    def with_rate_limit(self, config: RateLimitConfig) -> "Box":
        """Add rate limiting middleware."""
        from mcpbox.middleware.rate_limit import RateLimitMiddleware

        self._middleware.append(RateLimitMiddleware(config))
        return self

    def with_circuit_breaker(
        self, config: Optional[CircuitBreakerConfig] = None
    ) -> "Box":
        """Add circuit breaker middleware."""
        from mcpbox.middleware.circuit_breaker import CircuitBreakerMiddleware

        self._middleware.append(
            CircuitBreakerMiddleware(config or CircuitBreakerConfig())
        )
        return self

    def with_timeout(self, seconds: float) -> "Box":
        """Add timeout middleware."""
        from mcpbox.middleware.timeout import TimeoutMiddleware

        self._middleware.append(TimeoutMiddleware(TimeoutConfig(seconds=seconds)))
        return self

    def with_tracing(self) -> "Box":
        """Add distributed tracing middleware."""
        from mcpbox.middleware.tracing import TracingMiddleware

        self._middleware.append(TracingMiddleware())
        return self

    # ── Server Execution ────────────────────────────────────────────────────

    def run(self, transport: TransportType = TransportType.STDIO) -> None:
        """Start the MCPBox server.

        Args:
            transport: One of ``stdio`` (Claude Desktop), ``sse`` (HTTP), or ``http``.
        """
        if transport == TransportType.STDIO:
            from mcpbox.transport.stdio import StdioTransport

            StdioTransport(self).start()
        elif transport == TransportType.SSE:
            from mcpbox.transport.sse import SSETransport

            SSETransport(self).start()
        elif transport == TransportType.HTTP:
            from mcpbox.transport.http import HTTPTransport

            HTTPTransport(self).start()
        else:
            raise ValueError(f"Unknown transport type: {transport}")

    # ── Internal routing ─────────────────────────────────────────────────────

    def _handle_jsonrpc(self, method: str, params: Optional[Dict]) -> Dict:
        """Route an incoming JSON-RPC request to the appropriate handler."""
        handlers = {
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
        }

        handler = handlers.get(method)
        if handler is None:
            return self._error_response(
                -32601, f"Method not found: {method}", None
            )

        try:
            result = handler(params or {})
            return {"jsonrpc": "2.0", "id": None, "result": result}
        except MCPBoxError as exc:
            return self._error_response(exc.code, exc.message, None)
        except Exception as exc:  # noqa: BLE001
            return self._error_response(-32603, str(exc), None)

    def _handle_tools_list(self, params: Dict) -> Dict:
        return {"tools": self._registry.list_tools_public()}

    def _handle_tools_call(self, params: Dict) -> Dict:
        name: str = params.get("name", "")
        arguments: Dict = params.get("arguments", {})
        result = self._registry.execute(
            name=name,
            arguments=arguments,
            middleware_chain=self._middleware,
        )
        return {
            "content": result.content,
            "isError": result.isError,
        }

    @staticmethod
    def _error_response(code: int, message: str, id_: Any) -> Dict:
        return {
            "jsonrpc": "2.0",
            "id": id_,
            "error": {"code": code, "message": message},
        }
