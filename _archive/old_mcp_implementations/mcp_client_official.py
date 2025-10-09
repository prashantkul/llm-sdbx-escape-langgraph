"""
Official MCP Client using the mcp package with SSE transport.
Thread-safe synchronous wrapper for use with FastAPI.
"""

import threading
import asyncio
from typing import Dict, Any, List
from mcp.client.sse import sse_client


class OfficialMCPClient:
    """Synchronous MCP client using official SDK."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.message_url = f"{base_url}/messages/"
        self.tools = []
        self._initialized = False
        self._session = None

    def _run_async(self, coro):
        """Run async code in a dedicated thread with its own event loop."""
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
        """Connect to MCP server and initialize."""
        if self._initialized:
            return

        print(f"Connecting to MCP server at {self.sse_url}...")

        async def do_connect():
            """Async connection logic."""
            async with sse_client(self.sse_url, self.message_url) as (read, write):
                # Initialize
                await write({"method": "initialize", "params": {}})

                # Read initialization response
                init_response = await read()
                print(f"✓ Initialized: {init_response}")

                # List tools
                await write({"method": "tools/list"})
                tools_response = await read()

                if tools_response and "result" in tools_response:
                    self.tools = tools_response["result"].get("tools", [])
                    print(f"✓ Available tools: {[t['name'] for t in self.tools]}")

                # Store session for later use
                self._session = (read, write)

        self._run_async(do_connect())
        self._initialized = True
        print("✓ Connected to MCP server")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool and return results."""
        if not self._initialized:
            self.connect()

        async def do_call():
            """Async tool call logic."""
            async with sse_client(self.sse_url, self.message_url) as (read, write):
                # Call tool
                await write({
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                })

                # Read response
                response = await read()

                if response and "result" in response:
                    result = response["result"]

                    # Extract text content
                    content_list = result.get("content", [])
                    if content_list:
                        text = content_list[0].get("text", "")
                    else:
                        text = ""

                    return {
                        "output": text,
                        "is_error": result.get("isError", False)
                    }

                return {"output": "", "is_error": True}

        return self._run_async(do_call())

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        if not self._initialized:
            self.connect()
        return self.tools
