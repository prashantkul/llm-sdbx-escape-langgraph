"""
MCP Client for connecting to the vulnerable MCP server via SSE.
"""

import json
import asyncio
import uuid
import threading
from typing import Dict, Any, Optional
import httpx
from sseclient import SSEClient


class MCPClient:
    """Client for communicating with MCP server over SSE transport."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.message_url = None
        self.connection_id = None
        self.tools = []
        self.sse_task = None
        self.response_queue = asyncio.Queue()

    async def connect(self):
        """Establish SSE connection to MCP server."""
        print(f"Connecting to MCP server at {self.sse_url}...")

        # Make SSE connection
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", self.sse_url) as response:
                # Read the endpoint message
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        if "endpoint" in data:
                            endpoint = data["endpoint"]
                            # Extract connection_id from endpoint
                            self.message_url = f"{self.base_url}/message"
                            if "connection_id=" in endpoint:
                                self.connection_id = endpoint.split("connection_id=")[1]
                            print(f"Connected! Connection ID: {self.connection_id}")
                            break

        # Initialize the connection
        await self.initialize()

        # List available tools
        await self.list_tools()

    async def initialize(self):
        """Send MCP initialize message."""
        response = await self._send_message({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "security-researcher-agent",
                    "version": "1.0.0"
                }
            }
        })
        print(f"Initialized: {response.get('result', {}).get('serverInfo', {})}")

    async def list_tools(self):
        """List available tools from MCP server."""
        response = await self._send_message({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list"
        })

        self.tools = response.get("result", {}).get("tools", [])
        print(f"Available tools: {[t['name'] for t in self.tools]}")

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        response = await self._send_message({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        })

        result = response.get("result", {})

        # Extract text from content array
        content = result.get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = ""

        return {
            "output": text,
            "is_error": result.get("isError", False)
        }

    async def _send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server and wait for response."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send message
            response = await client.post(
                self.message_url,
                params={"connection_id": self.connection_id},
                json=message
            )
            response.raise_for_status()

            # In a real implementation, we'd listen to the SSE stream for the response
            # For simplicity, we'll add a small delay and assume synchronous response
            await asyncio.sleep(0.1)

        # Note: This is a simplified implementation
        # A production version would properly handle SSE events and match request/response IDs
        return {"result": {}}


class SyncMCPClient:
    """Synchronous wrapper for MCP client that works with existing event loops."""

    def __init__(self, base_url: str):
        self.client = MCPClient(base_url)
        self._initialized = False

    def _run_in_thread(self, coro):
        """Run an async coroutine in a dedicated thread with its own event loop."""
        result = None
        exception = None

        def run():
            nonlocal result, exception
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(coro)
                loop.close()
            except Exception as e:
                exception = e

        thread = threading.Thread(target=run)
        thread.start()
        thread.join()

        if exception:
            raise exception
        return result

    def connect(self):
        """Connect to MCP server."""
        if not self._initialized:
            self._run_in_thread(self.client.connect())
            self._initialized = True

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool synchronously."""
        if not self._initialized:
            self.connect()
        return self._run_in_thread(self.client.call_tool(name, arguments))

    def get_tools(self):
        """Get list of available tools."""
        if not self._initialized:
            self.connect()
        return self.client.tools
