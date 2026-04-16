"""MCPBox — Production Configuration Example

Demonstrates composing middleware for a production deployment.
Run with: python production.py
"""

from mcpbox import Box, TransportType
from mcpbox.models import CircuitBreakerConfig, RateLimitConfig
from mcpbox.middleware.circuit_breaker import CircuitBreakerMiddleware
from mcpbox.middleware.rate_limit import RateLimitMiddleware
from mcpbox.middleware.tracing import TracingMiddleware

box = Box(name="production-box")


@box.tool(name="heavy_task", description="A slow, resource-intensive task")
async def heavy_task(flag: str = "default") -> str:
    import time

    time.sleep(0.1)
    return f"Heavy task completed with flag: {flag}"


# ── Production middleware ──────────────────────────────────────────────────

box.with_tracing()  # Adds trace_id to every call
box.with_rate_limit(RateLimitConfig(max_calls=50, window_seconds=60))
box.with_circuit_breaker(CircuitBreakerConfig(failure_threshold=3))


if __name__ == "__main__":
    import sys

    transport = TransportType.STDIO
    if len(sys.argv) > 1:
        transport = TransportType(sys.argv[1])

    box.run(transport=transport)
