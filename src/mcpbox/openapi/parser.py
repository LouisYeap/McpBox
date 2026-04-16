"""OpenAPI spec parser — converts OpenAPI 3.x documents to MCP tools."""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Dict, List, Optional, Union

from mcpbox.models import ToolDefinition


class OpenAPIParser:
    """Parse an OpenAPI 3.x specification into a list of ToolDefinitions.

    Supports:
    - OpenAPI 3.0 and 3.1 JSON documents
    - Remote URLs (https://)
    - Local file paths (file://)
    - Python dict objects
    """

    def __init__(
        self,
        spec: Union[str, Dict[str, Any]],
        base_url: Optional[str] = None,
    ) -> None:
        self.spec = self._load_spec(spec)
        servers = self.spec.get("servers", [])
        self.base_url: str = base_url or (
            servers[0].get("url", "") if servers else ""
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def parse(self) -> List[ToolDefinition]:
        """Parse all operations into ToolDefinitions."""
        tools: List[ToolDefinition] = []
        for path, methods in self.spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue
                tool = self._parse_operation(path, method, operation)
                if tool:
                    tools.append(tool)
        return tools

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_spec(self, spec: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Load and return the OpenAPI spec dict."""
        if isinstance(spec, dict):
            return spec
        if spec.startswith("http"):
            with urllib.request.urlopen(spec) as resp:
                return json.loads(resp.read().decode())
        if spec.startswith("file://"):
            path = spec[7:]
            with open(path) as f:
                return json.load(f)
        # Try as a local file path
        with open(spec) as f:
            return json.load(f)

    def _parse_operation(
        self, path: str, method: str, operation: Dict[str, Any]
    ) -> Optional[ToolDefinition]:
        """Parse a single OpenAPI operation into a ToolDefinition."""
        operation_id = operation.get("operationId") or self._generate_id(path, method)
        name = self._to_snake_case(operation_id)
        description = (
            operation.get("summary")
            or operation.get("description", "")
        ).split("\n")[0]

        params = operation.get("parameters", [])
        request_body = operation.get("requestBody")
        input_schema = self._build_schema(params, request_body)

        handler = self._create_handler(path, method, operation)

        return ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def _build_schema(
        self,
        params: List[Dict[str, Any]],
        request_body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a JSON Schema dict from OpenAPI parameters and requestBody."""
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for p in params:
            pname = p.get("name", "")
            schema = p.get("schema", {})
            required_flag = p.get("required", False)
            description = p.get("description", "")

            json_schema = {"type": schema.get("type", "string")}
            if description:
                json_schema["description"] = description

            properties[pname] = json_schema
            if required_flag:
                required.append(pname)

        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            body_schema = json_content.get("schema", {})
            if body_schema:
                properties["body"] = body_schema
                if request_body.get("required"):
                    required.append("body")

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _create_handler(self, path: str, method: str, operation: Dict[str, Any]):
        """Create a handler function for this operation."""

        async def handler(**kwargs) -> str:
            # This is a stub — in a real implementation this would call the actual API
            return json.dumps(
                {"path": path, "method": method, "params": kwargs}, ensure_ascii=False
            )

        return handler

    @staticmethod
    def _to_snake_case(name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def _generate_id(path: str, method: str) -> str:
        clean = path.strip("/").replace("/", "_").replace("-", "_")
        return f"{method}_{clean}"
