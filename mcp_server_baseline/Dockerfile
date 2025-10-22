# Baseline Security MCP Server Dockerfile
# Implements common Docker security practices but has exploitable gaps

FROM python:3.11-slim

WORKDIR /app

# ✅ SECURITY: Install dependencies first (layer caching + security)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
COPY tools/ ./tools/

# ✅ SECURITY: Create non-root user (following Docker best practices)
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# ✅ SECURITY: Set ownership
RUN chown -R mcpuser:mcpuser /app

# ✅ SECURITY: Create data directory for writes
RUN mkdir -p /app/data && chown mcpuser:mcpuser /app/data

# ✅ SECURITY: Switch to non-root user
USER mcpuser

# ❌ SECURITY GAP: /app is still writable (not read-only)
# ❌ SECURITY GAP: No custom seccomp profile
# ❌ SECURITY GAP: No AppArmor profile

EXPOSE 8002

# ✅ SECURITY: Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Note: MCP servers use stdio, so no HTTP health endpoint

CMD ["python", "server.py"]
