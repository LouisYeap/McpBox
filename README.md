<div align="center">

<!-- Header -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=220&section=header&text=MCPBox&fontSize=90&fontAlignY=38&desc=Turn%20any%20Python%20function%20or%20API%20into%20an%20AI%20tool&descAlignY=60&animation=twinkling" width="100%"/>

<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0D1117" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=0D1117" />
  <img src="https://img.shields.io/badge/MCP%20Protocol-JSON--RPC%202.0-orange?style=for-the-badge&labelColor=0D1117" />
  <img src="https://img.shields.io/badge/Status-Alpha-FF6B6B?style=for-the-badge&labelColor=0D1117" />
</p>

<!-- Quick tagline -->
<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=22&duration=4000&pause=1500&color=4A90E2&center=true&vCenter=true&width=700&height=60&lines=Zero%20protocol%20knowledge%20required;Just%20write%20functions%20or%20import%20OpenAPI%20docs" alt="Typing SVG" />
</p>

</div>

<br>

---

## ✨ What is MCPBox?

**MCPBox** is a production-ready Python framework that turns any Python function or OpenAPI document into an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) tool — with zero protocol knowledge required.

AI agents like Claude Desktop, Cursor, and any MCP-compatible client can discover and call your tools instantly. MCPBox handles the JSON-RPC 2.0 protocol, parameter validation, error formatting, and production-grade concerns like retries, circuit breakers, and rate limiting — all out of the box.

<br>

### Why MCPBox?

| Your situation | Without MCPBox | With MCPBox |
|---|---|---|
| You have Python functions | Manually define schemas, write JSON-RPC handlers | `@box.tool()` — one decorator, done |
| You have an OpenAPI spec | Rewrite every endpoint by hand | `box.import_from_openapi(url)` — fully automatic |
| You have a FastAPI/Flask app | Do it yourself | `box.import_from_fastapi(app)` — one line |
| You need production reliability | Build retries, circuit breakers, rate limits yourself | `box.with_circuit_breaker().with_rate_limit()` — built-in |
| You need auth / tracing / timeouts | Integrate each concern manually | `box.with_auth().with_tracing().with_timeout()` — composable |

<br>

---

## 🚀 Quick Start

### Installation

```bash
pip install mcpbox
```

### From a Python function

```python
from mcpbox import Box

box = Box()


@box.tool(
    name="get_weather",
    description="Get weather forecast for a city",
)
async def get_weather(city: str, days: int = 1) -> str:
    """Fetch weather forecast."""
    return f"{city}: sunny, 25°C for the next {days} day(s)"


box.run()  # starts in stdio mode (Claude Desktop compatible)
```

Your AI agent will immediately see and be able to call `get_weather`.

### From an OpenAPI URL

```python
from mcpbox import Box

box = Box(name="Feishu Assistant")

box.import_from_openapi(
    "https://open.feishu.cn/open-apis/openapi.json",
    base_url="https://open.feishu.cn",
)

box.run(transport="sse")  # or stdio, http
```

**One line turns an entire OpenAPI spec into a suite of AI-callable tools.**

### From an existing FastAPI app

```python
from fastapi import FastAPI
from mcpbox import Box

app = FastAPI()
box = Box()

box.import_from_fastapi(app)  # imports all routes automatically

box.run()
```

<br>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    AI Agent                          │
│            (Claude Desktop / Cursor / any)            │
└──────────────────────┬──────────────────────────────┘
                       │  MCP Protocol (JSON-RPC 2.0)
