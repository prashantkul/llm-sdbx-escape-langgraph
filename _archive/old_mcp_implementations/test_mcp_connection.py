"""
Quick test to verify we can connect to and use the MCP server.
This will help us understand the correct client implementation.
"""

import asyncio
from mcp.client.sse import sse_client

async def test_connection():
    """Test connecting to MCP server and listing tools."""
    sse_url = "http://localhost:8000/sse"
    message_url = "http://localhost:8000/messages/"

    print(f"Connecting to {sse_url}...")

    try:
        async with sse_client(sse_url, message_url) as (read, write):
            print("✓ Connected!")

            # Send initialize
            await write({
                "jsonrpc": "2.0",
                "id": "1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            })

            # Read initialize response
            init_response = await read()
            print(f"✓ Initialize response: {init_response}")

            # List tools
            await write({
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tools/list"
            })

            # Read tools response
            tools_response = await read()
            print(f"✓ Tools response: {tools_response}")

            if tools_response and "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                print(f"\n✓ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")

            # Test calling read_file tool
            print("\n Testing read_file tool with /etc/passwd...")
            await write({
                "jsonrpc": "2.0",
                "id": "3",
                "method": "tools/call",
                "params": {
                    "name": "read_file",
                    "arguments": {
                        "filename": "/etc/passwd"
                    }
                }
            })

            # Read tool call response
            tool_response = await read()
            print(f"✓ Tool response: {tool_response}")

            if tool_response and "result" in tool_response:
                content = tool_response["result"].get("content", [])
                if content:
                    print(f"\n✓ Tool output:\n{content[0].get('text', '')[:500]}...")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
