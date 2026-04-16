"""Circuit breaker middleware — prevents cascading failures."""

from __future__ import annotations

import time
from typing import Any, Optional

from mcpbox.errors import CircuitBreakerOpenError
from mcpbox.models import CircuitBreakerConfig, ToolCallContext


class CircuitBreaker:
    """Circuit breaker state machine (closed → open → half-open)."""

    def __init__(self, config: CircuitBreakerConfig) -> None:
        self.failure_threshold: int = config.failure_threshold
        self.recovery_timeout: float = config.recovery_timeout
        self._failures: int = 0
        self._last_failure_time: Optional[float] = None
        self._state: str = "closed"  # closed | open | half-open

    def is_open(self) -> bool:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                return False
            return True
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self.failure_threshold:
            self._state = "open"


class CircuitBreakerMiddleware:
    """Middleware that opens the circuit after repeated tool failures."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        self.cb = CircuitBreaker(config or CircuitBreakerConfig())

    def before_execute(self, ctx: ToolCallContext) -> None:
        if self.cb.is_open():
            raise CircuitBreakerOpenError()

    def after_execute(self, ctx: ToolCallContext, result: Any) -> None:
        if getattr(result, "isError", False):
            self.cb.record_failure()
        else:
            self.cb.record_success()
