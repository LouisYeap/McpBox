"""STDIO transport — used for local AI integrations (Claude Desktop, Cursor, etc.)."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from mcpbox.box import Box


class StdioTransport:
    """STDIO transport for local MCP clients.

    Reads JSON-RPC requests from stdin, writes responses to stdout.
    All messages are newline-delimited JSON.
    """

    def __init__(self, box: Box) -> None:
        self.box = box

    def start(self) -> None:
        """Block and read JSON-RPC requests from stdin forever."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request: Dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                print(json.dumps(response), flush=True)
                continue

            method: str = request.get("method", "")
            params: Optional[Dict[str, Any]] = request.get("params")
            id_: Any = request.get("id")

            # Handle initialize separately before the router is up
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": id_,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": self.box.name,
                            "version": self.box.version,
                        },
                        "capabilities": {
                            "tools": {"listChanged": True},
                        },
                    },
                }
                print(json.dumps(response), flush=True)
                continue

            if method == "notifications/initialized":
                continue  # Acknowledged, nothing to do

            response = self.box._handle_jsonrpc(method, params)
            response["id"] = id_
            print(json.dumps(response), flush=True)
