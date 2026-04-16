"""Tool registry — the central record of all available MCP tools."""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional

from mcpbox.errors import MCPBoxError, ToolNotFoundError
from mcpbox.models import CallToolResult, ToolCallContext, ToolDefinition


class ToolRegistry:
    """Holds and manages all registered MCP tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._groups: Dict[str, List[str]] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name is already taken."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool
        if tool.group:
            self._groups.setdefault(tool.group, []).append(tool.name)

    def get(self, name: str) -> ToolDefinition:
        """Get a tool by name. Raises ToolNotFoundError if not found."""
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(sorted(self._tools.keys()))
            raise ToolNotFoundError(
                f"Tool '{name}' not found. Available tools: [{available}]"
            )
        return tool

    def list_tools(
        self,
        group: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[ToolDefinition]:
        """List tools, optionally filtered by group."""
        tools = self._tools.values()
        if enabled_only:
            tools = (t for t in tools if t.enabled)
        if group is not None:
            names = self._groups.get(group, [])
            tools = (self._tools[n] for n in names if self._tools[n].enabled)
        return list(tools)

    def list_tools_public(self) -> List[Dict[str, str]]:
        """Return tools in the public tools/list format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
            }
            for t in self.list_tools()
        ]

    def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        middleware_chain: Optional[List[Any]] = None,
    ) -> CallToolResult:
        """Execute a tool by name with given arguments."""
        try:
            tool = self.get(name)
        except MCPBoxError as exc:
            return CallToolResult(
                content=[{"type": "text", "text": str(exc)}],
                isError=True,
            )

        ctx = ToolCallContext(tool_name=name, arguments=arguments)

        # Run middleware (before hooks)
        if middleware_chain:
            for mw in middleware_chain:
                try:
                    mw.before_execute(ctx)
                except MCPBoxError as exc:
                    return CallToolResult(
                        content=[{"type": "text", "text": str(exc)}],
                        isError=True,
                    )

        try:
            result = tool.handler(**arguments)
            # Handle async functions — run in a new event loop
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            return CallToolResult(
                content=[{"type": "text", "text": str(result)}],
                isError=False,
            )
        except MCPBoxError as exc:
            # Expected business-logic errors — return as error result, not raise
            return CallToolResult(
                content=[{"type": "text", "text": str(exc)}],
                isError=True,
            )
        except Exception as exc:
            return CallToolResult(
                content=[{"type": "text", "text": str(exc)}],
                isError=True,
            )
