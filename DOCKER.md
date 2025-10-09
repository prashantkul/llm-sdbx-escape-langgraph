# Docker Deployment Guide

This guide explains how to run the LLM security research agent in Docker containers.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Docker Network (research-net)         │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  MCP Server Container          │    │
│  │  ─────────────────────         │    │
│  │  - Vulnerable execute tool     │    │
│  │  - Listens on :8000            │    │
│  │  - Isolated /etc/passwd        │    │
│  └─────────────┬──────────────────┘    │
│                │                        │
│                │ HTTP/SSE               │
│                │                        │
│  ┌─────────────▼──────────────────┐    │
│  │  Agent Container               │    │
│  │  ──────────────                │    │
│  │  - LangGraph workflow          │    │
│  │  - Gemini API client           │    │
│  │  - Attacks MCP server          │    │
│  │  - Logs to volume              │    │
│  └────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
           │
           │ Volume Mount
           ▼
      ./results/ (host)
```

## 🚀 Quick Start

### 1. Set Environment Variables

Create a `.env` file (or use existing one):

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
MAX_ATTEMPTS=10
```

### 2. Build and Run

```bash
# Build both containers
docker-compose build

# Run the experiment
docker-compose up

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f agent
```

### 3. View Results

Results are automatically saved to `./results/` on your host machine:

```bash
ls -lrt results/
tail -100 results/experiment_*.txt
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `MCP_SERVER_URL` | `http://mcp-server:8000` | MCP server endpoint |
| `MAX_ATTEMPTS` | `10` | Maximum injection attempts |

### Custom Configuration

Edit `docker-compose.yml` to customize:

```yaml
agent:
  environment:
    - MAX_ATTEMPTS=20  # Allow more attempts
    - GEMINI_MODEL=gemini-2.0-flash-exp  # Use different model
```

## 📊 Monitoring

### View Real-Time Logs

```bash
# Agent logs
docker-compose logs -f agent

# MCP server logs
docker-compose logs -f mcp-server

# Both containers
docker-compose logs -f
```

### Check Container Status

```bash
docker-compose ps
```

### Inspect Containers

```bash
# Enter agent container
docker-compose exec agent /bin/bash

# Enter MCP server container
docker-compose exec mcp-server /bin/bash
```

## 🔒 Security Considerations

### Network Isolation

- Containers communicate via isolated Docker network
- MCP server is NOT exposed to internet (only to Docker network)
- Agent needs internet access for Gemini API only

### Read-Only Root Filesystem (Optional)

For extra security, uncomment in `docker-compose.yml`:

```yaml
agent:
  read_only: true
  tmpfs:
    - /tmp
```

### Limited Resources

Add resource limits:

```yaml
agent:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
```

## 🧪 Testing Scenarios

### 1. Remote Attack (Docker → Docker)

This is the default mode - agent attacks MCP server over network:

```bash
docker-compose up
```

### 2. Local Testing (Direct Execution)

For debugging without MCP server:

```bash
export USE_DIRECT_CLIENT=true
cd agent
python workflow.py
```

### 3. Multiple Runs

```bash
# Run experiment multiple times
for i in {1..5}; do
  echo "=== Run $i ==="
  docker-compose up agent
  docker-compose down
done
```

## 📁 File Structure in Containers

### Agent Container (`/app`)
```
/app/
├── workflow.py          # Main entry point
├── nodes.py             # LangGraph nodes
├── prompts.py           # Security researcher prompt
├── config.py            # Configuration
├── mcp_client.py        # MCP SSE client
├── direct_tool_client.py # Fallback client
├── logging/             # Logging module
│   └── logger.py
└── results/             # Mounted volume
    └── experiment_*.txt
```

### MCP Server Container (`/app`)
```
/app/
├── server.py            # FastAPI SSE server
├── tools.py             # Vulnerable execute_shell_command
└── requirements.txt
```

## 🐛 Troubleshooting

### MCP Server Not Starting

```bash
# Check health
docker-compose exec mcp-server curl http://localhost:8000/health

# View logs
docker-compose logs mcp-server
```

### Agent Can't Connect

```bash
# Verify network
docker network inspect llm-sdbx-escape-langgraph_research-net

# Test connectivity
docker-compose exec agent curl http://mcp-server:8000/health
```

### No Results Generated

```bash
# Check volume mount
docker-compose exec agent ls -la /app/results

# Check permissions
ls -la results/
```

### Gemini API Rate Limits

If you hit rate limits, reduce `MAX_ATTEMPTS` or add delays:

```yaml
agent:
  environment:
    - MAX_ATTEMPTS=5  # Fewer attempts
```

## 🧹 Cleanup

```bash
# Stop containers
docker-compose down

# Remove containers and networks
docker-compose down --remove-orphans

# Remove images
docker-compose down --rmi all

# Remove volumes (WARNING: deletes results!)
docker-compose down -v
```

## 🔄 Rebuilding

After code changes:

```bash
# Rebuild specific service
docker-compose build agent

# Rebuild all services
docker-compose build

# Force rebuild (no cache)
docker-compose build --no-cache
```

## 📈 Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml llm-research

# Scale agent
docker service scale llm-research_agent=3
```

### Using Kubernetes

Convert docker-compose.yml:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose

# Convert
./kompose convert -f docker-compose.yml
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
