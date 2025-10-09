"""
Test using langchain-mcp-adapters to connect to our MCP server.
"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_tools():
    """Test the LangChain MCP tools."""

    print("Connecting to MCP server...")

    try:
        # Create MCP client with streamable_http transport
        client = MultiServerMCPClient({
            "vulnerable-server": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp"  # MCP endpoint
            }
        })

        print("✓ Connected!")

        # Get tools
        tools = await client.get_tools()
        print(f"\n✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Test calling a tool
        print("\n✓ Testing read_file tool with /etc/passwd...")
        read_file_tool = next(t for t in tools if t.name == "read_file")
        result = await read_file_tool.ainvoke({"filename": "/etc/passwd"})
        print(f"✓ Tool result (first 500 chars):\n{str(result)[:500]}...")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
