"""Rate limiting middleware using a token-bucket algorithm."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, Optional

from mcpbox.errors import RateLimitError
from mcpbox.models import RateLimitConfig, ToolCallContext


class RateLimitMiddleware:
    """Token-bucket rate limiter per tool or global."""

    def __init__(self, config: RateLimitConfig) -> None:
        self.max_calls: int = config.max_calls
        self.window_seconds: int = config.window_seconds
        self._calls: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def before_execute(self, ctx: ToolCallContext) -> None:
        key = ctx.tool_name
        now = time.monotonic()
        with self._lock:
            # Expire old calls outside the window
            cutoff = now - self.window_seconds
            self._calls[key] = [t for t in self._calls[key] if t > cutoff]

            if len(self._calls[key]) >= self.max_calls:
                retry_after = int(self._calls[key][0] + self.window_seconds - now) + 1
                raise RateLimitError(
                    f"Rate limit reached for '{key}'. Retry after {retry_after}s."
                )
            self._calls[key].append(now)
