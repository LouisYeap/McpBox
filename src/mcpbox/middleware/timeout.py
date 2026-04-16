"""Timeout middleware — interrupts tool calls that exceed a time limit."""

from __future__ import annotations

import asyncio
from typing import Any

from mcpbox.errors import TimeoutError
from mcpbox.models import TimeoutConfig, ToolCallContext


class TimeoutMiddleware:
    """Middleware that raises TimeoutError if execution exceeds the configured limit."""

    def __init__(self, config: TimeoutConfig) -> None:
        self.seconds: float = config.seconds

    async def before_execute(self, ctx: ToolCallContext) -> None:
        try:
            asyncio.timeout(self.seconds)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{ctx.tool_name}' timed out after {self.seconds}s")

    def after_execute(self, ctx: ToolCallContext, result: Any) -> None:
        pass  # Nothing to do after
