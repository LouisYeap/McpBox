"""Flask route importer — converts Flask routes to MCP tools."""

from __future__ import annotations

import inspect
from typing import Any, List

from mcpbox.models import ToolDefinition


class FlaskImporter:
    """Import Flask routes as MCP tools."""

    def __init__(self, app: Any) -> None:
        self.app = app

    def parse(self) -> List[ToolDefinition]:
        """Extract all routes from a Flask app."""
        tools: List[ToolDefinition] = []

        rules = getattr(self.app, "url_map", []).iterate_rules()
        for rule in rules:
            path: str = rule.rule
            methods = list(rule.methods or [])

            for method in methods:
                if method in ("HEAD", "OPTIONS"):
                    continue
                if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue

                name = self._path_to_name(path)
                description = f"{method} {path}"
                input_schema = self._infer_schema_from_rule(rule)

                def make_handler(path: str = path, method: str = method):
                    async def handler(**kwargs) -> str:
                        return f"Flask {method} {path} called with {kwargs}"

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

        segments = [s for s in path.strip("/").split("/") if s and not s.startswith("<")]
        name = "_".join(segments) or "root"
        name = re.sub(r"<[^>]+>", "by_id", name)
        return name.lower()

    @staticmethod
    def _infer_schema_from_rule(rule: Any) -> dict:
        properties = {}
        required = []

        # Try to get view function signature
        view_func = getattr(rule, "endpoint", None)
        if view_func:
            try:
                if callable(view_func):
                    sig = inspect.signature(view_func)
                    for param_name, param in sig.parameters.items():
                        if param_name == "self":
                            continue
                        properties[param_name] = {"type": "string"}
                        if param.default is inspect.Parameter.empty:
                            required.append(param_name)
            except Exception:
                pass

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
