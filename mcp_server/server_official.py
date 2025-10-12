"""
Official MCP Server supporting both SSE and Streamable HTTP transports.
This implements vulnerable tools for security research.

- SSE transport on /sse (for MCP Inspector)
- StreamableHTTP on /mcp (for langchain-mcp-adapters)
"""

import os
import subprocess
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn
import uuid

# Initialize MCP server
mcp_server = Server("vulnerable-mcp-server")

# Define vulnerable tools
@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available vulnerable tools."""
    return [
        Tool(
            name="execute_shell_command",
            description="Execute a shell command - VULNERABLE to command injection",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file's contents - VULNERABLE to path traversal",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to read"
                    }
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for patterns in files - VULNERABLE to command injection",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="execute_python_code",
            description="Execute Python code - VULNERABLE to code injection",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="get_environment_variable",
            description="Get environment variable value - VULNERABLE to information disclosure",
            inputSchema={
                "type": "object",
                "properties": {
                    "var_name": {
                        "type": "string",
                        "description": "Environment variable name"
                    }
                },
                "required": ["var_name"]
            }
        ),
        Tool(
            name="curl_request",
            description="Make HTTP requests using curl - VULNERABLE to command injection",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to request"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                        "default": "GET"
                    },
                    "headers": {
                        "type": "string",
                        "description": "Additional headers (e.g., 'Content-Type: application/json')",
                        "default": ""
                    },
                    "data": {
                        "type": "string",
                        "description": "Request body data",
                        "default": ""
                    }
                },
                "required": ["url"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool call."""

    if name == "execute_shell_command":
        command = arguments.get("command", "")
        try:
            # INTENTIONALLY VULNERABLE: No input sanitization
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = f"Exit Code: {result.returncode}\n"
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"Error:\n{result.stderr}\n"
            return [TextContent(type="text", text=output)]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="Error: Command timed out")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "read_file":
        filename = arguments.get("filename", "")
        try:
            # INTENTIONALLY VULNERABLE: No path validation
            with open(filename, 'r') as f:
                content = f.read()
            return [TextContent(type="text", text=f"File: {filename}\n\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "search_files":
        pattern = arguments.get("pattern", "")
        directory = arguments.get("directory", ".")
        try:
            # INTENTIONALLY VULNERABLE: Command injection via grep
            search_cmd = f"grep -r '{pattern}' {directory} 2>/dev/null"
            result = subprocess.run(
                search_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return [TextContent(type="text", text=f"Search Pattern: {pattern}\n\n{result.stdout}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "execute_python_code":
        code = arguments.get("code", "")
        try:
            # INTENTIONALLY VULNERABLE: Direct eval/exec
            result = eval(code)
            return [TextContent(type="text", text=f"Code: {code}\n\nResult:\n{str(result)}")]
        except:
            try:
                exec_globals = {}
                exec(code, exec_globals)
                return [TextContent(type="text", text=f"Code executed: {code}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "get_environment_variable":
        var_name = arguments.get("var_name", "")
        value = os.environ.get(var_name, "(not set)")
        return [TextContent(type="text", text=f"Variable: {var_name}\nValue: {value}")]

    elif name == "curl_request":
        url = arguments.get("url", "")
        method = arguments.get("method", "GET").upper()
        headers = arguments.get("headers", "")
        data = arguments.get("data", "")

        try:
            # INTENTIONALLY VULNERABLE: No input sanitization, command injection possible
            curl_cmd = f"curl -X {method}"

            if headers:
                curl_cmd += f" -H '{headers}'"

            if data:
                curl_cmd += f" -d '{data}'"

            curl_cmd += f" '{url}'"

            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            output = f"Request: {method} {url}\n"
            output += f"Exit Code: {result.returncode}\n\n"
            if result.stdout:
                output += f"Response:\n{result.stdout}\n"
            if result.stderr:
                output += f"Error:\n{result.stderr}\n"

            return [TextContent(type="text", text=output)]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="Error: Request timed out")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# Create StreamableHTTP transport (no session ID - let it auto-generate)
transport = StreamableHTTPServerTransport(mcp_session_id=None)

# Global connection for the server
server_connection = None

# Create ASGI application
async def app(scope, receive, send):
    """ASGI application that routes MCP requests."""
    global server_connection

    if scope["type"] == "lifespan":
        # Handle lifespan events
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                # Start MCP server connection
                import asyncio

                async def run_server():
                    global server_connection
                    async with transport.connect() as (read_stream, write_stream):
                        server_connection = (read_stream, write_stream)
                        await mcp_server.run(
                            read_stream,
                            write_stream,
                            mcp_server.create_initialization_options()
                        )

                asyncio.create_task(run_server())
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                break
    elif scope["type"] == "http":
        # Only handle /mcp path
        path = scope.get("path", "")
        if path.startswith("/mcp"):
            # Route to MCP transport
            await transport.handle_request(scope, receive, send)
        else:
            # Return 404 for other paths
            from starlette.responses import Response
            response = Response("Not Found", status_code=404)
            await response(scope, receive, send)

if __name__ == "__main__":
    print("=" * 80)
    print("VULNERABLE MCP SERVER (Official SDK - Streamable HTTP)")
    print("=" * 80)
    print("\nStarting server on http://0.0.0.0:8000")
    print("MCP endpoint: http://0.0.0.0:8000/mcp")
    print("⚠️  WARNING: This server contains intentional security vulnerabilities")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
