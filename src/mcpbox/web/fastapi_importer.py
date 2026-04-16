"""FastAPI route importer — converts FastAPI routes to MCP tools."""

from __future__ import annotations

import inspect
from typing import Any, List, Union

from mcpbox.models import ToolDefinition


class FastAPIImporter:
    """Import FastAPI routes as MCP tools."""

    def __init__(self, app: Any, prefix: str = "") -> None:
        self.app = app
        self.prefix = prefix

    def parse(self) -> List[ToolDefinition]:
        """Extract all routes from a FastAPI app/router."""
        tools: List[ToolDefinition] = []

        # Get routes from app or router
        routes = getattr(self.app, "routes", [])
        for route in routes:
            if not hasattr(route, "path"):
                continue
            path: str = route.path
            if self.prefix and not path.startswith(self.prefix):
                continue

            # Get HTTP methods
            methods = getattr(route, "methods", ["GET"])
            for method in methods:
                if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue

                # Build tool name from path
                name = self._path_to_name(path)
                description = f"{method.upper()} {path}"

                # Extract function signature for schema
                func = getattr(route, "endpoint", None)
                input_schema = self._infer_schema(func) if func else {"type": "object"}

                def make_handler(path: str = path, method: str = method):
                    async def handler(**kwargs) -> str:
                        return f"FastAPI {method} {path} called with {kwargs}"

                    return handler

                tools.append(
                    ToolDefinition(
                        name=name,
                        description=description,
                        input_schema=input_schema,
                        handler=make_handler(),
                    )
                )

        return tools

    @staticmethod
    def _path_to_name(path: str) -> str:
        import re

        segments = [s for s in path.strip("/").split("/") if s and not s.startswith("{")]
        name = "_".join(segments) or "root"
        # Replace {param} placeholders with generic names
        name = re.sub(r"\{[^}]+\}", "by_id", name)
        return name.lower()

    @staticmethod
    def _infer_schema(func: Any) -> dict:
        if func is None:
            return {"type": "object", "properties": {}}

        try:
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name in ("request", "self"):
                    continue
                properties[param_name] = {"type": "string"}
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            return {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        except Exception:
            return {"type": "object", "properties": {}}
