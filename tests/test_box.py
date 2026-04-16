"""Tests for MCPBox core functionality."""

import pytest

from mcpbox import Box
from mcpbox.errors import ToolNotFoundError
from mcpbox.models import RateLimitConfig, CircuitBreakerConfig


class TestBox:
    """Tests for the Box class."""

    def test_tool_decorator_registers_tool(self):
        """@box.tool() should register the function as a tool."""
        box = Box()

        @box.tool(name="greet", description="Greet someone")
        def greet(name: str) -> str:
            return f"Hi, {name}!"

        assert len(box._registry.list_tools()) == 1
        tool = box._registry.get("greet")
        assert tool.name == "greet"
        assert tool.description == "Greet someone"

    def test_tool_decorator_uses_function_name(self):
        """If no name given, tool name should be snake_case of function name."""
        box = Box()

        @box.tool()
        def GetUserInfo() -> str:  # noqa: N802
            return "user"

        assert box._registry.get("get_user_info").name == "get_user_info"

    def test_tool_decorator_uses_docstring(self):
        """If no description given, first line of docstring is used."""
        box = Box()

        @box.tool()
        def hello():
            """Say hello.

            More details here.
            """
            return "hi"

        assert box._registry.get("hello").description == "Say hello."

    def test_duplicate_tool_raises(self):
        """Registering the same tool name twice should raise ValueError."""
        box = Box()

        @box.tool(name="dup")
        def tool_a() -> str:
            return "a"

        with pytest.raises(ValueError, match="already registered"):
            box._registry.register(
                box._registry.get("dup")  # re-register same tool
            )

    def test_get_nonexistent_tool(self):
        """Getting a nonexistent tool should raise ToolNotFoundError."""
        box = Box()
        with pytest.raises(ToolNotFoundError, match="not found"):
            box._registry.get("does_not_exist")

    def test_list_tools(self):
        """list_tools should return all registered tools."""
        box = Box()

        @box.tool(name="tool1")
        def t1() -> str:
            return "1"

        @box.tool(name="tool2")
        def t2() -> str:
            return "2"

        tools = box._registry.list_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"tool1", "tool2"}

    def test_list_tools_public(self):
        """list_tools_public should return properly formatted dicts."""
        box = Box()

        @box.tool(name="pub_tool", description="A public tool")
        def pub() -> str:
            return "ok"

        result = box._registry.list_tools_public()
        assert len(result) == 1
        assert result[0]["name"] == "pub_tool"
        assert result[0]["description"] == "A public tool"
        assert "inputSchema" in result[0]

    def test_execute_tool(self):
        """execute should call the handler and return a result."""
        box = Box()

        @box.tool(name="calc")
        def calc(a: int, b: int) -> str:
            return str(a + b)

        result = box._registry.execute("calc", {"a": 3, "b": 5})
        assert result.isError is False
        assert "8" in result.content[0]["text"]

    def test_execute_with_invalid_args(self):
        """Executing with missing args should return an error result."""
        box = Box()

        @box.tool(name="strict")
        def strict(a: int) -> str:
            return str(a)

        result = box._registry.execute("strict", {})  # missing 'a'
        assert result.isError is True

    def test_execute_nonexistent_tool(self):
        """Executing a nonexistent tool should return an error result."""
        box = Box()
        result = box.execute("no_such_tool", {})
        assert result.isError is True

    def test_jsonrpc_request_tools_list(self):
        """tools/list JSON-RPC request should return all tools."""
        box = Box()

        @box.tool(name="rpc_tool")
        def rpc() -> str:
            return "ok"

        response = box._handle_jsonrpc("tools/list", None)
        assert response["result"]["tools"][0]["name"] == "rpc_tool"

    def test_jsonrpc_request_tools_call(self):
        """tools/call JSON-RPC request should execute and return result."""
        box = Box()

        @box.tool(name="call_tool")
        def call_tool(msg: str) -> str:
            return f"got: {msg}"

        response = box._handle_jsonrpc(
            "tools/call",
            {"name": "call_tool", "arguments": {"msg": "hello"}},
        )
        assert response["result"]["content"][0]["text"] == "got: hello"

    def test_jsonrpc_unknown_method(self):
        """Unknown method should return error response."""
        box = Box()
        response = box._handle_jsonrpc("unknown/method", {})
        assert response["error"]["code"] == -32601

    def test_openapi_import(self):
        """import_from_openapi with dict spec should create tools."""
        box = Box()
        box.import_from_openapi(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test", "version": "1.0.0"},
                "paths": {
                    "/ping": {
                        "get": {
                            "operationId": "ping",
                            "summary": "Health check",
                        }
                    }
                },
            }
        )
        tool = box._registry.get("ping")
        assert tool.description == "Health check"

    def test_rate_limit_middleware(self):
        """RateLimitMiddleware should block the 3rd call with max_calls=2."""
        box = Box()
        box.with_rate_limit(RateLimitConfig(max_calls=2, window_seconds=60))

        @box.tool(name="ratelimit_test")
        def rlt() -> str:
            return "ok"

        # First two should pass, third should be rate-limited
        for _ in range(2):
            result = box.execute("ratelimit_test", {})
            assert result.isError is False

        result = box.execute("ratelimit_test", {})
        assert result.isError is True
        assert "Rate limit" in result.content[0]["text"]
        assert "Rate limit" in result.content[0]["text"]


class TestDecorators:
    """Tests for the tool decorator and helpers."""

    def test_to_snake_case(self):
        """snake_case conversion should work for common patterns."""
        from mcpbox.decorators import _to_snake_case

        assert _to_snake_case("GetUserInfo") == "get_user_info"
        assert _to_snake_case("helloWorld") == "hello_world"
        assert _to_snake_case("simple") == "simple"

    def test_python_type_to_json(self):
        """Python type hints should map to JSON Schema types."""
        from mcpbox.decorators import _python_type_to_json

        assert _python_type_to_json(str) == "string"
        assert _python_type_to_json(int) == "integer"
        assert _python_type_to_json(float) == "number"
        assert _python_type_to_json(bool) == "boolean"
        assert _python_type_to_json(list) == "array"
        assert _python_type_to_json(dict) == "object"
