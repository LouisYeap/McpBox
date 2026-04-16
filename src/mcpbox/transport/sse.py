"""SSE (Server-Sent Events) transport for remote MCP clients."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from mcpbox.box import Box


class SSETransport:
    """SSE transport for HTTP-based remote MCP clients.

    Uses Starlette + sse-starlette under the hood for the server.
    """

    def __init__(self, box: Box, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.box = box
        self.host = host
        self.port = port

    def start(self) -> None:
        """Start the SSE server (blocking)."""
        try:
            from starlette.applications import Starlette
            from starlette.responses import JSONResponse, Response
            from starlette.routing import Route
            from sse_starlette import EventSourceResponse
        except ImportError:
            raise ImportError(
                "SSE transport requires starlette and sse-starlette. "
                "Install with: pip install 'mcpbox[sse]'"
            )

        app = Starlette(
            routes=[
                Route("/mcp", self._handle_mcp),
                Route("/health", self._handle_health),
            ]
        )

        import uvicorn

        uvicorn.run(app, host=self.host, port=self.port, log_level="info")

    async def _handle_mcp(self, scope: Any, receive: Any, send: Any) -> Response:
        """Handle incoming MCP HTTP requests.

        GET  /mcp → SSE event stream (tool list changes)
        POST /mcp → JSON-RPC tool call
        """
        # Simple dispatch: use same handler for now
        body = await self._read_body(receive)
        try:
            request: Dict[str, Any] = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )

        method: str = request.get("method", "")
        params: Optional[Dict[str, Any]] = request.get("params")
        id_: Any = request.get("id")
        response = self.box._handle_jsonrpc(method, params)
        response["id"] = id_
        return JSONResponse(response)

    async def _handle_health(self, scope: Any, receive: Any, send: Any) -> Response:
        return JSONResponse({"status": "ok", "name": self.box.name, "version": self.box.version})

    @staticmethod
    async def _read_body(receive: Any) -> bytes:
        message = await receive()
        if message["type"] == "http.request":
            return message.get("body", b"")
        return b""
