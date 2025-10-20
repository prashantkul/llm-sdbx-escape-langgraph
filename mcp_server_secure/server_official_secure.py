"""
Secure MCP Server supporting both SSE and Streamable HTTP transports.
This implements the same tools as the vulnerable server but with security controls.

- SSE transport on /sse (for MCP Inspector)
- StreamableHTTP on /mcp (for langchain-mcp-adapters)
"""

import os
import subprocess
import sys
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn
import uuid

# Add security module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from security import PathValidator, CommandValidator, get_executor

# Initialize validators
path_validator = PathValidator()
command_validator = CommandValidator()
python_executor = get_executor()

# Initialize MCP server
mcp_server = Server("secure-mcp-server")

# Security logging
def log_security_event(event_type: str, details: dict):
    """Log security-related events for audit trail."""
    print(f"⚠️  SECURITY EVENT [{event_type}]: {details}", file=sys.stderr)


# Define secure tools (same as vulnerable but with security descriptions)
@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available secure tools."""
    return [
        Tool(
            name="execute_shell_command",
            description="Execute allowed shell commands (ls, pwd, whoami, cat, curl)",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute (whitelist enforced)"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="read_file",
            description="Read file contents from allowed directories (/app/data, /tmp)",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to read (path validation enforced)"
                    }
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="execute_python_code",
            description="Execute Python code (restricted environment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute (dangerous patterns blocked)"
                    }
                },
                "required": ["code"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool call with security validation."""

    if name == "execute_shell_command":
        command = arguments.get("command", "")

        # Validate command
        is_valid, error_msg = command_validator.validate_command(command)
        if not is_valid:
            log_security_event("COMMAND_BLOCKED", {
                "command": command,
                "reason": error_msg
            })
            return [TextContent(type="text", text=error_msg)]

        # For cat command, also validate the file path
        if command.startswith('cat '):
            file_path = command.split('cat ', 1)[1].strip()
            is_valid, resolved_path, error_msg = path_validator.validate_path(file_path)
            if not is_valid:
                log_security_event("PATH_BLOCKED", {
                    "command": command,
                    "path": file_path,
                    "reason": error_msg
                })
                return [TextContent(type="text", text=error_msg)]

        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
                cwd='/tmp'  # Execute in /tmp for safety
            )

            # Sanitize output
            output = f"Exit Code: {result.returncode}\n"
            if result.stdout:
                sanitized = command_validator.sanitize_output(result.stdout)
                output += f"Output:\n{sanitized}\n"
            if result.stderr:
                sanitized = command_validator.sanitize_output(result.stderr)
                output += f"Error:\n{sanitized}\n"

            return [TextContent(type="text", text=output)]
        except subprocess.TimeoutExpired:
            log_security_event("COMMAND_TIMEOUT", {"command": command})
            return [TextContent(type="text", text="Error: Command execution timeout")]
        except Exception as e:
            log_security_event("COMMAND_ERROR", {
                "command": command,
                "error": str(e)
            })
            return [TextContent(type="text", text=f"Error: Execution failed: {str(e)}")]

    elif name == "read_file":
        filename = arguments.get("filename", "")

        # Validate path
        is_valid, resolved_path, error_msg = path_validator.validate_path(filename)
        if not is_valid:
            log_security_event("FILE_ACCESS_BLOCKED", {
                "filename": filename,
                "reason": error_msg
            })
            return [TextContent(type="text", text=error_msg)]

        # Check symlink chain
        is_safe, symlink_error = path_validator.check_symlink_chain(resolved_path)
        if not is_safe:
            log_security_event("SYMLINK_BLOCKED", {
                "filename": filename,
                "resolved": resolved_path,
                "reason": symlink_error
            })
            return [TextContent(type="text", text=symlink_error)]

        try:
            with open(resolved_path, 'r') as f:
                content = f.read()

            # Sanitize output
            content = command_validator.sanitize_output(content)

            return [TextContent(type="text", text=f"File: {filename}\n\n{content}")]
        except FileNotFoundError:
            return [TextContent(type="text", text=f"Error: File not found: {filename}")]
        except PermissionError:
            log_security_event("FILE_PERMISSION_DENIED", {"filename": filename})
            return [TextContent(type="text", text=f"Error: Permission denied: {filename}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: Failed to read file: {str(e)}")]

    elif name == "execute_python_code":
        code = arguments.get("code", "")

        # Execute code using sandboxed executor
        success, output = python_executor.execute(code)

        if success:
            log_security_event("PYTHON_EXECUTED", {
                "code": code[:100],
                "output_length": len(output)
            })
            return [TextContent(type="text", text=output)]
        else:
            log_security_event("PYTHON_BLOCKED", {
                "code": code[:100],
                "reason": output
            })
            return [TextContent(type="text", text=output)]

    else:
        return [TextContent(type="text", text=f"Error: Unknown tool: {name}")]


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
    print("🔒 SECURE MCP SERVER (Official SDK - Streamable HTTP)")
    print("=" * 80)
    print("\nStarting server on http://0.0.0.0:8001")
    print("MCP endpoint: http://0.0.0.0:8001/mcp")
    print("\nSecurity Features Enabled:")
    print("  ✓ Path validation (whitelist: /app/data, /tmp)")
    print("  ✓ Command validation (whitelist: ls, pwd, whoami, cat, curl)")
    print("  ✓ SSRF protection (curl: HTTP/HTTPS only)")
    print("  ✓ Output sanitization (10,000 char limit)")
    print("  ✓ Security logging for audit trail")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
