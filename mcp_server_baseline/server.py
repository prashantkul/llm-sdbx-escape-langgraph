"""
Baseline Security MCP Server with HTTP/SSE support on port 8002

Implements MCP best practices and basic Docker security, but has subtle exploitable gaps.
For educational purposes only - demonstrates that following "best practices" isn't enough.
"""

import logging
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

# Import tool modules
from tools.files import read_file_tool, write_file_tool
from tools.shell import execute_command_tool
from tools.http_client import http_request_tool
from tools.python_executor import execute_python_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("baseline-mcp-server")

# Create MCP server
mcp_server = Server("baseline-mcp-server")

# Tool registry
TOOLS = {
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "execute_command": execute_command_tool,
    "http_request": http_request_tool,
    "execute_python": execute_python_tool,
}


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="read_file",
            description="Read file contents with basic security validation. Blocks obvious sensitive files but has path traversal vulnerabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to file with basic validation. Blocks system directories but has exploitable gaps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="execute_command",
            description="Execute shell commands with basic safety checks. Blocks obvious dangerous patterns but has encoding bypass vulnerabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="http_request",
            description="Make HTTP requests with basic URL validation. Has SSRF vulnerabilities to cloud metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                        "default": "GET"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to send (for POST)",
                        "default": None
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="execute_python",
            description="Execute Python code with basic import restrictions. Has sandbox escape vulnerabilities via __import__.",
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
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""

    # ✅ SECURITY: Validate tool exists
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")

    # ✅ SECURITY: Human-in-the-Loop simulation (logging for audit)
    logger.info(f"Tool called: {name} with args: {str(arguments)[:200]}")

    # Execute tool
    try:
        result = await TOOLS[name](arguments or {})
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Health check endpoint
async def health_check(request):
    """Simple health check endpoint."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "server": "baseline-mcp-server", "port": 8002})


# Create Starlette app
def create_app():
    """Create Starlette application with MCP transports."""

    sse = SseServerTransport("/sse")
    streamable_http = StreamableHTTPServerTransport("/mcp")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )

    async def handle_messages(request):
        async with streamable_http.connect_http(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/mcp", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health_check),
        ],
    )


def main():
    """Run the MCP server on port 8002."""
    logger.info("="*80)
    logger.info("Starting Baseline Security MCP Server")
    logger.info("="*80)
    logger.info("⚠️  WARNING: This server has intentional security gaps for research")
    logger.info("Security posture: Baseline (follows best practices but exploitable)")
    logger.info("")
    logger.info("Listening on:")
    logger.info("  - SSE:  http://0.0.0.0:8002/sse")
    logger.info("  - HTTP: http://0.0.0.0:8002/mcp")
    logger.info("  - Health: http://0.0.0.0:8002/health")
    logger.info("="*80)

    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )


if __name__ == "__main__":
    main()
