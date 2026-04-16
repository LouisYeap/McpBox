"""MCPBox — Quick Start Example

Run with: python quickstart.py
"""

from mcpbox import Box

box = Box(name="demo-box")


@box.tool(name="hello", description="Say hello to someone")
def hello(name: str = "World") -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


@box.tool(name="add", description="Add two numbers together")
def add(a: int, b: int) -> str:
    """Return the sum of two integers."""
    return str(a + b)


@box.tool(name="weather", description="Get weather for a city")
async def get_weather(city: str, days: int = 1) -> str:
    """Fetch weather forecast for a city."""
    return f"{city}: sunny, {18 + days * 2}°C for the next {days} day(s)."


if __name__ == "__main__":
    print("Starting MCPBox demo server (stdio mode)...")
    print("Available tools:", [t["name"] for t in box._registry.list_tools_public()])
    box.run()
