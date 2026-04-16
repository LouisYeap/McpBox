"""HTTP transport for simple polling-based MCP clients."""

from __future__ import annotations

import json
from typing import Any, Dict

from mcpbox.box import Box


class HTTPTransport:
    """Minimal HTTP transport for simple request/response MCP calls."""

    def __init__(self, box: Box, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.box = box
        self.host = host
        self.port = port

    def start(self) -> None:
        """Start the HTTP server (blocking)."""
        try:
            import uvicorn
            from starlette.applications import Starlette
            from starlette.requests import Request
            from starlette.responses import JSONResponse
            from starlette.routing import Route
        except ImportError:
            raise ImportError(
                "HTTP transport requires starlette and uvicorn. "
                "Install with: pip install 'mcpbox[http]'"
            )

        async def handle(request: Request) -> JSONResponse:
            body = await request.body()
            try:
                rpc_request: Dict[str, Any] = (
                    json.loads(body.decode()) if body else {}
                )
            except json.JSONDecodeError:
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    },
                    status_code=400,
                )

            method: str = rpc_request.get("method", "")
            params: Any = rpc_request.get("params")
            id_: Any = rpc_request.get("id")
            response = self.box._handle_jsonrpc(method, params)
            response["id"] = id_
            return JSONResponse(response)

        app = Starlette(routes=[Route("/mcp", handle), Route("/health", lambda _: JSONResponse({"status": "ok"}))])

        uvicorn.run(app, host=self.host, port=self.port, log_level="info")
