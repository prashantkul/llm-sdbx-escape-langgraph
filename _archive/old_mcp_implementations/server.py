"""
MCP Server with SSE transport - Intentionally vulnerable for security research.

This server implements the Model Context Protocol over Server-Sent Events (SSE)
and exposes a vulnerable command execution tool for testing LLM security boundaries.
"""

import json
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

from tools import TOOLS, TOOL_SCHEMAS


app = FastAPI(title="Vulnerable MCP Server")

# Store active SSE connections
connections: Dict[str, asyncio.Queue] = {}


class MCPServer:
    """Handles MCP protocol messages and tool execution."""

    def __init__(self):
        self.tools = TOOLS

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "vulnerable-mcp-server",
                "version": "1.0.0"
            }
        }

    def handle_list_tools(self) -> Dict[str, Any]:
        """Return available tools."""
        return {
            "tools": TOOL_SCHEMAS
        }

    def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ]
            }

        # Execute the tool
        tool_func = self.tools[tool_name]
        result = tool_func(**arguments)

        # Format response based on tool type
        if 'exit_code' in result:
            # Shell command format
            output_text = f"Exit Code: {result['exit_code']}\n"
            if result.get('stdout'):
                output_text += f"Output:\n{result['stdout']}\n"
            if result.get('stderr'):
                output_text += f"Error:\n{result['stderr']}\n"
        elif 'content' in result:
            # File read format
            output_text = f"File: {result.get('filename', 'N/A')}\n\n{result['content']}"
        elif 'results' in result:
            # Search results format
            output_text = f"Search Pattern: {result.get('pattern', 'N/A')}\n\n{result['results']}"
        elif 'result' in result:
            # Python code execution format
            output_text = f"Code: {result.get('code', 'N/A')}\n\nResult:\n{result['result']}"
        elif 'variable' in result:
            # Environment variable format
            output_text = f"Variable: {result['variable']}\nValue: {result.get('value', '(not set)')}"
        else:
            # Fallback
            output_text = str(result)

        # Check for errors
        is_error = result.get('error') is not None or not result.get('success', True)
        if result.get('error'):
            output_text += f"\n\nError: {result['error']}"

        return {
            "content": [
                {
                    "type": "text",
                    "text": output_text.strip()
                }
            ],
            "isError": is_error
        }

    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route MCP messages to appropriate handlers."""
        method = message.get("method")

        if method == "initialize":
            result = self.handle_initialize(message.get("params", {}))
        elif method == "tools/list":
            result = self.handle_list_tools()
        elif method == "tools/call":
            result = self.handle_call_tool(message.get("params", {}))
        else:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": result
        }


mcp_server = MCPServer()


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for server-to-client communication."""
    connection_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    connections[connection_id] = queue

    async def event_generator():
        try:
            # Send endpoint URL as first message
            yield {
                "event": "endpoint",
                "data": json.dumps({"endpoint": f"/message?connection_id={connection_id}"})
            }

            # Stream messages from queue
            while True:
                message = await queue.get()
                if message is None:  # Shutdown signal
                    break
                yield {
                    "event": "message",
                    "data": json.dumps(message)
                }
        except asyncio.CancelledError:
            pass
        finally:
            connections.pop(connection_id, None)

    return EventSourceResponse(event_generator())


@app.post("/message")
async def message_endpoint(request: Request):
    """HTTP POST endpoint for client-to-server messages."""
    connection_id = request.query_params.get("connection_id")

    if not connection_id or connection_id not in connections:
        return {"error": "Invalid or missing connection_id"}

    try:
        message = await request.json()

        # Log incoming message
        print(f"[{datetime.now().isoformat()}] Received: {json.dumps(message, indent=2)}")

        # Process message
        response = mcp_server.handle_message(message)

        # Log response
        print(f"[{datetime.now().isoformat()}] Sending: {json.dumps(response, indent=2)}")

        # Send response via SSE
        await connections[connection_id].put(response)

        return {"status": "ok"}

    except Exception as e:
        print(f"Error processing message: {e}")
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": "vulnerable-mcp-server",
        "active_connections": len(connections)
    }


if __name__ == "__main__":
    print("Starting Vulnerable MCP Server on http://0.0.0.0:8000")
    print("SSE endpoint: http://0.0.0.0:8000/sse")
    print("⚠️  WARNING: This server contains intentional security vulnerabilities for research purposes")
    uvicorn.run(app, host="0.0.0.0", port=8000)
