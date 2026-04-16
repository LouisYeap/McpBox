"""Tracing middleware — injects and propagates trace IDs across tool calls."""

from __future__ import annotations

import uuid
from typing import Any

from mcpbox.models import ToolCallContext


class TracingMiddleware:
    """Injects a trace_id into every tool call context for observability."""

    def before_execute(self, ctx: ToolCallContext) -> None:
        if ctx.trace_id is None:
            ctx.trace_id = uuid.uuid4().hex[:16]

    def after_execute(self, ctx: ToolCallContext, result: Any) -> None:
        # trace_id is already set; this hook exists for instrumentation hooks
        pass
