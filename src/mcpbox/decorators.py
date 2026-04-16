"""Decorator for registering Python functions as MCP tools."""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from mcpbox.models import ToolDefinition


def tool(
    box: "Box",
    name: Optional[str] = None,
    description: Optional[str] = None,
    group: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """Register a function as an MCP tool on a Box instance.

    Args:
        box:       The Box instance to register with.
        name:      Tool name (defaults to function __name__ in snake_case).
        description: Human-readable description (defaults to docstring).
        group:     Optional group/category for the tool.
        tags:      Optional list of string tags.

    Example::

        from mcpbox import Box

        box = Box()

        @box.tool(description="Return the current weather")
        async def get_weather(city: str, days: int = 1) -> str:
            return f"{city}: sunny, 25°C"
    """

    def decorator(func: Callable) -> Callable:
        tool_name = name or _to_snake_case(func.__name__)
        tool_desc = description or (func.__doc__ or "").strip().split("\n")[0]

        # Build a minimal JSON Schema from function signature (best-effort)
        input_schema = _infer_schema(func)

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            input_schema=input_schema,
            group=group,
            tags=tags or [],
            handler=func,
        )
        box._registry.register(tool_def)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _to_snake_case(name: str) -> str:
    """Convert a name to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _infer_schema(func: Callable) -> Dict[str, Any]:
    """Infer a JSON Schema from a function's type hints (best-effort)."""
    import inspect

    hints = {}
    try:
        hints = func.__annotations__ or {}
    except Exception:
        pass

    sig = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        if param_name in hints:
            json_type = _python_type_to_json(hints[param_name])
            properties[param_name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        else:
            properties[param_name] = {"type": "string"}

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


_PYTHON_TYPE_TO_JSON = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def _python_type_to_json(typ: Any) -> str:
    """Map a Python type (or string name) to a JSON Schema type string."""
    name = getattr(typ, "__name__", str(typ))
    return _PYTHON_TYPE_TO_JSON.get(name, "string")