┌──────────────────────▼──────────────────────────────┐
│                    MCPBox Server                      │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              Tool Registry                    │   │
│  │   @box.tool()  ·  OpenAPI  ·  FastAPI import │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              Router Layer                     │   │
│  │   tools/call  ·  param validation  ·  format │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │            Middleware Chain                   │   │
│  │   Auth  ·  Rate Limit  ·  Circuit Breaker    │   │
│  │   Tracing  ·  Logging  ·  Timeout             │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│   ┌────────┐   ┌────────┐   ┌────────┐             │
│   │  STDIO │   │   SSE  │   │  HTTP  │             │
│   └────────┘   └────────┘   └────────┘             │
└─────────────────────────────────────────────────────┘
```

### Transport Modes

| Mode | Use case |
|------|----------|
| **STDIO** | Local integration — Claude Desktop, Cursor, local AI tools |
| **SSE** | Remote server — long-lived connections over HTTP |
| **HTTP** | Simple polling scenarios |

### Middleware (composable)

| Middleware | What it does |
|---|---|
| `Auth` | API key / Bearer token authentication |
| `RateLimit` | Token-bucket rate limiting |
| `CircuitBreaker` | Auto-open after repeated failures |
| `Timeout` | Per-call execution timeout |
| `Tracing` | Trace IDs across the full call chain |
| `Logging` | Structured request/response logging |

<br>

---

## 📦 Project Structure

```
mcpbox/
├── src/
│   └── mcpbox/
│       ├── __init__.py
│       ├── box.py                 # Core Box class
│       ├── decorators.py          # @box.tool() decorator
│       ├── registry.py            # Tool registry
│       ├── router.py             # JSON-RPC 2.0 router
│       ├── models.py             # Pydantic data models
│       ├── errors.py              # Typed error definitions
│       ├── openapi/
│       │   ├── parser.py         # OpenAPI spec parser
│       │   └── generator.py      # Pydantic model generator
│       ├── web/
│       │   ├── fastapi_importer.py
│       │   └── flask_importer.py
│       ├── transport/
│       │   ├── base.py           # Transport abstraction
│       │   ├── stdio.py          # STDIO transport
│       │   ├── sse.py            # SSE transport
│       │   └── http.py           # HTTP/WebSocket transport
│       ├── middleware/
│       │   ├── auth.py
│       │   ├── rate_limit.py
│       │   ├── circuit_breaker.py
│       │   ├── tracing.py
│       │   ├── timeout.py
│       │   └── logging.py
│       └── cli.py                # CLI scaffold
├── tests/
├── examples/
│   ├── quickstart.py
│   ├── with_openapi.py
│   ├── with_fastapi.py
│   └── production.py
├── pyproject.toml
└── README.md
```

<br>

---

## 🔧 Production Configuration

```python
from mcpbox import Box
from mcpbox.middleware import Auth, RateLimit, CircuitBreaker, Timeout

box = Box(name="production-box")

box.import_from_openapi("https://api.example.com/openapi.json")

box.with_auth(Auth(api_keys=["sk-xxx-xxxx"])) \
   .with_rate_limit(RateLimit(max_calls=100, window_seconds=60)) \
   .with_circuit_breaker(CircuitBreaker(failure_threshold=5)) \
   .with_timeout(seconds=30.0) \
   .run(transport="sse")
```

<br>

---

## 🔌 OpenAPI Import Support

| Input format | Supported |
|---|---|
| OpenAPI 3.0 JSON | ✅ |
| OpenAPI 3.1 JSON | ✅ |
| Swagger 2.0 | 🛠️ Planned |
| Remote URL (https://) | ✅ |
| Local file (file://) | ✅ |
| Python dict object | ✅ |

MCPBox maps each OpenAPI operation to a tool:

| OpenAPI field | → MCP tool attribute |
|---|---|
| `operationId` | Tool name (snake_case) |
| `summary` / `description` | Tool description |
| `parameters` | Tool input parameters (auto Pydantic model) |
| `requestBody` | POST body parameters |
| `responses[200]` | Return type inference |

<br>

---

## 📖 Documentation

> Full documentation coming soon. For now, see the examples in [`examples/`](examples/).

**Topics planned:**
- Advanced middleware composition
- Custom transport implementations
- Tool grouping and namespacing
- Prometheus metrics endpoint
- Hot-reload development mode
- MCP Inspector integration

<br>

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

```bash
# Development setup
git clone https://github.com/LouisYeap/McpBox.git
cd McpBox
pip install -e ".[dev]"
pytest
```

<br>

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

<br>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=80&section=footer" width="100%"/>

**Built with 💙 by [@LouisYeap](https://github.com/LouisYeap)**

*Turn any function into an AI tool. No protocol knowledge required.*
</div>
