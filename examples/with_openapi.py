"""MCPBox — OpenAPI Import Example

Run with: python with_openapi.py
"""

from mcpbox import Box

box = Box(name="openapi-box")

# Import from a remote OpenAPI URL
# box.import_from_openapi(
#     "https://api.example.com/openapi.json",
#     base_url="https://api.example.com",
# )

# Or from a local file
# box.import_from_openapi("file:///path/to/openapi.json")

# Or from a dict
box.import_from_openapi(
    {
        "openapi": "3.0.0",
        "info": {"title": "Example API", "version": "1.0.0"},
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get a user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                }
            }
        },
    },
    base_url="https://api.example.com",
)

print("Tools:", [t["name"] for t in box._registry.list_tools_public()])
box.run()
